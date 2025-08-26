"""
TUI (Text User Interface) components for GitHub CLI.

This package contains Textual-based UI components for the terminal interface,
organized into logical subpackages for better maintainability.
"""

# Import from the new organized structure
from .core import GitHubTUIApp
from .screens import (
    AuthScreen,
    HelpScreen,
    RepositoryDetailScreen,
    PullRequestDetailScreen,
    NotificationDetailScreen,
    SearchResultDetailScreen,
    ErrorDetailScreen,
    WorkflowRunDetailScreen,
    ResponsiveRepositoryDetailScreen
)

# Keep the old imports for backward compatibility
from .core.app import GitHubTUIApp as GitHubTUIApp_
from .screens.auth import AuthScreen as AuthScreen_
from .screens.help import HelpScreen as HelpScreen_

__all__ = [
    # Main application
    'GitHubTUIApp',

    # Screen components
    'AuthScreen',
    'HelpScreen',
    'RepositoryDetailScreen',
    'PullRequestDetailScreen',
    'NotificationDetailScreen',
    'SearchResultDetailScreen',
    'ErrorDetailScreen',
    'WorkflowRunDetailScreen',
    'ResponsiveRepositoryDetailScreen'
]
