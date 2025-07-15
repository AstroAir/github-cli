# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup

```bash
# Install in development mode (preferred method)
pip install -e .

# Alternative using uv (faster package manager)
uv pip install -e .

# Run the CLI directly
python -m github_cli

# Run with main.py entry point
python main.py

# Use the installed command
github-cli
```

### TUI Development

The project features an advanced Textual-based TUI with comprehensive responsive design:

```bash
# Run the TUI application
python -m github_cli tui

# Run with CSS hot-reload for development (when textual-dev is installed)
textual run --dev github_cli.tui.app:GitHubTUIApp

# View Textual console for debugging
textual console
```

**TUI Adaptability Features:**
- **Responsive Breakpoints**: 5 size breakpoints (xs, sm, md, lg, xl) with automatic layout adaptation
- **Adaptive Widgets**: Custom widgets that adjust content, columns, and visibility based on terminal size
- **Dynamic Column Management**: DataTables automatically hide/show columns based on available space
- **Intelligent Layout Switching**: Automatic horizontal/vertical layout selection based on terminal dimensions
- **Graceful Degradation**: Content prioritization ensures essential information remains visible in small terminals

### Running Tests

No formal test suite is currently configured. If implementing tests:

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=github_cli
```

### Linting and Formatting

```bash
# Format and lint code
ruff format github_cli/
ruff check github_cli/
ruff check --fix github_cli/

