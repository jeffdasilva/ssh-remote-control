# VS Code Configuration for SSH Remote Control

This directory contains VS Code workspace configuration files that optimize the development experience for the SSH Remote Control project.

## Files Overview

### `settings.json`
- **Python Environment**: Configured to use the project's virtual environment (`.venv`)
- **Linting & Formatting**: Integrated with ruff, mypy, and pylint
- **Test Discovery**: Automatic pytest test discovery and execution
- **Code Actions**: Auto-format and organize imports on save
- **GitHub Copilot**: Optimized settings with reduced follow-ups in agent mode
- **File Exclusions**: Hides cache directories and build artifacts

### `launch.json`
- **Run Tests**: Ctrl+F5 to run all tests
- **Debug Tests**: Shift+Ctrl+F5 to debug tests with breakpoints
- **Run CLI**: Launch the CLI application
- **Run Web Server**: Start the web server for testing
- **Debug Current File**: Debug the currently open Python file

### `tasks.json`
- **Test Tasks**: Run tests with and without coverage
- **Code Quality**: Check types, lint, and pylint
- **Format Code**: Auto-format all code
- **CI Pipeline**: Run the complete CI/CD pipeline
- **Setup**: Initialize development environment

### `keybindings.json`
Smart context-aware keybindings:
- **Ctrl+F5**: 
  - In test files (`test_*.py`): Run current test file
  - In other files: Run all tests
- **Shift+Ctrl+F5**: 
  - In test files: Debug current test file
  - In other files: Debug all tests
- **F5**: Standard debug launch
- **Ctrl+Shift+T**: Run test task
- **Ctrl+Shift+C**: Run CI task

### `extensions.json`
Recommends essential extensions:
- **Python**: Core Python support
- **Pylance**: Enhanced language server
- **Ruff**: Fast Python linter/formatter
- **MyPy**: Type checking
- **GitHub Copilot**: AI code assistance
- **YAML/TOML**: Configuration file support
- **Makefile Tools**: Makefile support

### `python.json`
Code snippets for common patterns:
- Async function templates
- Test function templates  
- Exception handling patterns
- Type annotation imports
- Pydantic model templates

## Quick Start

1. **Open Workspace**: Use `File > Open Workspace` and select `ssh-remote-control.code-workspace`

2. **Install Extensions**: VS Code will prompt to install recommended extensions

3. **Run Tests**: 
   - **In a test file**: Press `Ctrl+F5` to run the current test file
   - **In any other file**: Press `Ctrl+F5` to run all tests
   - **Debug tests**: Press `Shift+Ctrl+F5` to debug with breakpoints

4. **Run Tasks**: Use `Ctrl+Shift+P` → "Tasks: Run Task" for Makefile targets

## Key Features

### Smart Test Running
- **Context-aware**: `Ctrl+F5` automatically detects if you're in a test file
- **Current file**: When in `test_*.py`, runs only that test file
- **All tests**: When in other files, runs the entire test suite
- **Debugging**: `Shift+Ctrl+F5` enables breakpoints and debugging
- **Coverage**: Use tasks for coverage reports

### Test Integration
- **Automatic Discovery**: Tests are automatically discovered in the `tests/` directory
- **Module-based Execution**: Uses `python -m pytest` for proper module resolution
- **Environment Setup**: Automatically sets `PYTHONPATH` to include `src/`
- **Coverage Reports**: Generate coverage reports in `htmlcov/`

### Code Quality
- **Real-time Linting**: Errors and warnings appear as you type
- **Auto-formatting**: Code is formatted on save using ruff
- **Type Checking**: MyPy integration for static type checking
- **Import Organization**: Automatic import sorting and organization

### GitHub Copilot Optimization
- **Reduced Interruptions**: `followUps` disabled for smoother agent mode
- **Enhanced Completions**: Optimized for Python development
- **Context-aware**: Configured for the project's coding patterns

### Development Workflow
- **Makefile Integration**: All Makefile targets available as tasks
- **Environment Management**: Automatic virtual environment activation
- **Git Integration**: Enhanced git support with auto-fetch
- **Problem Detection**: Issues highlighted in the Problems panel

## Usage Tips

1. **Running Tests**: 
   - Use `Ctrl+F5` for quick test runs
   - Use `Shift+Ctrl+F5` for debugging with breakpoints
   - Use the Test Explorer in the sidebar for selective test running

2. **Code Quality**:
   - Problems appear in the Problems panel (View → Problems)
   - Use `Ctrl+Shift+P` → "Format Document" for manual formatting
   - Use `Ctrl+Shift+P` → "Python: Select Interpreter" if needed

3. **Tasks**:
   - Use `Ctrl+Shift+P` → "Tasks: Run Task" to access all Makefile targets
   - Use `Ctrl+Shift+C` for quick CI pipeline runs

4. **Debugging**:
   - Set breakpoints by clicking in the gutter
   - Use the Debug Console for interactive debugging
   - Variables are automatically watched in the Debug sidebar

## Troubleshooting

### Python Interpreter Issues
If VS Code doesn't detect the virtual environment:
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Select `./.venv/bin/python`

### Extension Installation
If extensions don't install automatically:
1. Open the Extensions sidebar (`Ctrl+Shift+X`)
2. Search for and install the recommended extensions manually

### Test Discovery Issues
If tests aren't discovered:
1. Check that pytest is installed: `make setup-dev`
2. Verify the Python interpreter is set correctly
3. Reload VS Code (`Ctrl+Shift+P` → "Developer: Reload Window")

## Customization

Feel free to modify these settings for your preferences:
- **Keybindings**: Edit `keybindings.json` for custom shortcuts
- **Settings**: Modify `settings.json` for editor preferences
- **Tasks**: Add custom tasks in `tasks.json`
- **Snippets**: Add project-specific snippets in `python.json`
