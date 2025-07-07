# SSH Remote Control Dashboard - Makefile
# ===========================================
#
# This Makefile provides convenient targets for development tasks.
# By default, 'make' or 'make all' runs all quality checks and tests.
#
# Requirements:
#   - uv (Python package manager)
#   - make

# Variables
PYTHON := uv run python
UV := uv
SRC_DIR := src/ssh_remote_control
TEST_DIR := tests
VENV_DIR := .venv

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.PHONY: all
all: test ## Run tests (default target)
	@echo "$(GREEN)✅ Tests completed successfully!$(NC)"
	@echo "$(YELLOW)💡 Run 'make check' for code quality checks$(NC)"
	@echo "$(YELLOW)💡 Run 'make ci' for full CI pipeline$(NC)"

# Help target
.PHONY: help
help: ## Show this help message
	@echo "SSH Remote Control Dashboard - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make all          # Run essential checks and tests"
	@echo "  make run          # Start web server"
	@echo "  make test         # Run tests only"
	@echo "  make check        # Run basic quality checks"
	@echo "  make format       # Format code"
	@echo "  make ci           # Run full CI pipeline"

# Environment setup
.PHONY: setup
setup: ## Set up development environment
	@echo "$(YELLOW)Setting up development environment...$(NC)"
	$(UV) sync --all-extras --dev
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

# Quality checks
.PHONY: check
check: check-format check-lint ## Run basic quality checks

.PHONY: check-comprehensive
check-comprehensive: check check-types check-security check-pylint ## Run comprehensive quality checks

.PHONY: check-format
check-format: ## Check code formatting with ruff
	@echo "$(YELLOW)Checking code formatting...$(NC)"
	$(UV) run ruff format --check --diff
	@echo "$(GREEN)✅ Code formatting check passed$(NC)"

.PHONY: check-lint
check-lint: ## Check code with ruff linter
	@echo "$(YELLOW)Running ruff linter...$(NC)"
	$(UV) run ruff check src/
	@echo "$(GREEN)✅ Ruff linting passed$(NC)"

.PHONY: check-lint-all
check-lint-all: ## Check all code with ruff linter (including tests)
	@echo "$(YELLOW)Running ruff linter on all code...$(NC)"
	$(UV) run ruff check
	@echo "$(GREEN)✅ Ruff linting passed$(NC)"

.PHONY: check-types
check-types: ## Check types with mypy
	@echo "$(YELLOW)Running mypy type checker...$(NC)"
	$(UV) run mypy src/ tests/ --strict
	@echo "$(GREEN)✅ Type checking passed$(NC)"

.PHONY: check-security
check-security: ## Check security with bandit
	@echo "$(YELLOW)Running bandit security checker...$(NC)"
	$(UV) run bandit -r $(SRC_DIR) -f json -o bandit-report.json || \
	$(UV) run bandit -r $(SRC_DIR) -ll
	@echo "$(GREEN)✅ Security check passed$(NC)"

.PHONY: check-pylint
check-pylint: ## Check code with pylint
	@echo "$(YELLOW)Running pylint...$(NC)"
	$(UV) run pylint $(SRC_DIR)
	@echo "$(GREEN)✅ Pylint check passed$(NC)"

.PHONY: check-all
check-all: check-comprehensive ## Run all quality checks including pylint

# Code formatting
.PHONY: format
format: ## Format code with ruff
	@echo "$(YELLOW)Formatting code...$(NC)"
	$(UV) run ruff format
	$(UV) run ruff check --fix
	@echo "$(GREEN)✅ Code formatted$(NC)"

# Testing
.PHONY: test
test: ## Run tests with pytest
	@echo "$(YELLOW)Running tests...$(NC)"
	$(UV) run pytest
	@echo "$(GREEN)✅ Tests passed$(NC)"

.PHONY: test-verbose
test-verbose: ## Run tests with verbose output
	@echo "$(YELLOW)Running tests with verbose output...$(NC)"
	$(UV) run pytest -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	$(UV) run pytest --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