# Type checking
mypy github_cli/
```

## Architecture Overview

This is a terminal-based GitHub CLI client built with Python 3.11+ using modern async/await patterns and performance optimizations. The application provides comprehensive GitHub API access through a rich terminal interface.

### Core Architecture

**Entry Points:**

- `main.py`: Simple async entry point that calls `github_cli.__main__:main()`
- `github_cli/__main__.py`: Main CLI implementation with full argument parsing and command dispatch
- `pyproject.toml`: Defines console script entry point `github-cli = "github_cli.__main__:main_entrypoint"`

**Key Components:**

1. **TUI System** (`github_cli/tui/`)
   - `app.py`: Main Textual application with responsive design and status management
   - `repositories.py`, `pull_requests.py`, `actions.py`, `notifications.py`: Feature-specific TUI screens
   - `responsive.py`: Responsive layout management for different terminal sizes
   - `adaptive_widgets.py`: Widgets that adapt to terminal constraints
   - `github_tui.tcss`: CSS styling for TUI components

2. **Authentication System** (`github_cli/auth/`)
   - `authenticator.py`: OAuth device flow authentication with GitHub
   - `token_manager.py`: Token storage and management
   - `sso_handler.py`: Single sign-on support

3. **API Client** (`github_cli/api/`)
   - `client.py`: Core GitHub API client with rate limiting and pagination
   - Modular API handlers for different GitHub services (repositories, pull requests, actions, etc.)
   - Supports both individual and paginated requests

4. **User Interface** (`github_cli/ui/`)
   - `terminal.py`: Terminal UI components using Rich library
   - `dashboard.py`: Interactive dashboard interface
   - `diff_viewer.py`: Diff viewing capabilities

5. **Data Models** (`github_cli/models/`)
   - Structured data classes for GitHub entities (repositories, issues, PRs, etc.)

6. **Utilities** (`github_cli/utils/`)
   - `config.py`: Configuration management
   - `cache.py`: Caching mechanisms
   - `plugins.py`: Plugin system
   - `shortcuts.py`: Keyboard shortcuts
   - `exceptions.py`: Custom exception handling
   - `performance.py`: Performance monitoring utilities

### Authentication Flow

The application uses an enhanced GitHub OAuth device flow with improved usability:

1. **Device Code Request**: Automatic generation of user verification code
2. **Smart Browser Opening**: Multi-platform browser launching with fallback methods:
   - Primary: Python `webbrowser` module
   - Windows fallback: `cmd /c start` command
   - macOS fallback: `open` command  
   - Linux fallback: `xdg-open` command
3. **Clipboard Integration**: Automatic URL copying to clipboard if browser opening fails
4. **User-Friendly Display**: Clear instructions with emojis and formatting
5. **Enhanced Polling**: Intelligent token polling with configurable intervals and timeouts
6. **Comprehensive Error Handling**: Detailed error messages and graceful failure recovery
7. **Token Storage**: Secure token management using keyring

### Command Structure

Commands are organized into categories:

- `auth`: Authentication management
- `repo`: Repository operations
- `pr`: Pull request management
- `actions`: GitHub Actions workflows
- `tui`: Launch full-featured Terminal User Interface
- `dashboard`: Interactive terminal dashboard (legacy Rich-based)
- Additional commands for gists, releases, search, notifications, etc.

### TUI Architecture

The TUI system (`github_cli/tui/`) is built with Textual and features advanced adaptability:

**Responsive Design System:**
- **ResponsiveLayoutManager**: Central system managing 5 breakpoints (xs: 0+, sm: 60+, md: 80+, lg: 120+, xl: 160+ width)
- **Dynamic Layout Adaptation**: Automatic sidebar visibility, tab orientation, and content sizing
- **Adaptive Widgets**: Base classes for widgets that respond to terminal size changes
- **Smart Content Prioritization**: High-priority content remains visible while low-priority content hides gracefully

**Advanced Widget Components:**
- **AdaptiveContainer**: Containers that reorganize content based on available space
- **AdaptiveDataTable**: Tables with intelligent column hiding/showing and width adjustment
- **AdaptiveInfoPanel**: Information panels that switch between full and compact display modes
- **Responsive Widget Factory**: Centralized creation of adaptive UI components

**CSS Styling System:**
- **Dynamic CSS Generation**: Responsive styles generated programmatically based on current breakpoint
- **Compact Mode Support**: Special styling for constrained terminal environments
- **Theme Integration**: CSS-based theming via `github_tui.tcss`

**Performance Features:**
- **Real-time Updates**: Status bar with connection status, rate limits, and user information
- **Efficient Redraws**: Minimal UI updates during resize events
- **Memory Optimization**: Proper cleanup of layout callbacks and resources

### Dependencies

Core dependencies:

- `aiohttp>=3.9.0`: Async HTTP client for GitHub API
- `rich>=13.7.0`: Terminal UI and formatting  
- `questionary>=2.0.0`: Interactive prompts
- `keyring>=24.0.0`: Secure token storage
- `python-dateutil>=2.8.0`: Date/time handling
- `loguru>=0.7.0`: Advanced structured logging
- `pydantic>=2.5.0`: Data validation and parsing
- `httpx>=0.25.0`: Alternative HTTP client with HTTP/2 support
- `textual>=0.41.0`: Modern TUI framework for rich terminal interfaces
- `textual-dev>=1.2.0`: Development tools for Textual applications
- `rich-argparse>=1.7.1`: Rich formatting for argument parsing
- `pyperclip>=1.9.0`: Clipboard operations

### Development Notes

- Uses modern Python 3.11+ patterns with type hints, slots, and async/await
- Dual entry points: `main.py` (simple) and `github_cli/__main__.py` (full CLI)
- API client includes built-in rate limiting awareness and retry logic
- Configuration and caching systems designed for extensibility
- Plugin architecture allows for additional functionality
- Comprehensive structured logging with loguru (logs stored in `logs/` directory)
- Enhanced exception handling with contextual information
- Performance monitoring and caching utilities for optimization

**TUI Framework Enhancements:**
- **Advanced Responsive Design**: 5-tier breakpoint system with intelligent layout adaptation
- **Cross-Platform OAuth**: Enhanced authentication with multi-platform browser support and clipboard fallbacks
- **Adaptive Component System**: Widgets that automatically adjust content visibility and layout based on constraints
- **Dynamic Resource Management**: Efficient memory usage with proper cleanup of layout callbacks
- **Real-Time Performance Monitoring**: Built-in status tracking and performance optimization
- **CSS-Based Theming**: Flexible styling system supporting multiple themes and responsive design
