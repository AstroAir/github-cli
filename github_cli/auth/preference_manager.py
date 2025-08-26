"""
Authentication preference management system
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, Tuple

from github_cli.auth.preferences import AuthPreferences
from github_cli.utils.exceptions import ConfigError


class AuthPreferenceManager:
    """Manages authentication preferences with environment detection."""

    def __init__(self) -> None:
        self._preferences: Optional[AuthPreferences] = None
        self._terminal_info: Dict[str, Any] = {}

    @property
    def preferences(self) -> AuthPreferences:
        """Get current preferences, loading if necessary."""
        if self._preferences is None:
            self._preferences = AuthPreferences.load()
        return self._preferences

    def reload_preferences(self) -> None:
        """Reload preferences from disk."""
        self._preferences = AuthPreferences.load()

    def detect_terminal_environment(self) -> Dict[str, Any]:
        """Detect current terminal environment and capabilities."""
        if self._terminal_info:
            return self._terminal_info

        terminal_info = {
            'name': os.environ.get('TERM', 'unknown'),
            'program': os.environ.get('TERM_PROGRAM', 'unknown'),
            'version': os.environ.get('TERM_PROGRAM_VERSION', 'unknown'),
            'colorterm': os.environ.get('COLORTERM', ''),
            'supports_color': self._detect_color_support(),
            'supports_unicode': self._detect_unicode_support(),
            'supports_mouse': self._detect_mouse_support(),
            'is_ssh': 'SSH_CONNECTION' in os.environ,
            'is_tmux': 'TMUX' in os.environ,
            'is_screen': os.environ.get('TERM', '').startswith('screen'),
        }

        self._terminal_info = terminal_info
        return terminal_info

    def _detect_color_support(self) -> bool:
        """Detect if terminal supports colors."""
        colorterm = os.environ.get('COLORTERM', '')
        term = os.environ.get('TERM', '')

        if colorterm in ('truecolor', '24bit'):
            return True

        if any(color_term in term for color_term in ['color', '256', 'xterm']):
            return True

        return False

    def _detect_unicode_support(self) -> bool:
        """Detect if terminal supports Unicode."""
        lang = os.environ.get('LANG', '')
        lc_all = os.environ.get('LC_ALL', '')

        return any('UTF-8' in var or 'utf8' in var.lower()
                   for var in [lang, lc_all] if var)

    def _detect_mouse_support(self) -> bool:
        """Detect if terminal supports mouse input."""
        term = os.environ.get('TERM', '')
        term_program = os.environ.get('TERM_PROGRAM', '')

        # Most modern terminals support mouse
        modern_terminals = ['xterm', 'screen', 'tmux', 'iTerm', 'Terminal']
        return any(terminal in term or terminal in term_program
                   for terminal in modern_terminals)

    def get_optimal_layout(self, terminal_width: int, terminal_height: int) -> str:
        """Get optimal layout based on preferences and terminal size."""
        prefs = self.preferences

        # Check for explicit user preference first
        if prefs.preferred_layout and not prefs.auto_adapt_layout:
            return prefs.preferred_layout

        # Get layout based on terminal size and preferences
        layout = prefs.get_layout_preference(terminal_width, terminal_height)

        # Apply terminal-specific optimizations
        terminal_info = self.detect_terminal_environment()
        terminal_name = terminal_info.get(
            'program', terminal_info.get('name', 'unknown'))
        optimizations = prefs.get_terminal_optimization(terminal_name)

        if 'force_layout' in optimizations:
            layout = optimizations['force_layout']

        return layout or 'standard'

    def should_auto_open_browser(self) -> bool:
        """Check if browser should be opened automatically."""
        prefs = self.preferences
        terminal_info = self.detect_terminal_environment()

        # Don't auto-open in SSH sessions unless explicitly enabled
        if terminal_info.get('is_ssh') and not prefs.auto_open_browser:
            return False

        return prefs.auto_open_browser

    def get_accessibility_settings(self) -> Dict[str, bool]:
        """Get current accessibility settings."""
        prefs = self.preferences
        terminal_info = self.detect_terminal_environment()

        settings = {
            'accessibility_mode': prefs.accessibility_mode,
            'high_contrast_mode': prefs.high_contrast_mode,
            'screen_reader_support': prefs.screen_reader_support,
            'keyboard_only_navigation': prefs.keyboard_only_navigation,
            'supports_color': terminal_info.get('supports_color', True),
            'supports_unicode': terminal_info.get('supports_unicode', True),
        }

        # Auto-enable high contrast in certain terminals
        if not terminal_info.get('supports_color'):
            settings['high_contrast_mode'] = True

        return settings

    def update_preferences(self, **kwargs: Any) -> None:
        """Update preferences with validation."""
        prefs = self.preferences

        # Validate layout preference
        if 'preferred_layout' in kwargs:
            layout = kwargs['preferred_layout']
            if layout and layout not in ['compact', 'standard', 'expanded']:
                raise ValueError(f"Invalid layout preference: {layout}")

        # Validate timeout values
        if 'preferred_timeout' in kwargs:
            timeout = kwargs['preferred_timeout']
            if not isinstance(timeout, int) or timeout < 30 or timeout > 1800:
                raise ValueError("Timeout must be between 30 and 1800 seconds")

        # Validate retry count
        if 'preferred_retry_count' in kwargs:
            retry_count = kwargs['preferred_retry_count']
            if not isinstance(retry_count, int) or retry_count < 0 or retry_count > 10:
                raise ValueError("Retry count must be between 0 and 10")

        prefs.update(**kwargs)

    def record_successful_authentication(self, auth_data: Dict[str, Any]) -> None:
        """Record successful authentication for pattern learning."""
        prefs = self.preferences

        if not prefs.remember_auth_patterns:
            return

        terminal_info = self.detect_terminal_environment()
        pattern_data = {
            'terminal_size': f"{auth_data.get('width', 0)}x{auth_data.get('height', 0)}",
            'layout_used': auth_data.get('layout', 'standard'),
            'terminal_program': terminal_info.get('program', 'unknown'),
            'success_time': auth_data.get('duration', 0),
            'retry_count': auth_data.get('retries', 0),
        }

        prefs.record_successful_auth_pattern(pattern_data)

    def suggest_layout_optimization(self, terminal_width: int, terminal_height: int) -> Optional[str]:
        """Suggest layout optimization based on usage patterns."""
        prefs = self.preferences

        if not prefs.remember_auth_patterns:
            return None

        # Look for successful patterns with similar terminal size
        current_size = f"{terminal_width}x{terminal_height}"

        for key, pattern in prefs.terminal_capabilities.items():
            if not key.startswith('auth_pattern_'):
                continue

            pattern_size = pattern.get('terminal_size', '')
            if pattern_size == current_size:
                layout_used = pattern.get('layout_used')
                return str(layout_used) if layout_used is not None else None

        return None

    def reset_preferences(self) -> None:
        """Reset preferences to defaults."""
        if self._preferences:
            self._preferences.reset_to_defaults()
        else:
            prefs = AuthPreferences.load()
            prefs.reset_to_defaults()

        self._preferences = None  # Force reload
