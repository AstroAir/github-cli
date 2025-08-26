"""
GitHub CLI user interface modules

This package contains all UI-related components including:
- Rich-based terminal UI components (dashboard, terminal)
- Textual-based TUI components (tui subpackage)
- Authentication UI components (auth subpackage)
- Reusable UI components (components subpackage)
"""

from .dashboard import Dashboard
from .terminal import TerminalUI
from .diff_viewer import DiffViewer

# Subpackages
from . import tui
from . import auth
from . import components

__all__ = [
    'Dashboard',
    'TerminalUI',
    'DiffViewer',
    'tui',
    'auth',
    'components'
]
