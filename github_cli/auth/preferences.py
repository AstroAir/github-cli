"""
Authentication preferences management for GitHub CLI
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, Optional, Literal

from github_cli.utils.exceptions import ConfigError


@dataclass
class AuthPreferences:
    """User preferences for authentication interface."""

    # Layout preferences
    preferred_layout: Optional[Literal["compact",
                                       "standard", "expanded"]] = None
    remember_terminal_size: bool = True
    auto_adapt_layout: bool = True

    # Behavior preferences
    auto_open_browser: bool = True
    auto_copy_url: bool = True
    show_technical_details: bool = False
    enable_animations: bool = True

    # Accessibility preferences
    accessibility_mode: bool = False
    high_contrast_mode: bool = False
    screen_reader_support: bool = False
    keyboard_only_navigation: bool = False
    large_text_mode: bool = False
    reduce_motion: bool = False
    audio_cues_enabled: bool = False
    extended_timeouts: bool = False
    simplified_interface: bool = False
    verbose_descriptions: bool = False

    # Terminal environment preferences
    terminal_capabilities: Dict[str, Any] = field(default_factory=dict)
    environment_optimizations: Dict[str, Any] = field(default_factory=dict)

    # Authentication flow preferences
    preferred_retry_count: int = 3
    preferred_timeout: int = 300  # 5 minutes
    remember_auth_patterns: bool = True
    skip_confirmation_prompts: bool = False

    def __post_init__(self) -> None:
        """Initialize default values for mutable fields."""
        # Fields are now initialized with field(default_factory=dict)
        # so no additional initialization needed
        pass

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the path to the auth preferences config file."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~')))
        else:  # Unix/Mac
            base_dir = Path(os.environ.get('XDG_CONFIG_HOME',
                            os.path.expanduser('~/.config')))

        config_dir = base_dir / 'github-cli'
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir / 'auth_preferences.json'

    @classmethod
    def load(cls) -> AuthPreferences:
        """Load preferences from config file."""
        config_path = cls.get_config_path()

        if not config_path.exists():
            # Return default preferences
            return cls()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Create instance with loaded data
            return cls(**data)

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise ConfigError(f"Failed to load auth preferences: {e}")

    def save(self) -> None:
        """Save preferences to config file."""
        config_path = self.get_config_path()

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)

        except (OSError, TypeError) as e:
            raise ConfigError(f"Failed to save auth preferences: {e}")

    def update(self, **kwargs: Any) -> None:
        """Update preferences with new values and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown preference key: {key}")

        self.save()

    def reset_to_defaults(self) -> None:
        """Reset all preferences to default values."""
        defaults = AuthPreferences()
        for field_name in asdict(self).keys():
            setattr(self, field_name, getattr(defaults, field_name))

        self.save()

    def get_layout_preference(self, terminal_width: int, terminal_height: int) -> Optional[str]:
        """Get layout preference based on terminal size and user settings."""
        if not self.auto_adapt_layout and self.preferred_layout:
            return self.preferred_layout

        # Auto-adapt based on terminal size if no explicit preference
        if terminal_width < 60 or terminal_height < 15:
            return "compact"
        elif terminal_width > 100 and terminal_height > 25:
            return "expanded"
        else:
            return "standard"

    def should_enable_accessibility(self) -> bool:
        """Check if accessibility features should be enabled."""
        return (
            self.accessibility_mode or
            self.high_contrast_mode or
            self.screen_reader_support or
            self.keyboard_only_navigation
        )

    def get_terminal_optimization(self, terminal_name: str) -> Dict[str, Any]:
        """Get terminal-specific optimizations."""
        result = self.environment_optimizations.get(terminal_name, {})
        return result if isinstance(result, dict) else {}

    def set_terminal_optimization(self, terminal_name: str, optimizations: Dict[str, Any]) -> None:
        """Set terminal-specific optimizations."""
        self.environment_optimizations[terminal_name] = optimizations
        self.save()

    def record_successful_auth_pattern(self, pattern_data: Dict[str, Any]) -> None:
        """Record successful authentication pattern for future optimization."""
        if not self.remember_auth_patterns:
            return

        # Store pattern data in terminal capabilities for now
        # This could be expanded to a separate patterns storage system
        pattern_key = f"auth_pattern_{pattern_data.get('terminal_size', 'unknown')}"
        self.terminal_capabilities[pattern_key] = pattern_data
        self.save()

    def get_accessibility_settings(self) -> Dict[str, Any]:
        """Get all accessibility-related settings as a dictionary."""
        return {
            "accessibility_mode": self.accessibility_mode,
            "high_contrast_mode": self.high_contrast_mode,
            "screen_reader_support": self.screen_reader_support,
            "keyboard_only_navigation": self.keyboard_only_navigation,
            "large_text_mode": self.large_text_mode,
            "reduce_motion": self.reduce_motion,
            "audio_cues_enabled": self.audio_cues_enabled,
            "extended_timeouts": self.extended_timeouts,
            "simplified_interface": self.simplified_interface,
            "verbose_descriptions": self.verbose_descriptions,
        }

    def update_accessibility_settings(self, settings: Dict[str, Any]) -> None:
        """Update accessibility settings and save preferences."""
        accessibility_keys = {
            "accessibility_mode", "high_contrast_mode", "screen_reader_support",
            "keyboard_only_navigation", "large_text_mode", "reduce_motion",
            "audio_cues_enabled", "extended_timeouts", "simplified_interface",
            "verbose_descriptions"
        }

        for key, value in settings.items():
            if key in accessibility_keys and hasattr(self, key):
                setattr(self, key, value)

        self.save()

    def enable_full_accessibility(self) -> None:
        """Enable all accessibility features for maximum compatibility."""
        self.accessibility_mode = True
        self.high_contrast_mode = True
        self.screen_reader_support = True
        self.keyboard_only_navigation = True
        self.large_text_mode = True
        self.reduce_motion = True
        self.audio_cues_enabled = True
        self.extended_timeouts = True
        self.simplified_interface = True
        self.verbose_descriptions = True
        self.save()

    def get_timeout_multiplier(self) -> float:
        """Get timeout multiplier based on accessibility settings."""
        if self.extended_timeouts:
            return 2.0
        elif self.accessibility_mode or self.screen_reader_support:
            return 1.5
        else:
            return 1.0
