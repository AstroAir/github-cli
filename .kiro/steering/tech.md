---
inclusion: always
---

# GitHub CLI Development Standards

## Required Technologies
- **Python 3.11+** with type hints, async/await, and modern features
- **Async-first architecture** - all I/O operations must be async
- **Textual** for TUI components, **Rich** for terminal formatting
- **aiohttp** as primary HTTP client, **Pydantic** for data models
- **Loguru** for structured async logging

## Code Standards

### Python Requirements
- Type hints mandatory for all functions (params and returns)
- Use `async def` for any I/O operations
- Import `from __future__ import annotations` in all files
- Pydantic models for all structured data
- Custom exceptions from `github_cli.utils.exceptions`

### Import Order
```python
from __future__ import annotations

# Standard library
import asyncio
from typing import Any

# Third-party
import aiohttp
from rich.console import Console

# Local
from github_cli.api.client import GitHubClient
```

## Architecture Rules

### Module Organization
- `api/`: Async GitHub API clients only
- `auth/`: OAuth flows and token management  
- `models/`: Pydantic models for GitHub entities
- `tui/`: Textual UI components
- `ui/`: Rich formatting and CLI output
- `utils/`: Config, exceptions, helpers

### Async Patterns
- Use async context managers for cleanup
- Handle errors in all async functions
- Use `asyncio.gather()` for concurrent ops
- Always close HTTP sessions

### Data Models
- Pydantic models for all API responses
- Include field validation and type conversion
- Implement `__str__` and `__repr__` methods

## Development Commands
```bash
# Install: uv pip install -e .
# Run CLI: python -m github_cli
# TUI mode: python -m github_cli --tui
# Hot reload: textual run --dev github_cli.tui.app:GitHubTUIApp
```

## API Integration
- Use centralized `GitHubClient` class exclusively
- Implement rate limiting and retry logic
- Handle auth errors gracefully with user feedback
- Store tokens securely via keyring
- Catch `aiohttp.ClientError` with exponential backoff
- Log detailed errors, show user-friendly messages