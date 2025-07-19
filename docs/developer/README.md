# Developer Guide

Welcome to the GitHub CLI developer documentation! This guide provides comprehensive information for developers who want to contribute to, extend, or understand the GitHub CLI codebase.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**: Modern Python with latest features
- **Git**: Version control
- **GitHub Account**: For testing and contributions
- **Terminal**: Command-line interface

### Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/github-cli.git
   cd github-cli
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Install in development mode
   pip install -e .
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Alternative using uv (faster)
   uv pip install -e .
   ```

4. **Verify Installation**
   ```bash
   github-cli --version
   python -m github_cli --help
   ```

## 🏗️ Architecture Overview

### Project Structure

```
github-cli/
├── github_cli/              # Main package
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # CLI entry point
│   ├── api/                # GitHub API client
│   ├── auth/               # Authentication system
│   ├── tui/                # Terminal User Interface
│   ├── ui/                 # Legacy Rich-based UI
│   ├── models/             # Data models
│   ├── utils/              # Utility modules
│   └── git/                # Git integration
├── docs/                   # Documentation
├── tests/                  # Test suite
├── examples/               # Usage examples
├── logs/                   # Application logs
├── pyproject.toml          # Project configuration
├── README.md               # Project overview
└── CLAUDE.md               # AI assistant guidance
```

### Core Components

#### 1. API Client (`github_cli/api/`)
- **Purpose**: GitHub REST API communication
- **Key Files**: `client.py`, `repositories.py`, `pull_requests.py`, `actions.py`
- **Features**: Rate limiting, error handling, pagination, caching

#### 2. Authentication (`github_cli/auth/`)
- **Purpose**: OAuth device flow authentication
- **Key Files**: `authenticator.py`, `token_manager.py`, `sso_handler.py`
- **Features**: Secure token storage, SSO support, adaptive UI

#### 3. TUI System (`github_cli/tui/`)
- **Purpose**: Modern terminal user interface
- **Key Files**: `app.py`, `responsive.py`, `adaptive_widgets.py`
- **Features**: Responsive design, keyboard shortcuts, accessibility

#### 4. Data Models (`github_cli/models/`)
- **Purpose**: Structured data representations
- **Key Files**: `repository.py`, `user.py`, `pull_request.py`, `workflow.py`
- **Features**: Type safety, validation, serialization

#### 5. Utilities (`github_cli/utils/`)
- **Purpose**: Common functionality and helpers
- **Key Files**: `config.py`, `exceptions.py`, `performance.py`
- **Features**: Configuration management, error handling, caching

## 🔧 Development Workflow

### Code Style and Standards

#### Python Standards
- **Python Version**: 3.11+ with modern features
- **Type Hints**: Full type annotations required
- **Docstrings**: Google-style docstrings
- **Formatting**: Black code formatter
- **Linting**: Ruff for fast linting
- **Import Sorting**: isort

#### Code Quality Tools

```bash
# Format code
black github_cli/

# Lint code
ruff check github_cli/

# Sort imports
isort github_cli/

# Type checking
mypy github_cli/

# Run all checks
pre-commit run --all-files
```

#### Modern Python Features

```python
# Use modern type annotations
from __future__ import annotations

# Dataclasses with slots and frozen
@dataclass(frozen=True, slots=True)
class Config:
    api_url: str
    timeout: int = 30

# Pattern matching (Python 3.10+)
match response.status_code:
    case 200:
        return response.data
    case 404:
        raise NotFoundError()
    case _:
        raise APIError()

# Union types with |
def process_data(data: str | dict[str, Any]) -> None:
    ...
```

### Testing Strategy

#### Test Structure
```
tests/
├── unit/                   # Unit tests
│   ├── test_api/          # API client tests
│   ├── test_auth/         # Authentication tests
│   ├── test_models/       # Model tests
│   └── test_utils/        # Utility tests
├── integration/           # Integration tests
├── tui/                   # TUI tests
└── conftest.py           # Pytest configuration
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=github_cli --cov-report=html

