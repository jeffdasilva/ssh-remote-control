"""Configuration management for SSH Remote Control."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .yaml_compat import safe_load


class ServerConfig(BaseModel):
    """Configuration for a single SSH server."""

    host: str
    port: int = 22
    username: str
    key_file: str | None = None
    known_hosts: str | None = None
    password: str | None = None
    passphrase: str | None = None


class WebConfig(BaseModel):
    """Web server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application settings
    debug: bool = False
    log_level: str = "info"

    # SSH servers configuration
    ssh_servers: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # Web configuration
    web: WebConfig = Field(default_factory=WebConfig)

    # Log files to monitor
    log_files: list[str] = Field(default_factory=list)

    # SSH connection settings
    ssh_connect_timeout: int = 30
    ssh_keepalive_interval: int = 60

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with config file support."""
        super().__init__(**kwargs)
        self._load_config_files()
        self._load_env_servers()

    def _load_config_files(self) -> None:
        """Load configuration from YAML file."""
        config_paths = [
            Path.cwd() / "ssh-remote-control.yaml",
            Path.cwd() / "ssh-remote-control.yml",
            Path.home() / ".ssh-remote-control.yaml",
            Path.home() / ".ssh-remote-control.yml",
        ]

        config_file = os.environ.get("SSH_REMOTE_CONTROL_CONFIG")
        if config_file:
            config_paths.insert(0, Path(config_file))

        for config_path in config_paths:
            if not config_path.exists():
                continue

            try:
                config = self._load_config_file(config_path)
                if config:
                    self._apply_config(config)
                break
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Warning: Could not load config file {config_path}: {e}")

    def _load_config_file(self, config_path: Path) -> dict[str, Any] | None:
        """Load configuration from a file."""
        with open(config_path, encoding="utf-8") as f:
            result = safe_load(f)
            if isinstance(result, dict):
                return cast(dict[str, Any], result)
            return None

    def _apply_config(self, config: dict[str, Any]) -> None:
        """Apply configuration values to settings."""
        for key, value in config.items():
            if not hasattr(self, key):
                continue
            if key == "web" and isinstance(value, dict):
                # Convert web dict to WebConfig object
                self.web = WebConfig(**value)
            else:
                setattr(self, key, value)

    def _load_env_servers(self) -> None:
        """Load SSH servers from environment variables."""
        # Look for SSH_SERVERS_<name>_<key> environment variables
        servers: dict[str, dict[str, Any]] = {}

        for key, value in os.environ.items():
            if key.startswith("SSH_SERVERS_"):
                parts = key.split("_", 3)
                if len(parts) >= 4:
                    _, _, server_name, config_key = parts
                    server_name = server_name.lower()
                    config_key = config_key.lower()

                    if server_name not in servers:
                        servers[server_name] = {}

                    # Convert port to int if needed
                    if config_key == "port":
                        try:
                            int_value = int(value)
                            servers[server_name][config_key] = int_value
                        except ValueError:
                            continue
                    else:
                        servers[server_name][config_key] = value

        # Merge with existing servers
        for name, config in servers.items():
            if name not in self.ssh_servers:
                self.ssh_servers[name] = {}
            self.ssh_servers[name].update(config)

    def get_server_config(self, name: str) -> ServerConfig | None:
        """Get configuration for a specific server."""
        if name not in self.ssh_servers:
            return None

        try:
            return ServerConfig(**self.ssh_servers[name])
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def list_servers(self) -> list[str]:
        """List all configured server names."""
        return list(self.ssh_servers.keys())  # pylint: disable=no-member

    def validate_server_config(self, name: str) -> bool:
        """Validate that a server configuration is complete."""
        config = self.get_server_config(name)
        if not config:
            return False

        # Check required fields
        return bool(config.host and config.username)
