# Project Structure

## Root Directory Layout

```
github-cli/
├── .git/                   # Git repository
├── .kiro/                  # Kiro IDE configuration
├── .venv/                  # Virtual environment
├── github_cli/             # Main package directory
├── logs/                   # Application logs
├── __pycache__/            # Python bytecode cache
├── .gitignore             # Git ignore rules
├── .python-version        # Python version (3.11)
├── CLAUDE.md              # Development guidance
├── README.md              # Project documentation
├── main.py                # Simple entry point
├── github_cli.py          # Alternative entry point
├── pyproject.toml         # Project configuration
├── setup.py               # Legacy setup script
├── uv.lock                # UV lock file
└── run.bat                # Windows batch script
```

## Package Structure (github_cli/)

```
github_cli/
├── __init__.py            # Package initialization and exports
├── __main__.py            # Main CLI entry point with full argument parsing
├── api/                   # GitHub API client modules
│   ├── client.py          # Core API client with rate limiting
│   ├── repositories.py    # Repository API operations
│   ├── pull_requests.py   # Pull request API operations
│   └── actions.py         # GitHub Actions API
├── auth/                  # Authentication system
│   ├── authenticator.py   # OAuth device flow authentication
│   ├── token_manager.py   # Token storage and management
│   └── sso_handler.py     # Single sign-on support
├── models/                # Data models and schemas
│   ├── repository.py      # Repository data models
│   └── ...               # Other GitHub entity models
├── tui/                   # Terminal User Interface (Textual-based)
│   ├── app.py            # Main TUI application
│   ├── repositories.py    # Repository management screen
│   ├── pull_requests.py   # Pull request screen
│   ├── actions.py         # GitHub Actions screen
│   ├── responsive.py      # Responsive layout management
│   ├── adaptive_widgets.py # Adaptive UI components
│   └── github_tui.tcss    # CSS styling
├── ui/                    # Terminal UI components (Rich-based)
│   ├── terminal.py        # Terminal UI utilities
│   ├── dashboard.py       # Interactive dashboard
│   └── diff_viewer.py     # Diff viewing capabilities
├── git/                   # Git integration
├── utils/                 # Utility modules
│   ├── config.py          # Configuration management
│   ├── cache.py           # Caching mechanisms
│   ├── exceptions.py      # Custom exceptions
│   ├── performance.py     # Performance monitoring
│   ├── plugins.py         # Plugin system
│   └── shortcuts.py       # Keyboard shortcuts
└── __pycache__/           # Python bytecode cache
```

## Entry Points

- **Primary**: `github_cli/__main__.py` - Full CLI with argument parsing
- **Simple**: `main.py` and `github_cli.py` - Minimal async entry points
- **Console Script**: `github-cli` command (defined in pyproject.toml)

## Key Architectural Patterns

- **Modular Design**: Clear separation between API, UI, Auth, and Models
- **Dual UI System**: Both Rich-based terminal UI and Textual-based TUI
- **Async Architecture**: All I/O operations use async/await patterns
- **Plugin System**: Extensible architecture in utils/plugins.py
- **Responsive TUI**: Advanced breakpoint system for terminal size adaptation

## Configuration Files

- `pyproject.toml`: Modern Python project configuration
- `setup.py`: Legacy setuptools configuration (backup)
- `.python-version`: Python version specification for pyenv
- `uv.lock`: UV package manager lock file

## Logging

- Application logs stored in `logs/` directory
- Structured logging with loguru
- Separate log files for different components (auth.log, github_cli.log)