# Run specific test file
pytest tests/unit/test_api/test_client.py

# Run tests with specific marker
pytest -m "not integration"

# Run TUI tests
pytest tests/tui/
```

#### Test Categories

```python
import pytest

# Unit tests (fast, isolated)
@pytest.mark.unit
def test_repository_model():
    """Test repository model creation."""
    pass

# Integration tests (slower, external dependencies)
@pytest.mark.integration
async def test_github_api_integration():
    """Test actual GitHub API calls."""
    pass

# TUI tests (UI testing)
@pytest.mark.tui
async def test_tui_navigation():
    """Test TUI navigation and interaction."""
    pass
```

### Debugging

#### Logging Configuration

```python
from loguru import logger

# Configure structured logging
logger.configure(
    handlers=[
        {
            "sink": "logs/github_cli.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            "rotation": "10 MB",
            "retention": "1 week",
            "level": "DEBUG"
        }
    ]
)

# Use in code
logger.info("Starting authentication flow")
logger.debug(f"API response: {response.data}")
logger.error(f"Authentication failed: {error}")
```

#### Debug Mode

```bash
# Enable debug logging
export GITHUB_CLI_DEBUG=1
github-cli repo list

# Enable verbose output
github-cli --verbose repo list

# Debug TUI
textual run --dev github_cli.tui.app:GitHubTUIApp
```

## 🧪 Testing Guidelines

### Unit Testing

```python
import pytest
from unittest.mock import Mock, AsyncMock
from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator

@pytest.fixture
def mock_authenticator():
    """Create mock authenticator for testing."""
    auth = Mock(spec=Authenticator)
    auth.token = "test_token"
    auth.is_authenticated.return_value = True
    return auth

@pytest.fixture
async def github_client(mock_authenticator):
    """Create GitHub client for testing."""
    client = GitHubClient(mock_authenticator)
    yield client
    await client.close()

async def test_get_user(github_client, aioresponses):
    """Test getting user information."""
    # Mock API response
    aioresponses.get(
        "https://api.github.com/user",
        payload={"login": "testuser", "id": 123}
    )
    
    # Test API call
    response = await github_client.get("/user")
    
    assert response.data["login"] == "testuser"
    assert response.status_code == 200
```

### Integration Testing

```python
@pytest.mark.integration
async def test_repository_api_integration():
    """Test repository API with real GitHub API."""
    # This test requires authentication
    config = Config()
    authenticator = Authenticator(config)
    
    if not authenticator.is_authenticated():
        pytest.skip("Authentication required for integration tests")
    
    async with GitHubClient(authenticator) as client:
        repo_api = RepositoryAPI(client)
        repos = await repo_api.list_user_repos()
        
        assert isinstance(repos, list)
        if repos:
            assert hasattr(repos[0], 'name')
            assert hasattr(repos[0], 'full_name')
```

### TUI Testing

```python
from textual.testing import TUITestCase
from github_cli.ui.tui.app import GitHubTUIApp

class TestGitHubTUI(TUITestCase):
    """Test GitHub TUI application."""
    
    async def test_app_startup(self):
        """Test TUI application startup."""
        app = GitHubTUIApp()
        
        async with app.run_test() as pilot:
            # Check initial state
            assert app.title == "GitHub CLI - Terminal User Interface"
            
            # Test navigation
            await pilot.press("tab")
            await pilot.press("enter")
            
            # Verify UI elements
            assert pilot.app.query_one("#main-container")
```

## 🔌 Extension Points

### Custom API Modules

```python
# Create custom API module
from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError

class CustomAPI:
    """Custom API functionality."""
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    async def custom_operation(self, param: str) -> dict:
        """Implement custom GitHub API operation."""
        try:
            response = await self.client.get(f"/custom/{param}")
            return response.data
        except Exception as e:
            raise GitHubCLIError(f"Custom operation failed: {e}")
