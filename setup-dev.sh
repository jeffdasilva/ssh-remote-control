#!/bin/bash
# Development environment setup script for SSH Remote Control

set -e

echo "🚀 Setting up SSH Remote Control development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Then restart your shell and run this script again."
    exit 1
fi

echo "✅ uv is installed"

# Install Python 3.12 if not available
echo "📦 Installing Python 3.12..."
uv python install 3.12

# Create and sync virtual environment
echo "🔧 Creating virtual environment..."
uv venv

# Sync dependencies
echo "📚 Installing dependencies..."
uv sync

# Create .env file if it doesn't exist and .env.example exists
if [ ! -f .env ] && [ -f .env.example ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "   Please edit .env file with your configuration"
elif [ ! -f .env ]; then
    echo "📝 Creating basic .env file..."
    cat > .env << 'EOF'
# SSH Remote Control Environment Variables
# Copy this to .env and customize as needed

# Debug mode
DEBUG=false

# Log level (debug, info, warning, error)
LOG_LEVEL=info

# Web server settings
WEB_HOST=127.0.0.1
WEB_PORT=8000

# Example server configuration via environment variables
# SSH_SERVERS_myserver_HOST=example.com
# SSH_SERVERS_myserver_USERNAME=myuser
# SSH_SERVERS_myserver_PORT=22
EOF
    echo "   Please edit .env file with your configuration"
fi

# Create sample config if it doesn't exist
if [ ! -f ~/.ssh-remote-control.yaml ]; then
    echo "⚙️  Creating sample configuration..."
    uv run ssh-remote-control init-config
    echo "   Configuration created at ~/.ssh-remote-control.yaml"
    echo "   Please edit it to add your SSH servers"
fi

# Check if VS Code is available and recommend extensions
if command -v code &> /dev/null; then
    echo "💡 VS Code detected! The project includes configuration for:"
    echo "   - Python interpreter detection"
    echo "   - Linting and formatting"
    echo "   - Debugging configurations"
    echo "   - Recommended extensions"
    echo ""
    echo "   Open the project in VS Code and install recommended extensions when prompted."
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit ~/.ssh-remote-control.yaml to configure your SSH servers"
echo "   2. Set up SSH key authentication for your servers"
echo "   3. Test the setup with: uv run ssh-remote-control --help"
echo ""
echo "🔧 Common commands:"
echo "   • Activate virtual environment:  source .venv/bin/activate"
echo "   • Run application:              uv run ssh-remote-control --help"
echo "   • List servers:                 uv run ssh-remote-control list-servers"
echo "   • Test connection:              uv run ssh-remote-control test-connection <server>"
echo "   • Start web server:             uv run ssh-remote-control web --reload"
echo "   • Run tests:                    uv run pytest"
echo "   • Format code:                  uv run ruff format ."
echo "   • Lint code:                    uv run ruff check ."
echo "   • Type check:                   uv run mypy src"
echo ""
echo "📖 For more information, see README.md"
