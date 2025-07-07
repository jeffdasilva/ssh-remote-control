# SSH Remote Control Dashboard

A Python web application for monitoring and controlling remote servers via SSH. Built with FastAPI, AsyncSSH, and modern Python tooling.

## Features

- 🖥️ **Web Dashboard**: Modern, responsive web interface for server management
- 🔧 **CLI Interface**: Powerful command-line tools for server administration
- 🔄 **Real-time Updates**: Live log monitoring and command output via WebSockets
- 🌐 **Multi-server Support**: Manage multiple servers from a single interface
- 🔐 **Secure Authentication**: SSH key-based authentication with connection reuse
- 📊 **System Monitoring**: Real-time system information display
- 🚀 **Async Performance**: Built with async/await for high performance
- 🔧 **Production Ready**: Comprehensive testing, type checking, and CI/CD pipeline

## Screenshots

### Dashboard Overview
The main dashboard shows all configured servers with their connection status:
- Server cards with connection indicators
- Quick connect/disconnect actions
- System information at a glance

### Server Detail View
Individual server pages provide comprehensive management:
- **Overview Tab**: System information and quick actions
- **Terminal Tab**: Interactive command execution
- **Logs Tab**: Real-time log file monitoring

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- SSH access to target servers

### Installation

```bash
# Clone the repository
git clone https://github.com/jeffdasilva/ssh-remote-control.git
cd ssh-remote-control

# Install dependencies
uv sync --all-extras --dev

# Initialize configuration
uv run ssh-remote-control init-config

# Edit the configuration file
nano ~/.ssh-remote-control.yaml
```

### Basic Configuration

Create a configuration file at `~/.ssh-remote-control.yaml`:

```yaml
debug: false
log_level: "info"

ssh_servers:
  production:
    host: "prod.example.com"
    port: 22
    username: "deploy"
    key_file: "~/.ssh/id_ed25519"
  
  staging:
    host: "staging.example.com"
    port: 22
    username: "deploy"
    key_file: "~/.ssh/id_ed25519"

web:
  host: "127.0.0.1"
  port: 8000

log_files:
  - "/var/log/syslog"
  - "/var/log/auth.log"
  - "/var/log/nginx/access.log"
```

### Running the Application

```bash
# Start the web server
uv run ssh-remote-control web

# Or with custom options
uv run ssh-remote-control web --host 0.0.0.0 --port 8080 --reload
```

Visit `http://localhost:8000` to access the dashboard.

## SSH Authentication Setup

### SSH Key Authentication (Recommended)

1. **Generate SSH Key Pair**:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **Copy Public Key to Server**:
   ```bash
   ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server.com
   ```

3. **Test Connection**:
   ```bash
   ssh -i ~/.ssh/id_ed25519 user@server.com
   ```

4. **Configure in Application**:
   ```yaml
   ssh_servers:
     myserver:
       host: "server.com"
       username: "user"
       key_file: "~/.ssh/id_ed25519"
   ```

### Known Hosts Configuration

For security, configure known_hosts file:
```bash
# Add server to known_hosts
ssh-keyscan -H server.com >> ~/.ssh/known_hosts

# Or connect manually first
ssh user@server.com
```

### Troubleshooting SSH Issues

**Permission Denied**:
- Check SSH key permissions: `chmod 600 ~/.ssh/id_ed25519`
- Verify public key is in server's `~/.ssh/authorized_keys`

**Host Key Verification Failed**:
- Add server to known_hosts: `ssh-keyscan -H server.com >> ~/.ssh/known_hosts`

**Connection Timeout**:
- Check firewall settings
- Verify SSH service is running: `sudo systemctl status ssh`

## Configuration

### Configuration File Locations

The application searches for configuration files in this order:
1. `./ssh-remote-control.yaml` (current directory)
2. `~/.ssh-remote-control.yaml` (home directory)
3. Custom path via `SSH_REMOTE_CONTROL_CONFIG` environment variable

### Environment Variables

You can configure servers using environment variables:

```bash
# Server configuration
SSH_SERVERS_myserver_HOST=example.com
SSH_SERVERS_myserver_PORT=22
SSH_SERVERS_myserver_USERNAME=myuser
SSH_SERVERS_myserver_KEY_FILE=/path/to/key

# Application settings
DEBUG=true
LOG_LEVEL=debug
```

### Complete Configuration Example

```yaml
# Application settings
debug: false
log_level: "info"

# SSH connection settings
ssh_connect_timeout: 30
ssh_keepalive_interval: 60

# Web server settings
web:
  host: "127.0.0.1"
  port: 8000

# Server definitions
ssh_servers:
  web-server:
    host: "web.example.com"
    port: 22
    username: "www-data"
    key_file: "~/.ssh/web_server_key"
    known_hosts: "~/.ssh/known_hosts"
  
  database-server:
    host: "db.example.com"
    port: 2222
    username: "dbadmin"
    key_file: "~/.ssh/db_server_key"
  
  monitoring-server:
    host: "monitor.example.com"
    port: 22
    username: "monitor"
    # Optional: use password (not recommended)
    # password: "secretpassword"

# Log files to monitor
log_files:
  - "/var/log/syslog"
  - "/var/log/auth.log"
  - "/var/log/nginx/access.log"
  - "/var/log/nginx/error.log"
  - "/var/log/mysql/error.log"
  - "/var/log/apache2/access.log"
  - "/var/log/apache2/error.log"
```

## CLI Usage

### List Servers
```bash
uv run ssh-remote-control list-servers
```

### Test Connection
```bash
uv run ssh-remote-control test-connection myserver
```

### Execute Commands
```bash
uv run ssh-remote-control execute myserver "df -h"
uv run ssh-remote-control execute myserver "systemctl status nginx"
```

### Start Web Server
```bash
# Default settings
uv run ssh-remote-control web

# Custom host and port
uv run ssh-remote-control web --host 0.0.0.0 --port 8080

# Development mode with auto-reload
uv run ssh-remote-control web --reload --debug
```

## API Reference

### REST Endpoints

- `GET /` - Dashboard homepage
- `GET /api/servers` - List all configured servers
- `GET /api/servers/{server}/info` - Get server system information
- `POST /api/servers/{server}/connect` - Connect to server
- `POST /api/servers/{server}/disconnect` - Disconnect from server
- `POST /api/execute` - Execute command on server
- `GET /server/{server}` - Server detail page

### WebSocket Endpoints

- `WS /ws/{server}` - Real-time server communication

**WebSocket Message Types**:
```json
// Execute command
{
  "type": "execute_command",
  "command": "ls -la"
}

// Start log tailing
{
  "type": "start_log_tail",
  "file_path": "/var/log/syslog"
}

// Stop log tailing
{
  "type": "stop_log_tail",
  "file_path": "/var/log/syslog"
}
```

## Development

### Setup Development Environment

```bash
# Install dependencies with development tools
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/ssh_remote_control --cov-report=html

# Type checking
uv run mypy src/ssh_remote_control --strict

# Linting
uv run ruff check
uv run ruff format

# Run pylint
uv run pylint src/ssh_remote_control
```

### Project Structure

```
ssh-remote-control/
├── src/ssh_remote_control/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── server.py           # SSH connection manager
│   └── web_server.py       # FastAPI web server
├── templates/
│   ├── dashboard.html      # Main dashboard
│   └── server_detail.html  # Server detail page
├── static/                 # Static files (CSS, JS, images)
├── tests/
│   ├── test_config.py      # Configuration tests
│   ├── test_server.py      # SSH manager tests
│   ├── test_web_server.py  # Web server tests
│   └── test_cli.py         # CLI tests
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container image
├── .github/workflows/      # CI/CD pipeline
└── README.md
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_config.py -v

# Run tests with coverage
uv run pytest --cov=src/ssh_remote_control --cov-report=term-missing

# Run tests in parallel
uv run pytest -n auto
```

### Code Quality

The project enforces strict code quality standards:
- **mypy**: Strict type checking
- **ruff**: Fast linting and formatting
- **pylint**: Additional code quality checks
- **pytest**: Comprehensive test coverage
- **bandit**: Security linting

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t ssh-remote-control .

