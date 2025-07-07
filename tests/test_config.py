"""Test configuration for SSH Remote Control."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from ssh_remote_control.config import ServerConfig, Settings


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """Create a temporary config file for testing."""
    config_data: dict[str, Any] = {
        "debug": True,
        "log_level": "debug",
        "ssh_servers": {
            "test-server": {
                "host": "localhost",
                "port": 22,
                "username": "testuser",
                "key_file": "/tmp/test_key",
            }
        },
        "web": {"host": "0.0.0.0", "port": 8080},
        "log_files": ["/var/log/test.log"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def settings_with_config(temp_config_file: str) -> Generator[Settings, None, None]:
    """Create settings with a config file."""
    os.environ["SSH_REMOTE_CONTROL_CONFIG"] = temp_config_file
    settings = Settings()
    yield settings
    # Cleanup
    if "SSH_REMOTE_CONTROL_CONFIG" in os.environ:
        del os.environ["SSH_REMOTE_CONTROL_CONFIG"]


def test_server_config_creation() -> None:
    """Test ServerConfig creation."""
    config = ServerConfig(
        host="example.com", port=22, username="testuser", key_file="/path/to/key"
    )

    assert config.host == "example.com"
    assert config.port == 22
    assert config.username == "testuser"
    assert config.key_file == "/path/to/key"


def test_server_config_defaults() -> None:
    """Test ServerConfig with default values."""
    config = ServerConfig(host="example.com", username="testuser")

    assert config.port == 22
    assert config.key_file is None
    assert config.known_hosts is None


def test_settings_defaults() -> None:
    """Test Settings with default values."""
    # Mock the config file loading to ensure clean defaults
    with (
        patch("ssh_remote_control.config.Path.exists", return_value=False),
        patch.dict("os.environ", {}, clear=True),
    ):
        settings = Settings()

    assert settings.debug is False
    assert settings.log_level == "info"
    assert settings.ssh_servers == {}
    assert settings.web.host == "127.0.0.1"
    assert settings.web.port == 8000
    assert settings.log_files == []


def test_settings_from_config_file(settings_with_config: Settings) -> None:
    """Test Settings loading from config file."""
    settings = settings_with_config

    assert settings.debug is True
    assert settings.log_level == "debug"
    assert "test-server" in settings.ssh_servers
    assert settings.ssh_servers["test-server"]["host"] == "localhost"
    assert settings.web.host == "0.0.0.0"
    assert settings.web.port == 8080
    assert "/var/log/test.log" in settings.log_files


def test_settings_from_environment() -> None:
    """Test Settings loading from environment variables."""
    # Set environment variables
    os.environ.update(
        {
            "SSH_SERVERS_myserver_HOST": "env-server.com",
            "SSH_SERVERS_myserver_PORT": "2222",
            "SSH_SERVERS_myserver_USERNAME": "envuser",
            "DEBUG": "true",
        }
    )

    try:
        settings = Settings()

        assert "myserver" in settings.ssh_servers
        assert settings.ssh_servers["myserver"]["host"] == "env-server.com"
        assert settings.ssh_servers["myserver"]["port"] == 2222
        assert settings.ssh_servers["myserver"]["username"] == "envuser"

    finally:
        # Cleanup
        for key in [
            "SSH_SERVERS_myserver_HOST",
            "SSH_SERVERS_myserver_PORT",
            "SSH_SERVERS_myserver_USERNAME",
            "DEBUG",
        ]:
            if key in os.environ:
                del os.environ[key]


def test_get_server_config(settings_with_config: Settings) -> None:
    """Test getting server configuration."""
    settings = settings_with_config

    config = settings.get_server_config("test-server")
    assert config is not None
    assert config.host == "localhost"
    assert config.port == 22
    assert config.username == "testuser"

    # Test non-existent server
    config = settings.get_server_config("non-existent")
    assert config is None


def test_list_servers(settings_with_config: Settings) -> None:
    """Test listing servers."""
    settings = settings_with_config

    servers = settings.list_servers()
    assert "test-server" in servers
    assert len(servers) == 1


def test_validate_server_config(settings_with_config: Settings) -> None:
    """Test server configuration validation."""
    settings = settings_with_config

    # Valid server
    assert settings.validate_server_config("test-server") is True

    # Invalid server
    assert settings.validate_server_config("non-existent") is False


def test_config_file_precedence() -> None:
    """Test that config file takes precedence over defaults."""
    config_data = {"debug": True, "log_level": "error"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_file = f.name

    try:
        os.environ["SSH_REMOTE_CONTROL_CONFIG"] = temp_file
        settings = Settings()

        assert settings.debug is True
        assert settings.log_level == "error"

    finally:
        os.unlink(temp_file)
        if "SSH_REMOTE_CONTROL_CONFIG" in os.environ:
            del os.environ["SSH_REMOTE_CONTROL_CONFIG"]


def test_invalid_config_file() -> None:
    """Test handling of invalid config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_file = f.name

    try:
        os.environ["SSH_REMOTE_CONTROL_CONFIG"] = temp_file
        # Should not raise an exception, just use defaults
        settings = Settings()
        assert settings.debug is False

    finally:
        os.unlink(temp_file)
        if "SSH_REMOTE_CONTROL_CONFIG" in os.environ:
            del os.environ["SSH_REMOTE_CONTROL_CONFIG"]
