from __future__ import annotations

"""
GitHub CLI - An advanced terminal-based GitHub client with TUI support
"""

__version__ = "0.1.0"
__author__ = "GitHub CLI Contributors"
__description__ = "An advanced terminal-based GitHub client with TUI support"

# Re-export main components for easy access
from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError, AuthenticationError, NetworkError

# TUI components
try:
    from github_cli.tui.app import GitHubTUIApp, run_tui
    TUI_AVAILABLE = True
except ImportError:
    TUI_AVAILABLE = False

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "GitHubClient",
    "Authenticator",
    "Config",
    "GitHubCLIError",
    "AuthenticationError",
    "NetworkError",
    "TUI_AVAILABLE"
]

if TUI_AVAILABLE:
    __all__.extend(["GitHubTUIApp", "run_tui"])
