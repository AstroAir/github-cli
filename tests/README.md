# GitHub CLI Test Suite

This directory contains comprehensive unit and integration tests for the GitHub CLI project.

## 📁 Test Structure

```
tests/
├── README.md                 # This file
├── conftest.py              # Pytest configuration and shared fixtures
├── auth/                    # Authentication-specific tests (legacy)
├── integration/             # Integration tests
│   └── test_git_integration.py
└── unit/                    # Unit tests organized by module
    ├── api/                 # API client tests
    │   ├── __init__.py
    │   └── test_client.py
    ├── auth/                # Authentication system tests
    │   ├── __init__.py
    │   ├── test_authenticator.py
    │   └── test_token_manager.py
    ├── git/                 # Git integration tests
    │   ├── __init__.py
    │   ├── test_commands.py
    │   ├── test_edge_cases.py
    │   └── test_terminal_methods.py
    ├── models/              # Data model tests
    │   ├── __init__.py
    │   ├── test_repository.py
    │   └── test_user.py
    ├── tui/                 # TUI component tests
    │   ├── __init__.py
    │   └── test_auth_screen.py
    ├── ui/                  # UI component tests
    │   ├── __init__.py
    │   └── test_terminal.py
    └── utils/               # Utility tests
        ├── __init__.py
        └── test_config.py
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests that test individual components without external dependencies.

- **API Tests** (`api/`): Test GitHub API client functionality
- **Auth Tests** (`auth/`): Test authentication and token management
- **Model Tests** (`models/`): Test data models and validation
- **UI Tests** (`ui/`, `tui/`): Test user interface components
- **Utils Tests** (`utils/`): Test utility functions and configuration

### Integration Tests (`tests/integration/`)

Slower tests that test component interactions and may require external dependencies.

- **Git Integration**: Tests requiring actual git installation
- **API Integration**: Tests that may make real API calls (when configured)

## 🚀 Running Tests

### Quick Start

```bash
# Run all unit tests (fast)
python run_tests.py fast

# Run all tests with coverage
python run_tests.py all --coverage

# Run specific test category
python run_tests.py api --verbose
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/ -m unit

# Run with coverage
pytest --cov=github_cli --cov-report=html

# Run specific test file
pytest tests/unit/api/test_client.py -v

# Run tests matching pattern
pytest -k "test_auth" -v
```

### Test Runner Script

The `run_tests.py` script provides convenient commands:

```bash
# Available commands
python run_tests.py unit        # Unit tests only
python run_tests.py integration # Integration tests only
python run_tests.py api         # API tests only
python run_tests.py auth        # Authentication tests only
python run_tests.py ui          # UI tests only
python run_tests.py models      # Model tests only
python run_tests.py utils       # Utility tests only
python run_tests.py all         # All tests
python run_tests.py fast        # Fast tests only (no integration)
python run_tests.py coverage    # Generate coverage report

# Options
--verbose    # Verbose output
--coverage   # Generate coverage report
--lint       # Run code linting
```

## 📊 Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (slower, external deps)
- `@pytest.mark.api`: API client tests
- `@pytest.mark.auth`: Authentication tests
- `@pytest.mark.ui`: UI component tests
- `@pytest.mark.tui`: TUI component tests
- `@pytest.mark.models`: Data model tests
- `@pytest.mark.git`: Tests requiring git installation
- `@pytest.mark.slow`: Slow tests

### Running by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Exclude slow tests
pytest -m "not slow"

# Combine markers
pytest -m "unit and api"
```

## 🔧 Test Configuration

### pytest.ini

The `pytest.ini` file configures:
- Test discovery patterns
- Coverage settings
- Marker definitions
- Warning filters
- Async test mode

### conftest.py

Shared fixtures and configuration:
- Mock objects for common components
- Sample data fixtures
- Test utilities
- Pytest configuration

## 📝 Writing Tests

### Test Structure

```python
"""
Unit tests for [Component Name].

Brief description of what this test module covers.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from github_cli.module import ComponentClass


@pytest.mark.unit
@pytest.mark.category  # e.g., api, auth, ui
class TestComponentClass:
    """Test cases for ComponentClass."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_dependency = Mock()
        self.component = ComponentClass(self.mock_dependency)

    def test_method_success(self):
        """Test successful method execution."""
        # Arrange
        expected_result = "success"
        
        # Act
        result = self.component.method()
        
        # Assert
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async method."""
        result = await self.component.async_method()
        assert result is not None
```

### Best Practices

1. **Use descriptive test names**: `test_method_with_valid_input_returns_expected_result`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: Use `unittest.mock` for isolation
4. **Test edge cases**: Empty inputs, None values, exceptions
5. **Use fixtures**: Leverage pytest fixtures for common setup
6. **Mark tests appropriately**: Use pytest markers for categorization

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    with patch('module.async_dependency', new_callable=AsyncMock) as mock_dep:
        mock_dep.return_value = "mocked_result"
        
        result = await async_function()
        
        assert result == "expected_result"
        mock_dep.assert_called_once()
```

### Mocking Guidelines

```python
# Mock external services
with patch('requests.get') as mock_get:
    mock_get.return_value.json.return_value = {"data": "test"}
    
# Mock async operations
with patch('module.async_func', new_callable=AsyncMock) as mock_async:
    mock_async.return_value = "result"
    
# Mock file operations
with patch('builtins.open', mock_open(read_data="file content")):
    # Test file reading
```

## 📈 Coverage Goals

- **Overall coverage**: 80%+ (configured in pytest.ini)
- **Critical modules**: 90%+ (auth, api, models)
- **UI modules**: 70%+ (harder to test, focus on logic)

### Viewing Coverage

```bash
# Generate HTML coverage report
pytest --cov=github_cli --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🐛 Debugging Tests

### Running Single Test

```bash
# Run specific test method
pytest tests/unit/api/test_client.py::TestGitHubClient::test_get_request_success -v

# Run with pdb debugger
pytest tests/unit/api/test_client.py::TestGitHubClient::test_get_request_success --pdb
```

### Common Issues

1. **Import errors**: Check PYTHONPATH and module structure
2. **Async test failures**: Ensure `@pytest.mark.asyncio` decorator
3. **Mock not working**: Verify patch target path
4. **Fixture not found**: Check conftest.py and fixture scope

## 🔄 Continuous Integration

Tests are designed to run in CI environments:

- **Fast feedback**: Unit tests run quickly
- **Isolated**: No external dependencies for unit tests
- **Deterministic**: Consistent results across environments
- **Comprehensive**: Good coverage of critical paths

### CI Configuration

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    python run_tests.py all --coverage
    
- name: Upload coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Textual testing guide](https://textual.textualize.io/guide/testing/)
- [GitHub CLI testing best practices](../docs/developer/testing.md)
