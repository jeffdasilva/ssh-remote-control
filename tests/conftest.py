"""Test utilities and fixtures for SSH Remote Control tests."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from ssh_remote_control.config import Settings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data for tests."""
    return {
        "debug": True,
        "log_level": "debug",
        "ssh_servers": {
            "test-server": {
                "host": "localhost",
                "port": 22,
                "username": "testuser",
                "key_file": "/tmp/test_key",
            },
            "remote-server": {
                "host": "remote.example.com",
                "port": 2222,
                "username": "remoteuser",
            },
        },
        "web": {"host": "0.0.0.0", "port": 8080},
        "log_files": ["/var/log/syslog", "/var/log/auth.log"],
        "ssh_connect_timeout": 30,
        "ssh_keepalive_interval": 60,
    }


@pytest.fixture
def config_file(temp_dir: Path, sample_config_data: dict[str, Any]) -> Path:
    """Create a temporary config file."""
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(sample_config_data, f)
    return config_path


@pytest.fixture
def mock_ssh_connection() -> AsyncMock:
    """Mock SSH connection for tests."""
    conn = AsyncMock()
    conn.is_closed.return_value = False

    # Mock command execution
    mock_result = AsyncMock()
    mock_result.exit_status = 0
    mock_result.stdout = "command output"
    mock_result.stderr = ""
    conn.run.return_value = mock_result

    # Mock SFTP
    mock_sftp = AsyncMock()
    mock_file = AsyncMock()
    mock_file.read.return_value = "file content"
    mock_sftp.open.return_value.__aenter__.return_value = mock_file
    conn.start_sftp_client.return_value.__aenter__.return_value = mock_sftp

    # Mock process creation
    mock_process = AsyncMock()
    mock_process.stdout = [b"line1\n", b"line2\n"]
    mock_process.wait.return_value = 0
    conn.create_process.return_value = mock_process

    return conn


@pytest.fixture
def mock_settings() -> Settings:
    """Mock settings for tests."""
    settings = Settings()
    settings.debug = True
    settings.log_level = "debug"
    settings.ssh_servers = {
        "test-server": {
            "host": "localhost",
            "port": 22,
            "username": "testuser",
            "key_file": "/tmp/test_key",
        }
    }
    settings.log_files = ["/var/log/syslog", "/var/log/auth.log"]
    settings.ssh_connect_timeout = 30
    settings.ssh_keepalive_interval = 60
    return settings


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Mock WebSocket for tests."""
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


def create_test_server_config(
    host: str = "localhost", port: int = 22, username: str = "testuser", **kwargs: Any
) -> dict[str, Any]:
    """Create a test server configuration."""
    config = {"host": host, "port": port, "username": username}
    config.update(kwargs)
    return config


def create_mock_command_result(
    stdout: str = "", stderr: str = "", exit_status: int = 0
) -> MagicMock:
    """Create a mock command result."""
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.exit_status = exit_status
    return result


def create_mock_system_info() -> dict[str, str]:
    """Create mock system information."""
    return {
        "hostname": "test-host",
        "uptime": "up 1 day, 2:30",
        "disk_usage": (
            "Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1        20G  5.0G   14G  27% /"
        ),
        "memory": (
            "              total        used        free      shared  "
            "buff/cache   available\n"
            "Mem:           2.0G        500M        1.2G         50M        "
            "300M        1.3G"
        ),
        "cpu_info": "model name\t: Intel(R) Core(TM) i5-8265U CPU @ 1.60GHz",
        "load_average": "0.15 0.12 0.08 1/123 1234",
        "kernel": "5.4.0-42-generic",
    }


class MockAsyncSSH:
    """Mock asyncssh module for testing."""

    @staticmethod
    async def connect(**_kwargs: Any) -> AsyncMock:
        """Mock asyncssh.connect function."""
        conn = AsyncMock()
        conn.is_closed.return_value = False

        # Mock command execution
        mock_result = AsyncMock()
        mock_result.exit_status = 0
        mock_result.stdout = "mock output"
        mock_result.stderr = ""
        conn.run.return_value = mock_result

        return conn


def setup_env_vars(servers: dict[str, dict[str, Any]] | None = None) -> None:
    """Set up environment variables for testing."""
    if servers is None:
        servers = {
            "testserver": {
                "host": "test.example.com",
                "port": 22,
                "username": "testuser",
            }
        }

    # Clear existing SSH_SERVERS_ env vars
    for key in list(os.environ.keys()):
        if key.startswith("SSH_SERVERS_"):
            del os.environ[key]

    # Set new env vars
    for server_name, config in servers.items():
        for key, value in config.items():
            env_key = f"SSH_SERVERS_{server_name.upper()}_{key.upper()}"
            os.environ[env_key] = str(value)


def cleanup_env_vars() -> None:
    """Clean up SSH_SERVERS_ environment variables."""
    for key in list(os.environ.keys()):
        if key.startswith("SSH_SERVERS_"):
            del os.environ[key]


@pytest.fixture(autouse=True)
def clean_environment() -> Generator[None, None, None]:
    """Clean up environment variables after each test."""
    yield
    cleanup_env_vars()


def assert_server_config_equal(config1: Any, config2: Any) -> None:
    """Assert that two server configurations are equal."""
    assert config1.host == config2.host
    assert config1.port == config2.port
    assert config1.username == config2.username
    assert config1.key_file == config2.key_file
    assert config1.known_hosts == config2.known_hosts


def create_test_log_lines(count: int = 10) -> list[str]:
    """Create test log lines."""
    lines = []
    for i in range(count):
        lines.append(f"2023-01-01 12:00:{i:02d} [INFO] Test log line {i}")
    return lines


def mock_file_operations() -> dict[str, Any]:
    """Mock file operations for testing."""
    return {
        "read": AsyncMock(return_value="file content"),
        "write": AsyncMock(),
        "exists": MagicMock(return_value=True),
        "is_file": MagicMock(return_value=True),
        "is_dir": MagicMock(return_value=False),
    }
