@echo off
REM Development environment setup script for SSH Remote Control

echo 🚀 Setting up SSH Remote Control development environment...

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: uv is not installed. Please install uv first:
    echo    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo    Then restart your shell and run this script again.
    exit /b 1
)

echo ✅ uv is installed

REM Install Python 3.12 if not available
echo 📦 Installing Python 3.12...
uv python install 3.12

REM Create and sync virtual environment
echo 🔧 Creating virtual environment...
uv venv

REM Sync dependencies
echo 📚 Installing dependencies...
uv sync

REM Create .env file if it doesn't exist and .env.example exists
if not exist .env (
    if exist .env.example (
        echo 📝 Creating .env file from template...
        copy .env.example .env
        echo    Please edit .env file with your configuration
    ) else (
        echo 📝 Creating basic .env file...
        (
            echo # SSH Remote Control Environment Variables
            echo # Copy this to .env and customize as needed
            echo.
            echo # Debug mode
            echo DEBUG=false
            echo.
            echo # Log level ^(debug, info, warning, error^)
            echo LOG_LEVEL=info
            echo.
            echo # Web server settings
            echo WEB_HOST=127.0.0.1
            echo WEB_PORT=8000
            echo.
            echo # Example server configuration via environment variables
            echo # SSH_SERVERS_myserver_HOST=example.com
            echo # SSH_SERVERS_myserver_USERNAME=myuser
            echo # SSH_SERVERS_myserver_PORT=22
        ) > .env
        echo    Please edit .env file with your configuration
    )
)

REM Create sample config if it doesn't exist
if not exist "%USERPROFILE%\.ssh-remote-control.yaml" (
    echo ⚙️  Creating sample configuration...
    uv run ssh-remote-control init-config
    echo    Configuration created at %USERPROFILE%\.ssh-remote-control.yaml
    echo    Please edit it to add your SSH servers
)

REM Check if VS Code is available and recommend extensions
where code >nul 2>nul
if %errorlevel% equ 0 (
    echo 💡 VS Code detected! The project includes configuration for:
    echo    - Python interpreter detection
    echo    - Linting and formatting
    echo    - Debugging configurations
    echo    - Recommended extensions
    echo.
    echo    Open the project in VS Code and install recommended extensions when prompted.
)

echo.
echo 🎉 Development environment setup complete!
echo.
echo 📋 Next steps:
echo    1. Edit %USERPROFILE%\.ssh-remote-control.yaml to configure your SSH servers
echo    2. Set up SSH key authentication for your servers
echo    3. Test the setup with: uv run ssh-remote-control --help
echo.
echo 🔧 Common commands:
echo    • Activate virtual environment:  .venv\Scripts\activate
echo    • Run application:              uv run ssh-remote-control --help
echo    • List servers:                 uv run ssh-remote-control list-servers
echo    • Test connection:              uv run ssh-remote-control test-connection ^<server^>
echo    • Start web server:             uv run ssh-remote-control web --reload
echo    • Run tests:                    uv run pytest
echo    • Format code:                  uv run ruff format .
echo    • Lint code:                    uv run ruff check .
echo    • Type check:                   uv run mypy src
echo.
echo 📖 For more information, see README.md
