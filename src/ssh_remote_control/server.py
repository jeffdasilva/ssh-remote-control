"""SSH connection management for remote server operations."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, cast

import asyncssh
from asyncssh import SSHClientConnection, SSHClientProcess

from .config import ServerConfig, Settings

logger = logging.getLogger(__name__)


class SSHConnectionManager:
    """Manages SSH connections to remote servers."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the SSH connection manager."""
        self.settings = settings
        self.connections: dict[str, SSHClientConnection] = {}
        self._connection_locks: dict[str, asyncio.Lock] = {}

    async def connect(self, server_name: str) -> SSHClientConnection:
        """Connect to a server and return the connection."""
        if server_name not in self._connection_locks:
            self._connection_locks[server_name] = asyncio.Lock()

        async with self._connection_locks[server_name]:
            # Return existing connection if available and not closed
            if server_name in self.connections:
                conn = self.connections[server_name]
                if not conn.is_closed():
                    return conn
                # Remove closed connection
                del self.connections[server_name]

            # Get server configuration
            server_config = self.settings.get_server_config(server_name)
            if not server_config:
                raise ValueError(f"No configuration found for server: {server_name}")

            # Establish new connection
            logger.info(
                "Connecting to %s (%s:%s)",
                server_name,
                server_config.host,
                server_config.port,
            )

            try:
                conn = await self._create_connection(server_config)
                self.connections[server_name] = conn
                logger.info("Successfully connected to %s", server_name)
                return conn
            except Exception as e:
                logger.error("Failed to connect to %s: %s", server_name, e)
                raise

    async def _create_connection(self, config: ServerConfig) -> SSHClientConnection:
        """Create a new SSH connection."""
        connect_kwargs: dict[str, Any] = {
            "host": config.host,
            "port": config.port,
            "username": config.username,
            "connect_timeout": self.settings.ssh_connect_timeout,
            "keepalive_interval": self.settings.ssh_keepalive_interval,
        }

        # Add authentication options
        if config.key_file:
            connect_kwargs["client_keys"] = [config.key_file]

        if config.password:
            connect_kwargs["password"] = config.password

        if config.passphrase:
            connect_kwargs["passphrase"] = config.passphrase

        if config.known_hosts:
            connect_kwargs["known_hosts"] = config.known_hosts
        else:
            # For development/testing - in production, always use known_hosts
            connect_kwargs["known_hosts"] = None

        return await asyncssh.connect(**connect_kwargs)

    async def execute_command(
        self, server_name: str, command: str, timeout: int | None = None
    ) -> str:
        """Execute a command on a remote server."""
        conn = await self.connect(server_name)

        try:
            logger.debug("Executing command on %s: %s", server_name, command)
            result = await conn.run(command, timeout=timeout)

            if result.exit_status != 0:
                error_msg = f"Command failed with exit code {result.exit_status}"
                if result.stderr:
                    if isinstance(result.stderr, bytes):
                        error_msg += (
                            f": {result.stderr.decode('utf-8', errors='ignore')}"
                        )
                    else:
                        error_msg += f": {result.stderr}"
                raise RuntimeError(error_msg)

            # Handle both bytes and str stdout
            if result.stdout:
                if isinstance(result.stdout, str):
                    return result.stdout
                # Handle bytes, bytearray, memoryview or other types
                return str(result.stdout)
            return ""
        except Exception as e:
            logger.error("Command execution failed on %s: %s", server_name, e)
            raise

    async def execute_command_stream(
        self,
        server_name: str,
        command: str,
        callback: Callable[[str], Awaitable[None]] | None = None,
    ) -> SSHClientProcess[str]:
        """Execute a command with streaming output."""
        conn = await self.connect(server_name)

        try:
            logger.debug("Starting streaming command on %s: %s", server_name, command)
            # Create process with text encoding to get str output
            process: SSHClientProcess[str] = cast(
                SSHClientProcess[str],
                await conn.create_process(command, encoding="utf-8"),
            )

            if callback:
                # Start a task to handle streaming output
                asyncio.create_task(self._stream_output(process, callback))

            return process
        except Exception as e:
            logger.error("Streaming command failed on %s: %s", server_name, e)
            raise

    async def _stream_output(
        self, process: SSHClientProcess[str], callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Stream output from a process to a callback function."""
        try:
            async for line in process.stdout:
                # Since we specified encoding='utf-8', line should be a str
                await callback(line)
        except (
            ConnectionError,
            OSError,
            UnicodeDecodeError,
            asyncio.CancelledError,
        ) as e:
            logger.error("Error streaming output: %s", e)
        finally:
            await process.wait()

    async def read_file(self, server_name: str, file_path: str) -> str:
        """Read a file from a remote server."""
        conn = await self.connect(server_name)

        try:
            async with (
                conn.start_sftp_client() as sftp,
                sftp.open(file_path, "r") as f,
            ):
                return await f.read()
        except (ConnectionError, OSError, PermissionError, FileNotFoundError) as e:
            logger.error(
                "Failed to read file %s from %s: %s", file_path, server_name, e
            )
            raise

    async def write_file(self, server_name: str, file_path: str, content: str) -> None:
        """Write content to a file on a remote server."""
        conn = await self.connect(server_name)

        try:
            async with (
                conn.start_sftp_client() as sftp,
                sftp.open(file_path, "w") as f,
            ):
                await f.write(content)
        except (ConnectionError, OSError, PermissionError, FileNotFoundError) as e:
            logger.error("Failed to write file %s to %s: %s", file_path, server_name, e)
            raise

    async def tail_file(
        self,
        server_name: str,
        file_path: str,
        callback: Callable[[str], Awaitable[None]],
        lines: int = 10,
    ) -> SSHClientProcess[str]:
        """Tail a file and stream new lines to callback."""
        # Start with the last N lines
        try:
            initial_content = await self.execute_command(
                server_name, f"tail -n {lines} {file_path}"
            )
            for line in initial_content.strip().split("\n"):
                if line.strip():
                    await callback(line)
        except (ConnectionError, OSError, RuntimeError, FileNotFoundError) as e:
            logger.warning("Could not get initial tail content: %s", e)

        # Follow the file for new lines
        command = f"tail -f {file_path}"
        process = await self.execute_command_stream(server_name, command, callback)

        return process

    async def get_system_info(self, server_name: str) -> dict[str, Any]:
        """Get system information from a remote server."""
        commands = {
            "hostname": "hostname",
            "uptime": "uptime",
            "disk_usage": "df -h",
            "memory": "free -h",
            "cpu_info": "cat /proc/cpuinfo | grep 'model name' | head -1",
            "load_average": "cat /proc/loadavg",
            "kernel": "uname -r",
        }

        info: dict[str, str] = {}
        for key, command in commands.items():
            try:
                result = await self.execute_command(server_name, command)
                info[key] = result.strip()
            except (ConnectionError, OSError, TimeoutError, RuntimeError) as e:
                logger.warning("Could not get %s from %s: %s", key, server_name, e)
                info[key] = "N/A"

        return info

    async def is_connected(self, server_name: str) -> bool:
        """Check if connected to a server."""
        if server_name not in self.connections:
            return False

        conn = self.connections[server_name]
        return not conn.is_closed()

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from a specific server."""
        if server_name in self.connections:
            conn = self.connections[server_name]
            if not conn.is_closed():
                conn.close()
                await conn.wait_closed()
            del self.connections[server_name]
            logger.info("Disconnected from %s", server_name)

    async def close_all(self) -> None:
        """Close all SSH connections."""
        for server_name in list(self.connections.keys()):
            await self.disconnect(server_name)
        logger.info("All SSH connections closed")

    def list_connected_servers(self) -> list[str]:
        """List all currently connected servers."""
        return [name for name, conn in self.connections.items() if not conn.is_closed()]