# Run container
docker run -d -p 8000:8000 \
  -e SSH_SERVERS_myserver_HOST=example.com \
  -e SSH_SERVERS_myserver_USERNAME=deploy \
  -v ~/.ssh:/home/appuser/.ssh:ro \
  ssh-remote-control
```

### Production Deployment

1. **Use a reverse proxy** (nginx) for HTTPS:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /ws {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

2. **Use systemd for service management**:
   ```ini
   [Unit]
   Description=SSH Remote Control Dashboard
   After=network.target
   
   [Service]
   Type=exec
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/ssh-remote-control
   ExecStart=/opt/ssh-remote-control/.venv/bin/ssh-remote-control web --host 127.0.0.1 --port 8000
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Configure environment variables**:
   ```bash
   # /etc/environment or systemd service file
   SSH_SERVERS_prod_HOST=prod.example.com
   SSH_SERVERS_prod_USERNAME=deploy
   SSH_SERVERS_prod_KEY_FILE=/home/deploy/.ssh/id_ed25519
   ```

## Security Considerations

- **SSH Key Authentication**: Always use SSH keys instead of passwords
- **Connection Limits**: Configure appropriate connection timeouts
- **Input Validation**: All user inputs are validated and sanitized
- **Secure Defaults**: Security-focused default configuration
- **Environment Variables**: Store sensitive data in environment variables
- **Regular Updates**: Keep dependencies updated for security patches

## Troubleshooting

### Common Issues

**ImportError: No module named 'ssh_remote_control'**:
```bash
# Make sure you're in the project directory and dependencies are installed
uv sync --all-extras --dev
```

**SSH Connection Refused**:
- Check if SSH service is running: `sudo systemctl status ssh`
- Verify firewall settings: `sudo ufw status`
- Test connection manually: `ssh user@server.com`

**Permission Denied (publickey)**:
- Check SSH key permissions: `chmod 600 ~/.ssh/id_ed25519`
- Verify public key is in server's authorized_keys
- Test key: `ssh -i ~/.ssh/id_ed25519 user@server.com`

**Web Server Won't Start**:
- Check if port is already in use: `lsof -i :8000`
- Try different port: `uv run ssh-remote-control web --port 8080`
- Check firewall: `sudo ufw allow 8000`

### Debugging

Enable debug mode for detailed logging:
```bash
# Environment variable
DEBUG=true uv run ssh-remote-control web

# Or in configuration file
debug: true
log_level: "debug"
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `uv run pytest`
5. Run quality checks: `uv run ruff check && uv run mypy src/ssh_remote_control --strict`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Create a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/jeffdasilva/ssh-remote-control/wiki)
- 🐛 [Issue Tracker](https://github.com/jeffdasilva/ssh-remote-control/issues)
- 💬 [Discussions](https://github.com/jeffdasilva/ssh-remote-control/discussions)

## Origin Prompt

This app was started from the following prompt:


Help me create a python project using uv to manage it. Use python 3.12.
- This should be a production quality product. Not an MVP and not a prototype. The code should be readable, maintainable, and extensible by other developers.
- Update README.md to document how this all works. Add a copilot file to document and provide context for other ai agents.
- The project should: 
    - have a command line user interface built with Typer
    - provide a web dashboard that uses FastAPI and htmx. Use asyncio wherever possible to make it fast.
    - use asynssh to display various system logs in realtime extracted from various remote server that I specify
    - share one ssh connection to do all operations
    - allow the user to run simple commands on the server via asyncssh.
    - Readme.md should include clear simple instructions for setting up ssh authentication files
- all code should be reasonably unittested with pytest. Tests should be structured in a "tests" directory. 
- all code should use strict mypy type hinting. uv ty should also be clean
- all code should be formatted and checked with ruff
- all code should pass a pylint test
- This project will be upstreamed to github. Add github action to run all tests and check when code is pushed
- Don't prompt me for questions or to continue unless you are doing something potentially dangerous


## Changelog

### v0.1.0 (Current)
- Initial release
- Web dashboard with server management
- CLI interface for server operations
- Real-time log monitoring
- SSH connection management
- Comprehensive test suite
- Docker support
- CI/CD pipeline
