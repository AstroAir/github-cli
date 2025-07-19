"""
TUI core package.

This package contains the core functionality for the GitHub CLI TUI,
including the main application, settings, shortcuts, and responsive layout.
"""

from .app import GitHubTUIApp
from .settings import SettingsWidget
from .shortcuts import (
    NavigationMode,
    ShortcutScope,
    KeyboardShortcut,
    NavigationContext,
    ShortcutManager
)
from .responsive import (
    LayoutBreakpoint,
    ResponsiveLayoutManager,
    AdaptiveWidget,
    get_responsive_styles
)

__all__ = [
    'GitHubTUIApp',
    'SettingsWidget',
    'NavigationMode',
    'ShortcutScope',
    'KeyboardShortcut',
    'NavigationContext',
    'ShortcutManager',
    'LayoutBreakpoint',
    'ResponsiveLayoutManager',
    'AdaptiveWidget',
    'get_responsive_styles'
]