.PHONY: test-fast
test-fast: ## Run tests in parallel (faster)
	@echo "$(YELLOW)Running tests in parallel...$(NC)"
	$(UV) run pytest -n auto

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(YELLOW)Running tests in watch mode...$(NC)"
	$(UV) run pytest --watch

# Application running
.PHONY: run
run: ## Start the web server with auto-reload (default: localhost:8000)
	@echo "$(YELLOW)Starting SSH Remote Control web server with auto-reload...$(NC)"
	@echo "$(GREEN)🚀 Server will be available at http://localhost:8000$(NC)"
	@echo "$(GREEN)🔄 Auto-reload enabled for development$(NC)"
	$(UV) run ssh-remote-control web --reload

.PHONY: run-prod
run-prod: ## Start web server in production mode (no auto-reload)
	@echo "$(YELLOW)Starting SSH Remote Control web server in production mode...$(NC)"
	@echo "$(GREEN)🚀 Server will be available at http://localhost:8000$(NC)"
	$(UV) run ssh-remote-control web

.PHONY: run-dev
run-dev: ## Start web server in development mode (with auto-reload)
	@echo "$(YELLOW)Starting SSH Remote Control web server in development mode...$(NC)"
	@echo "$(GREEN)🚀 Server will be available at http://localhost:8000$(NC)"
	@echo "$(GREEN)🔄 Auto-reload enabled$(NC)"
	$(UV) run ssh-remote-control web --reload --debug

.PHONY: run-public
run-public: ## Start web server accessible from all interfaces
	@echo "$(YELLOW)Starting SSH Remote Control web server (public access)...$(NC)"
	@echo "$(GREEN)🚀 Server will be available at http://0.0.0.0:8000$(NC)"
	@echo "$(RED)⚠️  WARNING: Server accessible from all network interfaces!$(NC)"
	$(UV) run ssh-remote-control web --host 0.0.0.0

.PHONY: run-custom
run-custom: ## Start web server with custom host and port (use HOST=x.x.x.x PORT=xxxx)
	@echo "$(YELLOW)Starting SSH Remote Control web server...$(NC)"
	@echo "$(GREEN)🚀 Server will be available at http://$(HOST):$(PORT)$(NC)"
	$(UV) run ssh-remote-control web --host $(HOST) --port $(PORT)

.PHONY: run-docker
run-docker: ## Build and run with Docker
	@echo "$(YELLOW)Building Docker image...$(NC)"
	docker build -t ssh-remote-control .
	@echo "$(YELLOW)Running Docker container...$(NC)"
	@echo "$(GREEN)🚀 Server will be available at http://localhost:8000$(NC)"
	docker run -p 8000:8000 ssh-remote-control

# CLI demonstrations
.PHONY: demo-cli
demo-cli: ## Demonstrate CLI functionality
	@echo "$(YELLOW)Demonstrating CLI functionality...$(NC)"
	@echo ""
	@echo "$(GREEN)1. Show version:$(NC)"
	$(UV) run ssh-remote-control --version
	@echo ""
	@echo "$(GREEN)2. Show help:$(NC)"
	$(UV) run ssh-remote-control --help
	@echo ""
	@echo "$(GREEN)3. List configured servers:$(NC)"
	$(UV) run ssh-remote-control list-servers || echo "No servers configured"
	@echo ""
	@echo "$(GREEN)4. Initialize sample config:$(NC)"
	@echo "Would create config at ~/.ssh-remote-control.yaml"
	@echo "Run 'uv run ssh-remote-control init-config' to create it"

