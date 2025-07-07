"""Test web server functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ssh_remote_control.config import Settings
from ssh_remote_control.web_server import create_app


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    settings = Settings()
    settings.ssh_servers = {
        "test-server": {"host": "localhost", "port": 22, "username": "testuser"}
    }
    settings.log_files = ["/var/log/syslog", "/var/log/auth.log"]
    return settings


@pytest.fixture
def app(mock_settings: Settings) -> FastAPI:
    """Create test app with mocked settings."""
    with patch("ssh_remote_control.web_server.Settings") as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        app = create_app()
        return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_dashboard_route(client: TestClient) -> None:
    """Test dashboard page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SSH Remote Control Dashboard" in response.text


def test_api_servers_route(client: TestClient) -> None:
    """Test API servers endpoint."""
    with patch.object(client.app.state, "ssh_manager") as mock_ssh_manager:  # type: ignore[attr-defined]
        mock_ssh_manager.is_connected = AsyncMock(return_value=False)

        response = client.get("/api/servers")
        assert response.status_code == 200

        data = response.json()
        assert "servers" in data
        assert len(data["servers"]) == 1
        assert data["servers"][0]["name"] == "test-server"
        assert data["servers"][0]["host"] == "localhost"
        assert data["servers"][0]["connected"] is False


@pytest.mark.asyncio
async def test_api_server_info_route(client: TestClient) -> None:
    """Test API server info endpoint."""
    mock_info = {
        "hostname": "test-host",
        "uptime": "up 1 day",
        "disk_usage": "50% used",
        "memory": "4GB used",
        "cpu_info": "Intel CPU",
        "load_average": "0.5 0.3 0.2",
        "kernel": "5.4.0",
    }

    with patch.object(client.app.state, "ssh_manager") as mock_ssh_manager:  # type: ignore[attr-defined]
        # Make get_system_info an async mock that returns the mock info
        mock_ssh_manager.get_system_info = AsyncMock(return_value=mock_info)

        response = client.get("/api/servers/test-server/info")
        assert response.status_code == 200

        data = response.json()
        assert "info" in data
        assert data["info"]["hostname"] == "test-host"


def test_api_server_info_not_found(client: TestClient) -> None:
    """Test API server info for non-existent server."""
    response = client.get("/api/servers/non-existent/info")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_connect_server(client: TestClient) -> None:
    """Test API server connection."""
    with patch.object(client.app.state, "ssh_manager") as mock_ssh_manager:  # type: ignore[attr-defined]
        mock_ssh_manager.connect = AsyncMock(return_value=None)

        response = client.post("/api/servers/test-server/connect")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "connected"

        mock_ssh_manager.connect.assert_called_once_with("test-server")


def test_api_connect_server_not_found(client: TestClient) -> None:
    """Test API server connection for non-existent server."""
    response = client.post("/api/servers/non-existent/connect")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_disconnect_server(client: TestClient) -> None:
    """Test API server disconnection."""
    with patch.object(client.app.state, "ssh_manager") as mock_ssh_manager:  # type: ignore[attr-defined]
        mock_ssh_manager.disconnect = AsyncMock(return_value=None)

        response = client.post("/api/servers/test-server/disconnect")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "disconnected"

        mock_ssh_manager.disconnect.assert_called_once_with("test-server")


