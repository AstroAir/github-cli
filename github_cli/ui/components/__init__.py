"""
Reusable UI components.

This package contains shared UI components that can be used across different interfaces.
"""

# Import all component modules for easy access
from . import common
from . import github  
from . import diff

# Re-export main classes for convenience
from .common import BasePanelFactory, InfoPanel, ErrorPanel, BaseTable, GitHubTable, HeaderFactory, FooterFactory
from .github import RepositoryPanel, PullRequestPanel, IssuePanel, NotificationPanel
from .diff import DiffParser, DiffRenderer, DiffViewer

__all__ = [
    # Common components
    'common',
    'BasePanelFactory',
    'InfoPanel',
    'ErrorPanel', 
    'BaseTable',
    'GitHubTable',
    'HeaderFactory',
    'FooterFactory',
    
    # GitHub components
    'github',
    'RepositoryPanel',
    'PullRequestPanel',
    'IssuePanel', 
    'NotificationPanel',
    
    # Diff components
    'diff',
    'DiffParser',
    'DiffRenderer',
    'DiffViewer',
]