```

### Custom TUI Widgets

```python
from textual.widget import Widget
from textual.app import ComposeResult
from github_cli.ui.tui.adaptive_widgets import AdaptiveWidget

class CustomWidget(Widget, AdaptiveWidget):
    """Custom TUI widget with responsive design."""
    
    def __init__(self, layout_manager):
        super().__init__()
        self.layout_manager = layout_manager
    
    def compose(self) -> ComposeResult:
        """Compose widget content."""
        yield Label("Custom Widget")
    
    def adapt_to_layout(self, layout_config: dict) -> None:
        """Adapt to layout changes."""
        if layout_config.get('compact_mode'):
            self.add_class('compact')
        else:
            self.remove_class('compact')
```

### Plugin System

```python
# Plugin interface
from abc import ABC, abstractmethod

class GitHubCLIPlugin(ABC):
    """Base class for GitHub CLI plugins."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name."""
        pass
    
    @abstractmethod
    def get_commands(self) -> dict:
        """Get plugin commands."""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, args: dict) -> None:
        """Execute plugin command."""
        pass

# Example plugin
class ExamplePlugin(GitHubCLIPlugin):
    """Example plugin implementation."""
    
    def get_name(self) -> str:
        return "example"
    
    def get_commands(self) -> dict:
        return {
            "hello": "Say hello",
            "info": "Show plugin info"
        }
    
    async def execute_command(self, command: str, args: dict) -> None:
        if command == "hello":
            print("Hello from example plugin!")
        elif command == "info":
            print("Example plugin v1.0")
```

## 📦 Building and Distribution

### Building the Package

```bash
# Build wheel and source distribution
python -m build

# Build with uv (faster)
uv build

# Check distribution
twine check dist/*
```

### Release Process

1. **Update Version**
   ```python
   # In github_cli/__init__.py
   __version__ = "0.2.0"
   ```

2. **Update Changelog**
   ```markdown
   ## [0.2.0] - 2024-01-15
   ### Added
   - New TUI interface
   - Responsive design
   ### Fixed
   - Authentication issues
   ```

3. **Create Release**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **Publish to PyPI**
   ```bash
   twine upload dist/*
   ```

## 🤝 Contributing

### Contribution Workflow

1. **Fork the Repository**
2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Run Tests**
   ```bash
   pytest
   pre-commit run --all-files
   ```

5. **Submit Pull Request**
   - Clear description of changes
   - Link to related issues
   - Include screenshots for UI changes

### Code Review Guidelines

- **Functionality**: Does the code work as intended?
- **Testing**: Are there adequate tests?
- **Documentation**: Is the code well-documented?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?

## 📚 Resources

### Documentation
- [API Documentation](../api/README.md)
- [TUI Documentation](../tui/README.md)
- [Authentication Guide](../auth/README.md)
- [Models Documentation](../models/README.md)

### External Resources
- [GitHub REST API](https://docs.github.com/en/rest)
- [Textual Documentation](https://textual.textualize.io/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Community
- [GitHub Discussions](https://github.com/yourusername/github-cli/discussions)
- [Issue Tracker](https://github.com/yourusername/github-cli/issues)
- [Contributing Guidelines](contributing.md)

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Reinstall in development mode
   pip install -e .
   ```

2. **Authentication Issues**
   ```bash
   # Clear stored tokens
   rm -rf ~/.config/github-cli/tokens/
   ```

3. **TUI Issues**
   ```bash
   # Run with debug mode
   textual run --dev github_cli.tui.app:GitHubTUIApp
   ```

### Getting Help

- Check the [FAQ](faq.md)
- Search [existing issues](https://github.com/yourusername/github-cli/issues)
- Join [discussions](https://github.com/yourusername/github-cli/discussions)
- Contact maintainers
