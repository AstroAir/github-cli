"""
TUI screens package.

This package contains all the screen components for the GitHub CLI TUI,
organized by functionality.
"""

from .auth import AuthScreen
from .help import HelpScreen
from .repository import RepositoryDetailScreen
from .pull_request import PullRequestDetailScreen
from .notification import NotificationDetailScreen
from .search import SearchResultDetailScreen
from .error import ErrorDetailScreen
from .actions import WorkflowRunDetailScreen
from .responsive_repository import ResponsiveRepositoryDetailScreen

__all__ = [
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
