"""Web server for SSH Remote Control Dashboard."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import __version__
from .config import Settings
from .server import SSHConnectionManager

logger = logging.getLogger(__name__)


class CommandRequest(BaseModel):
    """Request model for command execution."""

    server: str
    command: str
    timeout: int | None = 30


class LogTailRequest(BaseModel):
    """Request model for log tailing."""

    server: str
    file_path: str
    lines: int = 50


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.log_tasks: dict[str, asyncio.Task[Any]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except (ConnectionResetError, ConnectionAbortedError, RuntimeError) as e:
            logger.error("Error sending message: %s", e)

    async def broadcast(self, message: str) -> None:
        """Broadcast a message to all connected WebSockets."""
        disconnected: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except (ConnectionResetError, ConnectionAbortedError, RuntimeError):
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def start_log_tail(
        self, server: str, file_path: str, websocket: WebSocket
    ) -> None:
        """Start tailing a log file and send updates via WebSocket."""
        task_key = f"{server}:{file_path}"

        # Stop existing task if any
        if task_key in self.log_tasks:
            self.log_tasks[task_key].cancel()

        async def log_callback(line: str) -> None:
            """Callback for log lines."""
            await self.send_personal_message(
                json.dumps(
                    {
                        "type": "log_line",
                        "server": server,
                        "file": file_path,
                        "line": line.strip(),
                    }
                ),
                websocket,
            )

        try:
            ssh_manager = websocket.app.state.ssh_manager
            process = await ssh_manager.tail_file(server, file_path, log_callback)

            # Store the task
            self.log_tasks[task_key] = asyncio.create_task(process.wait())

        except (ConnectionError, OSError, ValueError, RuntimeError) as e:
            await self.send_personal_message(
                json.dumps(
                    {"type": "error", "message": f"Failed to start log tail: {e}"}
                ),
                websocket,
            )

    def stop_log_tail(self, server: str, file_path: str) -> None:
        """Stop tailing a log file."""
        task_key = f"{server}:{file_path}"
        if task_key in self.log_tasks:
            self.log_tasks[task_key].cancel()
            del self.log_tasks[task_key]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = Settings()

    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None]:
        """Application lifespan context."""
        # Startup
        logger.info("SSH Remote Control Dashboard starting up...")
        yield
        # Shutdown
        logger.info("SSH Remote Control Dashboard shutting down...")
        await fastapi_app.state.ssh_manager.close_all()

    app = FastAPI(
        title="SSH Remote Control Dashboard",
        description="Monitor and control remote servers via SSH",
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Initialize managers
    ssh_manager = SSHConnectionManager(settings)
    connection_manager = ConnectionManager()

    # Store in app state
    app.state.settings = settings
    app.state.ssh_manager = ssh_manager
    app.state.connection_manager = connection_manager

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Templates
    templates = Jinja2Templates(directory="templates")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        """Main dashboard page."""
        servers = settings.list_servers()
        return templates.TemplateResponse(
            request, "dashboard.html", {"servers": servers}
        )

    @app.get("/api/servers", response_class=JSONResponse)
    async def get_servers(request: Request) -> JSONResponse:
        """Get list of configured servers."""
        servers: list[dict[str, Any]] = []
        for name in settings.list_servers():
            config = settings.get_server_config(name)
            if config:
                servers.append(
                    {
                        "name": name,
                        "host": config.host,
                        "port": config.port,
                        "username": config.username,
                        "connected": await request.app.state.ssh_manager.is_connected(
                            name
                        ),
                    }
                )
        return JSONResponse({"servers": servers})

    @app.get("/api/servers/{server_name}/info", response_class=JSONResponse)
    async def get_server_info(server_name: str, request: Request) -> JSONResponse:
        """Get system information for a server."""
        if server_name not in settings.list_servers():
            raise HTTPException(status_code=404, detail="Server not found")

        try:
            info = await request.app.state.ssh_manager.get_system_info(server_name)
            return JSONResponse({"info": info})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/api/servers/{server_name}/connect", response_class=JSONResponse)
    async def connect_server(server_name: str, request: Request) -> JSONResponse:
        """Connect to a server."""
        if server_name not in settings.list_servers():
            raise HTTPException(status_code=404, detail="Server not found")

        try:
            await request.app.state.ssh_manager.connect(server_name)
            return JSONResponse({"status": "connected"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/api/servers/{server_name}/disconnect", response_class=JSONResponse)
    async def disconnect_server(server_name: str, request: Request) -> JSONResponse:
        """Disconnect from a server."""
        if server_name not in settings.list_servers():
            raise HTTPException(status_code=404, detail="Server not found")

        try:
            await request.app.state.ssh_manager.disconnect(server_name)
            return JSONResponse({"status": "disconnected"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/api/execute", response_class=JSONResponse)
    async def execute_command(
        command_request: CommandRequest, request: Request
    ) -> JSONResponse:
        """Execute a command on a remote server."""
        if command_request.server not in settings.list_servers():
            raise HTTPException(status_code=404, detail="Server not found")

        try:
            output = await request.app.state.ssh_manager.execute_command(
                command_request.server,
                command_request.command,
                timeout=command_request.timeout,
            )
            return JSONResponse(
                {
                    "output": output,
                    "server": command_request.server,
                    "command": command_request.command,
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/server/{server_name}", response_class=HTMLResponse)
    async def server_detail(request: Request, server_name: str) -> HTMLResponse:
        """Server detail page."""
        if server_name not in settings.list_servers():
            raise HTTPException(status_code=404, detail="Server not found")

        config = settings.get_server_config(server_name)
        return templates.TemplateResponse(
            request,
            "server_detail.html",
            {
                "server_name": server_name,
                "server_config": config,
                "log_files": settings.log_files,
            },
        )

    @app.websocket("/ws/{server_name}")
    async def websocket_endpoint(websocket: WebSocket, server_name: str) -> None:
        """WebSocket endpoint for real-time updates."""
        await connection_manager.connect(websocket)

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message["type"] == "start_log_tail":
                    await connection_manager.start_log_tail(
                        server_name, message["file_path"], websocket
                    )
                elif message["type"] == "stop_log_tail":
                    connection_manager.stop_log_tail(server_name, message["file_path"])
                elif message["type"] == "execute_command":
                    try:
                        output = await websocket.app.state.ssh_manager.execute_command(
                            server_name, message["command"]
                        )
                        await connection_manager.send_personal_message(
                            json.dumps(
                                {
                                    "type": "command_output",
                                    "command": message["command"],
                                    "output": output,
                                }
                            ),
                            websocket,
                        )
                    except (ConnectionError, OSError, ValueError, RuntimeError) as e:
                        await connection_manager.send_personal_message(
                            json.dumps({"type": "error", "message": str(e)}), websocket
                        )

        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
        except (
            ConnectionResetError,
            ConnectionAbortedError,
            RuntimeError,
            ValueError,
            json.JSONDecodeError,
        ) as e:
            logger.error("WebSocket error: %s", e)
            connection_manager.disconnect(websocket)

    return app


if __name__ == "__main__":
    import uvicorn

    application = create_app()
    uvicorn.run(application, host="127.0.0.1", port=8000)
