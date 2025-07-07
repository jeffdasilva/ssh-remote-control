"""Test CLI functionality."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import typer
from click.testing import Result
from typer.testing import CliRunner

from ssh_remote_control import __version__
from ssh_remote_control.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_settings() -> Generator[MagicMock, None, None]:
    """Mock settings for testing."""
    with patch("ssh_remote_control.cli.Settings") as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings.ssh_servers = {
            "test-server": {"host": "localhost", "port": 22, "username": "testuser"}
        }
        mock_settings_class.return_value = mock_settings
        yield mock_settings


def test_cli_help(runner: CliRunner) -> None:
    """Test CLI help output."""
    result: Result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SSH Remote Control Dashboard" in result.output


def test_list_servers_command(runner: CliRunner, mock_settings: MagicMock) -> None:
    """Test list-servers command."""
    result: Result = runner.invoke(app, ["list-servers"])
    assert result.exit_code == 0
    assert "test-server" in result.output
    assert "localhost" in result.output


def test_list_servers_no_servers(runner: CliRunner) -> None:
    """Test list-servers command with no servers configured."""
    with patch("ssh_remote_control.cli.Settings") as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings.ssh_servers = {}
        mock_settings_class.return_value = mock_settings

        result: Result = runner.invoke(app, ["list-servers"])
        assert result.exit_code == 0
        assert "No SSH servers configured" in result.output


@patch("uvicorn.run")
def test_web_command(mock_uvicorn: MagicMock, runner: CliRunner) -> None:
    """Test web command."""
    result: Result = runner.invoke(app, ["web"])
    assert result.exit_code == 0
    mock_uvicorn.assert_called_once()


@patch("uvicorn.run")
def test_web_command_with_options(mock_uvicorn: MagicMock, runner: CliRunner) -> None:
    """Test web command with options."""
    result: Result = runner.invoke(
        app, ["web", "--host", "0.0.0.0", "--port", "8080", "--reload"]
    )
    assert result.exit_code == 0

    # Check that uvicorn.run was called with correct parameters
    call_args = mock_uvicorn.call_args
    assert call_args is not None
    # Type ignore for mock call args access
    kwargs: dict[str, Any] = call_args[1]  # type: ignore[misc]
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 8080
    assert kwargs["reload"] is True


@patch("ssh_remote_control.cli.asyncio.run")
def test_test_connection_command(
    mock_asyncio_run: MagicMock, runner: CliRunner, mock_settings: MagicMock
) -> None:
    """Test test-connection command."""
    result: Result = runner.invoke(app, ["test-connection", "test-server"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


def test_test_connection_invalid_server(runner: CliRunner) -> None:
    """Test test-connection command with invalid server."""
    with patch("ssh_remote_control.cli.Settings") as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings.ssh_servers = {}
        mock_settings_class.return_value = mock_settings

        with patch("ssh_remote_control.cli.asyncio.run") as mock_asyncio_run:
            result: Result = runner.invoke(app, ["test-connection", "non-existent"])
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()


@patch("ssh_remote_control.cli.asyncio.run")
def test_execute_command(
    mock_asyncio_run: MagicMock, runner: CliRunner, mock_settings: MagicMock
) -> None:
    """Test execute command."""
    result: Result = runner.invoke(app, ["execute", "test-server", "ls -la"])
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


def test_execute_command_invalid_server(runner: CliRunner) -> None:
    """Test execute command with invalid server."""
    with patch("ssh_remote_control.cli.Settings") as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings.ssh_servers = {}
        mock_settings_class.return_value = mock_settings

        # Mock the entire execute command to avoid async issues
        with (
            patch("ssh_remote_control.cli.SSHConnectionManager"),
            patch("ssh_remote_control.cli.asyncio.run") as mock_asyncio_run,
        ):
            # Mock the async function call to prevent coroutine warnings
            def mock_run(coro: Any) -> None:
                # If a coroutine is passed, close it to avoid warnings
                if hasattr(coro, "close"):
                    coro.close()
                return None

            mock_asyncio_run.side_effect = mock_run
            result: Result = runner.invoke(app, ["execute", "non-existent", "ls"])
            assert result.exit_code == 0
            mock_asyncio_run.assert_called_once()


def test_init_config_command(runner: CliRunner) -> None:
    """Test init-config command."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test-config.yaml"

        # Mock typer.confirm to avoid interactive prompts
        with patch("ssh_remote_control.cli.typer.confirm", return_value=True):
            result: Result = runner.invoke(
                app, ["init-config", "--config", str(config_path)]
            )
            assert result.exit_code == 0
            assert config_path.exists()

            # Check config file contents
            config_content = config_path.read_text()
            assert "ssh_servers:" in config_content
            assert "example-server:" in config_content


def test_init_config_default_path(runner: CliRunner) -> None:
    """Test init-config command with default path."""
    with patch("ssh_remote_control.cli.Path.home") as mock_home:
        mock_home.return_value = Path("/tmp")

        with patch("ssh_remote_control.cli.Path.exists") as mock_exists:
            mock_exists.return_value = False

            with patch("ssh_remote_control.cli.Path.write_text") as mock_write:
                result: Result = runner.invoke(app, ["init-config"])
                assert result.exit_code == 0
                mock_write.assert_called_once()


def test_init_config_overwrite_confirmation(runner: CliRunner) -> None:
    """Test init-config command with existing file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test-config.yaml"
        config_path.write_text("existing content")

        # Test declining to overwrite
        result: Result = runner.invoke(
            app, ["init-config", "--config", str(config_path)], input="n\n"
        )
        assert result.exit_code == 0
        assert config_path.read_text() == "existing content"

        # Test accepting to overwrite
        result = runner.invoke(
            app, ["init-config", "--config", str(config_path)], input="y\n"
        )
        assert result.exit_code == 0
        assert "ssh_servers:" in config_path.read_text()


def test_main_function() -> None:
    """Test main function entry point."""
    with patch("ssh_remote_control.cli.app") as mock_app:
        from ssh_remote_control.cli import main

        main()
        mock_app.assert_called_once()


def test_main_function_keyboard_interrupt() -> None:
    """Test main function with keyboard interrupt."""
    with patch("ssh_remote_control.cli.app") as mock_app:
        mock_app.side_effect = KeyboardInterrupt()

        from ssh_remote_control.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1  # type: ignore[attr-defined]


def test_main_function_exception() -> None:
    """Test main function with exception."""
    with patch("ssh_remote_control.cli.app") as mock_app:
        mock_app.side_effect = typer.Exit(1)

        from ssh_remote_control.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1  # type: ignore[attr-defined]


@patch("ssh_remote_control.cli.SSHConnectionManager")
def test_connection_manager_usage(
    mock_ssh_manager_class: MagicMock, runner: CliRunner, mock_settings: MagicMock
) -> None:
    """Test that SSH connection manager is used correctly."""
    mock_ssh_manager = MagicMock()
    mock_ssh_manager_class.return_value = mock_ssh_manager

    with patch("ssh_remote_control.cli.asyncio.run") as mock_asyncio_run:
        result: Result = runner.invoke(app, ["test-connection", "test-server"])
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()


def test_console_output_formatting(runner: CliRunner, mock_settings: MagicMock) -> None:
    """Test console output formatting."""
    result: Result = runner.invoke(app, ["list-servers"])
    assert result.exit_code == 0

    # Check that output contains formatted table
    assert "Name" in result.output
    assert "Host" in result.output
    assert "Port" in result.output
    assert "User" in result.output


def test_version_option(runner: CliRunner) -> None:
    """Test --version option."""
    result: Result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"ssh-remote-control {__version__}" in result.output
