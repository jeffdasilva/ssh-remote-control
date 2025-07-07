"""Test SSH connection manager."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ssh_remote_control.config import Settings
from ssh_remote_control.server import SSHConnectionManager


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    settings = Settings()
    settings.ssh_servers = {
        "test-server": {
            "host": "localhost",
            "port": 22,
            "username": "testuser",
            "key_file": "/tmp/test_key",
        }
    }
    return settings


@pytest.fixture
def ssh_manager(mock_settings: Settings) -> SSHConnectionManager:
    """Create SSH connection manager for testing."""
    return SSHConnectionManager(mock_settings)


@pytest.mark.asyncio
async def test_ssh_manager_initialization(ssh_manager: SSHConnectionManager) -> None:
    """Test SSH manager initialization."""
    assert ssh_manager.connections == {}
    assert ssh_manager._connection_locks == {}


@pytest.mark.asyncio
async def test_server_config_retrieval(ssh_manager: SSHConnectionManager) -> None:
    """Test server configuration retrieval."""
    config = ssh_manager.settings.get_server_config("test-server")
    assert config is not None
    assert config.host == "localhost"
    assert config.port == 22
    assert config.username == "testuser"


@pytest.mark.asyncio
async def test_invalid_server_connection(ssh_manager: SSHConnectionManager) -> None:
    """Test connection to invalid server."""
    with pytest.raises(ValueError, match="No configuration found"):
        await ssh_manager.connect("non-existent-server")


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect")
async def test_successful_connection(
    mock_connect: MagicMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test successful SSH connection."""
    # Mock the SSH connection
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False

    # Make the mock connect function return a coroutine that yields the connection
    async def mock_connect_impl(*_args: Any, **_kwargs: Any) -> MagicMock:
        return mock_conn

    mock_connect.side_effect = mock_connect_impl

    # Test connection
    conn = await ssh_manager.connect("test-server")

    assert conn == mock_conn
    assert "test-server" in ssh_manager.connections
    assert ssh_manager.connections["test-server"] == mock_conn

    # Verify connection parameters
    mock_connect.assert_called_once()
    call_args = mock_connect.call_args[1]  # type: ignore[union-attr]
    assert call_args["host"] == "localhost"
    assert call_args["port"] == 22
    assert call_args["username"] == "testuser"
    assert call_args["client_keys"] == ["/tmp/test_key"]


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect", new_callable=AsyncMock)
@patch("ssh_remote_control.server.asyncio.Lock")
async def test_connection_reuse(
    mock_lock: MagicMock, mock_connect: AsyncMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test that existing connections are reused."""
    # Mock the lock to avoid async context manager issues
    mock_lock_instance = MagicMock()
    mock_lock_instance.__aenter__ = AsyncMock(return_value=None)
    mock_lock_instance.__aexit__ = AsyncMock(return_value=None)
    mock_lock.return_value = mock_lock_instance

    # Mock the SSH connection
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False

    # Configure mock to return the connection
    mock_connect.return_value = mock_conn

    # First connection
    conn1 = await ssh_manager.connect("test-server")

    # Second connection should reuse the first
    conn2 = await ssh_manager.connect("test-server")

    assert conn1 == conn2
    assert mock_connect.call_count == 1  # Only called once


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect")
async def test_connection_replacement_when_closed(
    mock_connect: MagicMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test that closed connections are replaced."""
    # Mock the SSH connections
    mock_conn1 = MagicMock()
    mock_conn1.is_closed.return_value = True  # First connection is closed
    mock_conn2 = MagicMock()
    mock_conn2.is_closed.return_value = False

    # Make the mock connect function return different connections
    async def mock_connect_impl(*_args: Any, **_kwargs: Any) -> MagicMock:
        if mock_connect.call_count == 1:
            return mock_conn1
        else:
            return mock_conn2

    mock_connect.side_effect = mock_connect_impl

    # First connection
    conn1 = await ssh_manager.connect("test-server")

    # Second connection should create a new one because first is closed
    conn2 = await ssh_manager.connect("test-server")

    assert conn1 != conn2
    assert mock_connect.call_count == 2


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect")
async def test_execute_command_success(
    mock_connect: MagicMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test successful command execution."""
    # Mock the SSH connection and result
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False
    mock_result = AsyncMock()
    mock_result.exit_status = 0
    mock_result.stdout = "command output"
    mock_result.stderr = ""

    # Make run method async
    async def mock_run(command: str, timeout: int | None = None) -> Any:
        return mock_result

    mock_conn.run = mock_run

    async def mock_connect_impl(*args: Any, **kwargs: Any) -> MagicMock:
        return mock_conn

    mock_connect.side_effect = mock_connect_impl

    # Test command execution
    result = await ssh_manager.execute_command("test-server", "ls -la")

    assert result == "command output"


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect")
async def test_execute_command_failure(
    mock_connect: MagicMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test command execution failure."""
    # Mock the SSH connection and result
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False
    mock_result = AsyncMock()
    mock_result.exit_status = 1
    mock_result.stdout = ""
    mock_result.stderr = "command failed"

    # Make run method async
    async def mock_run(command: str, timeout: int | None = None) -> Any:
        return mock_result

    mock_conn.run = mock_run

    async def mock_connect_impl(*args: Any, **kwargs: Any) -> MagicMock:
        return mock_conn

    mock_connect.side_effect = mock_connect_impl

    # Test command execution failure
    with pytest.raises(RuntimeError, match="Command failed with exit code 1"):
        await ssh_manager.execute_command("test-server", "false")


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect")
async def test_execute_command_with_timeout(
    mock_connect: MagicMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test command execution with timeout."""
    # Mock the SSH connection and result
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False
    mock_result = AsyncMock()
    mock_result.exit_status = 0
    mock_result.stdout = "output"
    mock_result.stderr = ""

    # Make run method async
    async def mock_run(command: str, timeout: int | None = None) -> Any:
        return mock_result

    mock_conn.run = mock_run

    async def mock_connect_impl(*args: Any, **kwargs: Any) -> MagicMock:
        return mock_conn

    mock_connect.side_effect = mock_connect_impl

    # Test command execution with timeout
    result = await ssh_manager.execute_command("test-server", "sleep 1", timeout=30)

    assert result == "output"


@pytest.mark.asyncio
@patch("ssh_remote_control.server.asyncssh.connect")
async def test_get_system_info(
    mock_connect: MagicMock, ssh_manager: SSHConnectionManager
) -> None:
    """Test system info retrieval."""
    # Mock the SSH connection and results
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False

    # Mock different command results
    command_results = {
        "hostname": "test-host",
        "uptime": "up 1 day",
        "df -h": "filesystem info",
        "free -h": "memory info",
        "cat /proc/cpuinfo | grep 'model name' | head -1": "cpu info",
        "cat /proc/loadavg": "load info",
        "uname -r": "kernel info",
    }

    def mock_run(command: str, timeout: int | None = None) -> Any:
        result = AsyncMock()
        result.exit_status = 0
        result.stdout = command_results.get(command, "N/A")
        result.stderr = ""
        return result

    # Make run method async
    async def async_mock_run(command: str, timeout: int | None = None) -> Any:
        return mock_run(command, timeout)

    mock_conn.run = async_mock_run

    async def mock_connect_impl(*args: Any, **kwargs: Any) -> MagicMock:
        return mock_conn

    mock_connect.side_effect = mock_connect_impl

    # Test system info retrieval
    info = await ssh_manager.get_system_info("test-server")

    assert info["hostname"] == "test-host"
    assert info["uptime"] == "up 1 day"
    assert info["disk_usage"] == "filesystem info"
    assert info["memory"] == "memory info"


@pytest.mark.asyncio
async def test_is_connected(ssh_manager: SSHConnectionManager) -> None:
    """Test connection status checking."""
    # No connection yet
    assert await ssh_manager.is_connected("test-server") is False

    # Mock connection
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False
    ssh_manager.connections["test-server"] = mock_conn

    assert await ssh_manager.is_connected("test-server") is True

    # Mock closed connection
    mock_conn.is_closed.return_value = True
    assert await ssh_manager.is_connected("test-server") is False


@pytest.mark.asyncio
async def test_disconnect(ssh_manager: SSHConnectionManager) -> None:
    """Test disconnection."""
    # Mock connection
    mock_conn = MagicMock()
    mock_conn.is_closed.return_value = False
    mock_conn.wait_closed = AsyncMock()
    ssh_manager.connections["test-server"] = mock_conn

    # Test disconnect
    await ssh_manager.disconnect("test-server")

    mock_conn.close.assert_called_once()
    mock_conn.wait_closed.assert_called_once()
    assert "test-server" not in ssh_manager.connections


@pytest.mark.asyncio
async def test_close_all(ssh_manager: SSHConnectionManager) -> None:
    """Test closing all connections."""
    # Mock multiple connections
    mock_conn1 = MagicMock()
    mock_conn1.is_closed.return_value = False
    mock_conn1.wait_closed = AsyncMock()
    mock_conn2 = MagicMock()
    mock_conn2.is_closed.return_value = False
    mock_conn2.wait_closed = AsyncMock()

    ssh_manager.connections["server1"] = mock_conn1
    ssh_manager.connections["server2"] = mock_conn2

    # Test close all
    await ssh_manager.close_all()

    mock_conn1.close.assert_called_once()
    mock_conn1.wait_closed.assert_called_once()
    mock_conn2.close.assert_called_once()
    mock_conn2.wait_closed.assert_called_once()
    assert len(ssh_manager.connections) == 0


@pytest.mark.asyncio
async def test_list_connected_servers(ssh_manager: SSHConnectionManager) -> None:
    """Test listing connected servers."""
    # Mock connections
    mock_conn1 = MagicMock()
    mock_conn1.is_closed.return_value = False
    mock_conn2 = MagicMock()
    mock_conn2.is_closed.return_value = True  # Closed connection

    ssh_manager.connections["server1"] = mock_conn1
    ssh_manager.connections["server2"] = mock_conn2

    # Test listing
    connected = ssh_manager.list_connected_servers()

    assert "server1" in connected
    assert "server2" not in connected
    assert len(connected) == 1