@pytest.mark.asyncio
async def test_api_execute_command(client: TestClient) -> None:
    """Test API command execution."""
    with patch.object(client.app.state, "ssh_manager") as mock_ssh_manager:  # type: ignore[attr-defined]
        mock_ssh_manager.execute_command = AsyncMock(return_value="command output")

        response = client.post(
            "/api/execute",
            json={"server": "test-server", "command": "ls -la", "timeout": 30},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["output"] == "command output"
        assert data["server"] == "test-server"
        assert data["command"] == "ls -la"

        mock_ssh_manager.execute_command.assert_called_once_with(
            "test-server", "ls -la", timeout=30
        )


def test_api_execute_command_invalid_server(client: TestClient) -> None:
    """Test API command execution for non-existent server."""
    response = client.post(
        "/api/execute", json={"server": "non-existent", "command": "ls -la"}
    )
    assert response.status_code == 404


def test_server_detail_route(client: TestClient) -> None:
    """Test server detail page."""
    response = client.get("/server/test-server")
    assert response.status_code == 200
    assert "test-server" in response.text


def test_server_detail_not_found(client: TestClient) -> None:
    """Test server detail page for non-existent server."""
    response = client.get("/server/non-existent")
    assert response.status_code == 404


def test_connection_manager_initialization() -> None:
    """Test ConnectionManager initialization."""
    from ssh_remote_control.web_server import ConnectionManager

    manager = ConnectionManager()
    assert manager.active_connections == []
    assert manager.log_tasks == {}


@pytest.mark.asyncio
async def test_connection_manager_connect() -> None:
    """Test ConnectionManager WebSocket connection."""
    from ssh_remote_control.web_server import ConnectionManager

    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)

    assert mock_websocket in manager.active_connections
    mock_websocket.accept.assert_called_once()


def test_connection_manager_disconnect() -> None:
    """Test ConnectionManager WebSocket disconnection."""
    from ssh_remote_control.web_server import ConnectionManager

    manager = ConnectionManager()
    mock_websocket = MagicMock()
    manager.active_connections = [mock_websocket]

    manager.disconnect(mock_websocket)

    assert mock_websocket not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_send_message() -> None:
    """Test ConnectionManager sending personal message."""
    from ssh_remote_control.web_server import ConnectionManager

    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.send_personal_message("test message", mock_websocket)

    mock_websocket.send_text.assert_called_once_with("test message")


@pytest.mark.asyncio
async def test_connection_manager_broadcast() -> None:
    """Test ConnectionManager broadcasting message."""
    from ssh_remote_control.web_server import ConnectionManager

    manager = ConnectionManager()
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()
    manager.active_connections = [mock_websocket1, mock_websocket2]

    await manager.broadcast("broadcast message")

    mock_websocket1.send_text.assert_called_once_with("broadcast message")
    mock_websocket2.send_text.assert_called_once_with("broadcast message")


@pytest.mark.asyncio
async def test_connection_manager_broadcast_with_error() -> None:
    """Test ConnectionManager broadcasting with disconnected client."""
    from ssh_remote_control.web_server import ConnectionManager

    manager = ConnectionManager()
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()
    mock_websocket2.send_text.side_effect = ConnectionResetError("Connection lost")
    manager.active_connections = [mock_websocket1, mock_websocket2]

    await manager.broadcast("broadcast message")

    # Working connection should receive message
    mock_websocket1.send_text.assert_called_once_with("broadcast message")
    # Failing connection should be removed
    assert mock_websocket2 not in manager.active_connections
    assert mock_websocket1 in manager.active_connections


def test_websocket_endpoint_setup() -> None:
    """Test WebSocket endpoint is configured."""
    app = create_app()
    routes = [getattr(route, "path", None) for route in app.routes]
    assert "/ws/{server_name}" in routes


def test_static_files_mounted() -> None:
    """Test static files are mounted."""
    app = create_app()

    # Check if static files mount exists
    mounts = [
        mount
        for mount in app.router.routes
        if hasattr(mount, "path") and mount.path == "/static"
    ]
    assert len(mounts) > 0


def test_app_state_initialization() -> None:
    """Test app state is properly initialized."""
    app = create_app()

    assert hasattr(app.state, "settings")
    assert hasattr(app.state, "ssh_manager")
    assert hasattr(app.state, "connection_manager")


def test_app_startup_event() -> None:
    """Test app startup event is configured."""
    app = create_app()

    # Check that lifespan context is configured
    assert hasattr(app.router, "lifespan_context")
    assert app.router.lifespan_context is not None


def test_app_debug_mode() -> None:
    """Test app debug mode configuration."""
    with patch("ssh_remote_control.web_server.Settings") as mock_settings_class:
        mock_settings = Settings()
        mock_settings.debug = True
        mock_settings_class.return_value = mock_settings

        app = create_app()
        assert app.debug is True
