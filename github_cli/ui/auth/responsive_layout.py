"""
Responsive authentication layout system for GitHub CLI.

This module provides responsive layout management specifically for authentication
screens, adapting to different terminal sizes and providing optimal user experience.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable, Callable
from textual.geometry import Size
from loguru import logger

from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager, LayoutBreakpoint
from github_cli.auth.preference_manager import AuthPreferenceManager


@dataclass(frozen=True, slots=True)
class AuthLayoutConfig:
    """Configuration for authentication screen layout."""
    layout_type: Literal["compact", "standard", "expanded"]
    container_width: int
    container_height: int
    show_detailed_instructions: bool
    show_progress_details: bool
    enable_animations: bool
    button_layout: Literal["horizontal", "vertical", "grid"]
    text_truncation: bool
    show_device_code_emphasis: bool = True
    show_countdown_timer: bool = True
    show_browser_fallback: bool = True
    max_instruction_lines: int = 10


@runtime_checkable
class AuthView(Protocol):
    """Protocol for authentication view implementations."""

    def render_auth_screen(self, config: AuthLayoutConfig) -> None:
        """Render the authentication screen with the given configuration."""
        ...

    def update_progress(self, step: str, details: dict[str, str] | None = None) -> None:
        """Update the progress display."""
        ...

    def show_error(self, error_message: str, recovery_options: list[str] | None = None) -> None:
        """Show error message with optional recovery options."""
        ...


class ResponsiveAuthLayout:
    """Manages responsive layout for authentication screens."""

    # Authentication-specific breakpoints
    AUTH_BREAKPOINTS = {
        "compact": {
            "min_width": 0,
            "min_height": 0,
            "max_width": 59,
            "max_height": 14,
            "layout_type": "compact"
        },
        "standard": {
            "min_width": 60,
            "min_height": 15,
            "max_width": 99,
            "max_height": 24,
            "layout_type": "standard"
        },
        "expanded": {
            "min_width": 100,
            "min_height": 25,
            "max_width": float('inf'),
            "max_height": float('inf'),
            "layout_type": "expanded"
        }
    }

    def __init__(self, layout_manager: ResponsiveLayoutManager,
                 preference_manager: AuthPreferenceManager | None = None) -> None:
        """Initialize the responsive authentication layout."""
        self.layout_manager = layout_manager
        self.preference_manager = preference_manager or AuthPreferenceManager()
        self.current_config: AuthLayoutConfig | None = None
        self._resize_callbacks: list[Callable] = []

        # Register for layout changes
        self.layout_manager.add_resize_callback(self._on_terminal_resize)

        logger.debug("ResponsiveAuthLayout initialized with preferences")

    def add_resize_callback(self, callback: Callable) -> None:
        """Add a callback to be called when auth layout changes."""
        self._resize_callbacks.append(callback)

    def remove_resize_callback(self, callback: Callable) -> None:
        """Remove a resize callback."""
        if callback in self._resize_callbacks:
            self._resize_callbacks.remove(callback)

    def get_optimal_layout(self, terminal_size: Size | None = None) -> AuthLayoutConfig:
        """Determine optimal layout configuration based on terminal size."""
        if terminal_size is None:
            terminal_size = self.layout_manager.app.size

        # Determine layout type based on terminal dimensions
        layout_type = self._determine_layout_type(terminal_size)

        # Create configuration based on layout type
        config = self._create_layout_config(layout_type, terminal_size)

        logger.debug(
            f"Optimal auth layout: {layout_type} for size {terminal_size.width}x{terminal_size.height}")

        return config

    def _determine_layout_type(self, terminal_size: Size) -> Literal["compact", "standard", "expanded"]:
        """Determine the appropriate layout type for the given terminal size."""
        width, height = terminal_size.width, terminal_size.height

        # Use preference manager to get optimal layout
        preferred_layout = self.preference_manager.get_optimal_layout(
            width, height)

        # Check if preferred layout is valid for current terminal size
        if preferred_layout in self.AUTH_BREAKPOINTS:
            breakpoint = self.AUTH_BREAKPOINTS[preferred_layout]
            if (width >= breakpoint["min_width"] and  # type: ignore[operator]
                    height >= breakpoint["min_height"]):  # type: ignore[operator]
                return preferred_layout  # type: ignore

        # Fallback to automatic detection if preference doesn't fit
        for layout_name in ["expanded", "standard", "compact"]:
            breakpoint = self.AUTH_BREAKPOINTS[layout_name]
            if (width >= breakpoint["min_width"] and  # type: ignore[operator]
                # type: ignore[operator]
                height >= breakpoint["min_height"] and
                width <= breakpoint["max_width"] and  # type: ignore[operator]
                    height <= breakpoint["max_height"]):  # type: ignore[operator]
                return breakpoint["layout_type"]  # type: ignore[return-value]

        # Final fallback to compact for very small terminals
        return "compact"

    def _create_layout_config(self, layout_type: Literal["compact", "standard", "expanded"],
                              terminal_size: Size) -> AuthLayoutConfig:
        """Create layout configuration for the specified layout type."""
        width, height = terminal_size.width, terminal_size.height
        prefs = self.preference_manager.preferences
        accessibility = self.preference_manager.get_accessibility_settings()

        # Base configuration for layout type
        base_configs = {
            "compact": {
                "container_width": min(width, 50),
                "container_height": min(height, 12),
                "show_detailed_instructions": False,
                "show_progress_details": False,
                "enable_animations": False,
                "button_layout": "vertical",
                "text_truncation": True,
                "show_countdown_timer": False,
                "show_browser_fallback": False,
                "max_instruction_lines": 3
            },
            "standard": {
                "container_width": min(width - 4, 80),
                "container_height": min(height - 4, 20),
                "show_detailed_instructions": True,
                "show_progress_details": True,
                "enable_animations": True,
                "button_layout": "horizontal",
                "text_truncation": False,
                "show_countdown_timer": True,
                "show_browser_fallback": True,
                "max_instruction_lines": 6
            },
            "expanded": {
                "container_width": min(width - 8, 120),
                "container_height": min(height - 6, 30),
                "show_detailed_instructions": True,
                "show_progress_details": True,
                "enable_animations": True,
                "button_layout": "grid",
                "text_truncation": False,
                "show_countdown_timer": True,
                "show_browser_fallback": True,
                "max_instruction_lines": 10
            }
        }

        config = base_configs[layout_type].copy()

        # Apply user preferences
        if not prefs.enable_animations:
            config["enable_animations"] = False

        if prefs.show_technical_details:
            config["show_detailed_instructions"] = True
            config["show_progress_details"] = True

        # Apply accessibility settings
        if accessibility["accessibility_mode"]:
            config["enable_animations"] = False
            config["text_truncation"] = False
            config["show_detailed_instructions"] = True

        if accessibility["keyboard_only_navigation"]:
            config["button_layout"] = "vertical"  # Easier keyboard navigation

        # Apply terminal-specific optimizations
        terminal_info = self.preference_manager.detect_terminal_environment()
        terminal_name = terminal_info.get(
            'program', terminal_info.get('name', 'unknown'))
        optimizations = prefs.get_terminal_optimization(terminal_name)

        if optimizations:
            config.update(optimizations)

        return AuthLayoutConfig(
            layout_type=layout_type,
            show_device_code_emphasis=True,
            **config  # type: ignore[arg-type]
        )

    def create_auth_view(self, config: AuthLayoutConfig) -> AuthView:
        """Create appropriate auth view for current layout configuration."""
        # Import here to avoid circular imports
        from github_cli.ui.auth.auth_views import CompactAuthView, StandardAuthView, ExpandedAuthView

        view_map = {
            "compact": CompactAuthView,
            "standard": StandardAuthView,
            "expanded": ExpandedAuthView
        }

        view_class = view_map[config.layout_type]
        return view_class(config)

    def handle_resize(self, new_size: Size) -> None:
        """Handle terminal resize during authentication."""
        old_config = self.current_config
        new_config = self.get_optimal_layout(new_size)

        # Check if layout actually changed
        if (old_config is None or
            old_config.layout_type != new_config.layout_type or
            abs(old_config.container_width - new_config.container_width) > 5 or
                abs(old_config.container_height - new_config.container_height) > 3):

            self.current_config = new_config

            logger.info(
                f"Auth layout changed: {old_config.layout_type if old_config else 'None'} -> {new_config.layout_type}")

            # Notify callbacks
            for callback in self._resize_callbacks:
                try:
                    callback(old_config, new_config)
                except Exception as e:
                    logger.error(f"Error in auth resize callback: {e}")

    def _on_terminal_resize(self, old_breakpoint: LayoutBreakpoint | None,
                            new_breakpoint: LayoutBreakpoint) -> None:
        """Handle terminal resize events from the layout manager."""
        terminal_size = self.layout_manager.app.size
        self.handle_resize(terminal_size)

    def get_layout_constraints(self, config: AuthLayoutConfig) -> dict[str, int]:
        """Get layout constraints for the given configuration."""
        return {
            "min_width": 40 if config.layout_type == "compact" else 60,
            "min_height": 8 if config.layout_type == "compact" else 12,
            "preferred_width": config.container_width,
            "preferred_height": config.container_height,
            "max_width": config.container_width + 20,
            "max_height": config.container_height + 10
        }

    def should_use_vertical_layout(self, config: AuthLayoutConfig) -> bool:
        """Determine if vertical layout should be used for the given configuration."""
        return (config.layout_type == "compact" or
                config.button_layout == "vertical" or
                config.container_width < 60)

    def get_content_areas(self, config: AuthLayoutConfig) -> dict[str, dict[str, int]]:
        """Get content area dimensions for different sections of the auth screen."""
        total_width = config.container_width
        total_height = config.container_height

        if config.layout_type == "compact":
            return {
                "header": {"width": total_width, "height": 2},
                "instructions": {"width": total_width, "height": 3},
                "device_code": {"width": total_width, "height": 2},
                "progress": {"width": total_width, "height": 2},
                "actions": {"width": total_width, "height": 3}
            }
        elif config.layout_type == "standard":
            return {
                "header": {"width": total_width, "height": 3},
                "instructions": {"width": total_width, "height": 5},
                "device_code": {"width": total_width // 2, "height": 3},
                "progress": {"width": total_width // 2, "height": 3},
                "actions": {"width": total_width, "height": 4},
                "status": {"width": total_width, "height": 2}
            }
        else:  # expanded
            return {
                "header": {"width": total_width, "height": 4},
                "instructions": {"width": total_width * 2 // 3, "height": 6},
                "device_code": {"width": total_width // 3, "height": 4},
                "progress": {"width": total_width // 3, "height": 4},
                "actions": {"width": total_width // 2, "height": 5},
                "status": {"width": total_width, "height": 3},
                "help": {"width": total_width // 2, "height": 5}
            }

    def record_successful_authentication(self, auth_duration: float, retry_count: int = 0) -> None:
        """Record successful authentication for pattern learning."""
        if self.current_config:
            terminal_size = self.layout_manager.app.size
            auth_data = {
                'width': terminal_size.width,
                'height': terminal_size.height,
                'layout': self.current_config.layout_type,
                'duration': auth_duration,
                'retries': retry_count
            }
            self.preference_manager.record_successful_authentication(auth_data)
            logger.debug(f"Recorded successful auth pattern: {auth_data}")

    def cleanup(self) -> None:
        """Clean up resources when layout manager is destroyed."""
        self.layout_manager.remove_resize_callback(self._on_terminal_resize)
        self._resize_callbacks.clear()
        logger.debug("ResponsiveAuthLayout cleaned up")
