# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup

```bash
# Install in development mode
pip install -e .

# Or using uv
uv pip install -e .

# Run the CLI directly
python -m github_cli

# Or use the installed command
github-cli
```

### Running Tests

This project does not appear to have a formal test suite configured. To add testing:

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests (when implemented)
pytest tests/ -v --cov=github_cli

# Run with performance monitoring
pytest tests/ -v --tb=short
```

### Linting and Formatting

The project now uses modern Python 3.11+ features. Recommended tools:

```bash
# Install development tools
pip install ruff black mypy

# Format code
black github_cli/
ruff format github_cli/

# Lint code  
ruff check github_cli/
mypy github_cli/

# Auto-fix issues
ruff check --fix github_cli/
```

## Architecture Overview

This is a terminal-based GitHub CLI client built with Python 3.11+ using modern async/await patterns and performance optimizations. The application provides comprehensive GitHub API access through a rich terminal interface.

### Core Architecture

**Entry Points:**

- `main.py`: Primary CLI entry with comprehensive argument parsing
- `github_cli/__main__.py`: Package entry point (simpler version)
- Both files implement similar command structures but with different complexity levels

**Key Components:**

1. **Authentication System** (`github_cli/auth/`)
   - `authenticator.py`: OAuth device flow authentication with GitHub
   - `token_manager.py`: Token storage and management
   - `sso_handler.py`: Single sign-on support

2. **API Client** (`github_cli/api/`)
   - `client.py`: Core GitHub API client with rate limiting and pagination
   - Modular API handlers for different GitHub services (repositories, pull requests, actions, etc.)
   - Supports both individual and paginated requests

3. **User Interface** (`github_cli/ui/`)
   - `terminal.py`: Terminal UI components using Rich library
   - `dashboard.py`: Interactive dashboard interface
   - `diff_viewer.py`: Diff viewing capabilities

4. **Data Models** (`github_cli/models/`)
   - Structured data classes for GitHub entities (repositories, issues, PRs, etc.)

5. **Utilities** (`github_cli/utils/`)
   - `config.py`: Configuration management
   - `cache.py`: Caching mechanisms
   - `plugins.py`: Plugin system
   - `shortcuts.py`: Keyboard shortcuts
   - `exceptions.py`: Custom exception handling

### Authentication Flow

The application uses GitHub's OAuth device flow:

1. Request device code from GitHub
2. Display user code and verification URL
3. Poll for token until user completes authorization
4. Store token securely using keyring

### Command Structure

Commands are organized into categories:

- `auth`: Authentication management
- `repo`: Repository operations
- `pr`: Pull request management
- `actions`: GitHub Actions workflows
- `dashboard`: Interactive terminal dashboard
- Additional commands for gists, releases, search, notifications, etc.

### Dependencies

Core dependencies:

- `aiohttp>=3.9.0`: Async HTTP client for GitHub API
- `rich>=13.7.0`: Terminal UI and formatting  
- `questionary>=2.0.0`: Interactive prompts
- `keyring>=24.0.0`: Secure token storage
- `python-dateutil>=2.8.0`: Date/time handling
- `loguru>=0.7.0`: Advanced structured logging
- `pydantic>=2.5.0`: Data validation and parsing
- `httpx>=0.25.0`: Alternative HTTP client with HTTP/2 support\n- `textual>=0.41.0`: Modern TUI framework for rich terminal interfaces\n- `textual-dev>=1.2.0`: Development tools for Textual applications

### Development Notes

- The codebase uses modern Python 3.11+ patterns with type hints, slots, and async/await
- Leverages Python 3.12 performance optimizations including eager task execution
- Two different main entry points exist with varying feature completeness  
- API client includes built-in rate limiting awareness and retry logic
- Configuration and caching systems are designed for extensibility
- Plugin architecture allows for additional functionality
- Comprehensive structured logging with loguru for debugging and monitoring
- Enhanced exception handling with contextual information
- Performance monitoring and caching utilities for optimization\n- **TUI Support**: Full-featured Terminal User Interface with Textual framework\n- Interactive dashboards for repositories, pull requests, Actions, and notifications\n- Real-time status monitoring and keyboard shortcuts for efficient navigation
