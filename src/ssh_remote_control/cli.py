"""CLI interface for SSH Remote Control."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import Settings
from .server import SSHConnectionManager

app = typer.Typer(
    name="ssh-remote-control",
    help="SSH Remote Control Dashboard",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"ssh-remote-control {__version__}")
        raise typer.Exit()


@app.callback()
def cli_callback(
    _version: bool = typer.Option(
        None, "--version", callback=version_callback, help="Show version and exit"
    ),
) -> None:
    """SSH Remote Control Dashboard."""


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
) -> None:
    """Start the web dashboard."""
    settings = Settings()
    if debug:
        settings.debug = True

    console.print(f"Starting web server on {host}:{port}")
    if reload:
        console.print("[yellow]Auto-reload enabled[/yellow]")

    try:
        uvicorn.run(
            "ssh_remote_control.web_server:create_app",
            host=host,
            port=port,
            reload=reload,
            factory=True,
            log_level="debug" if debug else "info",
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


@app.command()
def list_servers() -> None:
    """List configured SSH servers."""
    settings = Settings()

    if not settings.ssh_servers:
        console.print("[red]No SSH servers configured[/red]")
        console.print("Add servers to your configuration file or environment variables")
        return

    table = Table(title="Configured SSH Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Host", style="green")
    table.add_column("Port", style="yellow")
    table.add_column("User", style="blue")

    for name, config in settings.ssh_servers.items():  # pylint: disable=no-member
        table.add_row(
            name,
            config.get("host", "N/A"),
            str(config.get("port", 22)),
            config.get("username", "N/A"),
        )

    console.print(table)


@app.command()
def test_connection(
    server: str = typer.Argument(..., help="Server name to test"),
) -> None:
    """Test SSH connection to a server."""

    async def _test_connection() -> None:
        settings = Settings()

        if server not in settings.ssh_servers:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        console.print(f"Testing connection to {server}...")

        manager = SSHConnectionManager(settings)
        try:
            await manager.connect(server)
            console.print(f"[green]Successfully connected to {server}[/green]")

            # Test a simple command
            result = await manager.execute_command(
                server, "echo 'Connection test successful'"
            )
            console.print(f"Test command output: {result.strip()}")

        except (ConnectionError, OSError, ValueError, RuntimeError) as e:
            console.print(f"[red]Connection failed: {e}[/red]")
        finally:
            await manager.close_all()

    asyncio.run(_test_connection())


@app.command()
def execute(
    server: str = typer.Argument(..., help="Server name"),
    command: str = typer.Argument(..., help="Command to execute"),
) -> None:
    """Execute a command on a remote server."""

    async def _execute() -> None:
        settings = Settings()

        if server not in settings.ssh_servers:
            console.print(f"[red]Server '{server}' not found in configuration[/red]")
            return

        console.print(f"Executing '{command}' on {server}...")

        manager = SSHConnectionManager(settings)
        try:
            await manager.connect(server)

            result = await manager.execute_command(server, command)
            console.print(f"[green]Output:[/green]\n{result}")

        except (ConnectionError, OSError, ValueError, RuntimeError) as e:
            console.print(f"[red]Command execution failed: {e}[/red]")
        finally:
            await manager.close_all()

    asyncio.run(_execute())


@app.command()
def init_config(
    config_path: str = typer.Option(
        "", "--config", "-c", help="Path to create config file"
    ),
) -> None:
    """Initialize a sample configuration file."""
    if config_path:
        config_file_path = Path(config_path)
    else:
        config_file_path = Path.home() / ".ssh-remote-control.yaml"

    if config_file_path.exists() and not typer.confirm(
        f"Config file {config_file_path} already exists. Overwrite?"
    ):
        return

    sample_config = """# SSH Remote Control Configuration
# You can also use environment variables (SSH_SERVERS_<name>_<key>)

debug: false
log_level: "info"

ssh_servers:
  example-server:
    host: "example.com"
    port: 22
    username: "your-username"
    # Optional: specify key file path
    # key_file: "/path/to/your/private/key"
    # Optional: specify known_hosts file
    # known_hosts: "/path/to/known_hosts"

  local-server:
    host: "localhost"
    port: 22
    username: "your-local-username"

# Web server settings
web:
  host: "127.0.0.1"
  port: 8000

# Log files to monitor (optional)
log_files:
  - "/var/log/syslog"
  - "/var/log/auth.log"
  - "/var/log/nginx/access.log"
"""

    try:
        config_file_path.write_text(sample_config)
        console.print(
            f"[green]Sample configuration created at {config_file_path}[/green]"
        )
        console.print("\nEdit the configuration file to add your SSH servers.")
        console.print("You can also use environment variables:")
        console.print("  SSH_SERVERS_myserver_HOST=example.com")
        console.print("  SSH_SERVERS_myserver_USERNAME=myuser")
    except (OSError, PermissionError, FileExistsError) as e:
        console.print(f"[red]Failed to create config file: {e}[/red]")


def main() -> None:
    """Main entry point."""
    try:
        app()
    except (typer.Exit, SystemExit, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()