.PHONY: demo-commands
demo-commands: ## Show example CLI commands
	@echo "$(YELLOW)SSH Remote Control CLI Commands:$(NC)"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  ssh-remote-control init-config                    # Create sample config"
	@echo "  ssh-remote-control list-servers                   # List configured servers"
	@echo ""
	@echo "$(GREEN)Server Operations:$(NC)"
	@echo "  ssh-remote-control test-connection myserver       # Test SSH connection"
	@echo "  ssh-remote-control execute myserver 'df -h'       # Execute command"
	@echo "  ssh-remote-control execute myserver 'uptime'      # Check uptime"
	@echo ""
	@echo "$(GREEN)Web Server:$(NC)"
	@echo "  ssh-remote-control web                            # Start web server"
	@echo "  ssh-remote-control web --host 0.0.0.0 --port 8080 # Custom host/port"
	@echo "  ssh-remote-control web --reload --debug           # Development mode"

# Configuration
.PHONY: init-config
init-config: ## Initialize sample configuration
	@echo "$(YELLOW)Initializing sample configuration...$(NC)"
	$(UV) run ssh-remote-control init-config
	@echo "$(GREEN)✅ Configuration initialized$(NC)"
	@echo "$(YELLOW)Edit ~/.ssh-remote-control.yaml to add your servers$(NC)"

# Cleanup
.PHONY: clean
clean: ## Clean up build artifacts and cache
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

.PHONY: clean-all
clean-all: clean ## Clean everything including virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf $(VENV_DIR)
	@echo "$(GREEN)✅ Complete cleanup finished$(NC)"

# Development tools
.PHONY: install-pre-commit
install-pre-commit: ## Install pre-commit hooks
	@echo "$(YELLOW)Installing pre-commit hooks...$(NC)"
	$(UV) run pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"

.PHONY: update-deps
update-deps: ## Update dependencies
	@echo "$(YELLOW)Updating dependencies...$(NC)"
	$(UV) sync --upgrade
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

# Build and release
.PHONY: build
build: ## Build the package
	@echo "$(YELLOW)Building package...$(NC)"
	$(UV) build
	@echo "$(GREEN)✅ Package built$(NC)"

.PHONY: check-build
check-build: ## Check if package can be built
	@echo "$(YELLOW)Checking if package can be built...$(NC)"
	$(UV) build --check
	@echo "$(GREEN)✅ Package can be built$(NC)"

# CI/CD simulation
.PHONY: ci
ci: setup check-comprehensive test-coverage ## Simulate CI/CD pipeline
	@echo "$(GREEN)✅ CI/CD pipeline simulation completed successfully!$(NC)"

# Development shortcuts
.PHONY: dev
dev: setup format check test ## Quick development cycle: setup, format, check, test

.PHONY: quick-check
quick-check: check-format check-lint ## Quick checks (no mypy or tests)

# Information
.PHONY: info
info: ## Show project information
	@echo "$(YELLOW)SSH Remote Control Dashboard$(NC)"
	@echo "============================="
	@echo ""
	@echo "$(GREEN)Project Structure:$(NC)"
	@echo "  src/ssh_remote_control/    # Source code"
	@echo "  tests/                     # Test files"
	@echo "  templates/                 # HTML templates"
	@echo "  static/                    # Static files"
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  ~/.ssh-remote-control.yaml # Main config file"
	@echo "  .env                       # Environment variables"
	@echo ""
	@echo "$(GREEN)Key Features:$(NC)"
	@echo "  • Web dashboard for server management"
	@echo "  • CLI interface for server operations"
	@echo "  • Real-time log monitoring"
	@echo "  • SSH connection management"
	@echo "  • WebSocket support for real-time updates"

# Check if uv is available
.PHONY: check-uv
check-uv: ## Check if uv is installed
	@which uv > /dev/null || (echo "$(RED)Error: uv is not installed. Please install it first:$(NC)" && \
	echo "$(YELLOW)curl -LsSf https://astral.sh/uv/install.sh | sh$(NC)" && exit 1)
	@echo "$(GREEN)✅ uv is available$(NC)"

# Ensure uv is available for all targets
setup check check-format check-lint check-types check-security check-pylint check-all: | check-uv
format test test-verbose test-coverage test-fast test-watch: | check-uv
run run-dev run-public run-custom demo-cli init-config: | check-uv
build check-build update-deps install-pre-commit: | check-uv
