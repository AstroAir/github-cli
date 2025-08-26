"""
Base layout components for GitHub CLI TUI.

This module provides the base layout components and utilities
that can be used across different TUI screens and widgets.
"""

from typing import Any, Dict, Optional

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager


class BaseLayout:
    """Base layout class with common functionality."""

    def __init__(self, layout_manager: Optional[ResponsiveLayoutManager] = None):
        self.layout_manager = layout_manager
        self._cached_configs: Dict[str, Any] = {}

    def get_layout_config(self, config_type: str) -> Dict[str, Any]:
        """Get layout configuration for a specific type."""
        if config_type not in self._cached_configs and self.layout_manager:
            if config_type == "header":
                self._cached_configs[config_type] = self.layout_manager.get_header_config(
                )
            elif config_type == "footer":
                self._cached_configs[config_type] = self.layout_manager.get_footer_config(
                )
            elif config_type == "sidebar":
                self._cached_configs[config_type] = self.layout_manager.get_sidebar_config(
                )
            elif config_type == "content":
                self._cached_configs[config_type] = self.layout_manager.get_content_config(
                )
            else:
                self._cached_configs[config_type] = {}

        # type: ignore[no-any-return]
        return self._cached_configs.get(config_type, {})

    def should_use_compact_layout(self) -> bool:
        """Check if we should use compact layout."""
        if not self.layout_manager:
            return False

        breakpoint = self.layout_manager.get_current_breakpoint()
        return breakpoint.compact_mode

    def should_use_vertical_layout(self) -> bool:
        """Check if we should use vertical layout."""
        if not self.layout_manager:
            return False

        return self.layout_manager.should_use_vertical_layout()


class ResponsiveContainer(Container):
    """Container that adapts based on responsive layout."""

    def __init__(self, layout_manager: Optional[ResponsiveLayoutManager] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.layout_manager = layout_manager
        self._update_responsive_classes()

    def _update_responsive_classes(self) -> None:
        """Update CSS classes based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()

        # Remove old breakpoint classes
        for bp_name in ["xs", "sm", "md", "lg", "xl", "horizontal_tight", "horizontal_ultra_tight"]:
            self.remove_class(bp_name)

        # Add current breakpoint class
        self.add_class(breakpoint.name)

        # Add compact class if in compact mode
        if breakpoint.compact_mode:
            self.add_class("compact")
        else:
            self.remove_class("compact")


class TitleBar(Static):
    """Responsive title bar component."""

    def __init__(self, title: str, layout_manager: Optional[ResponsiveLayoutManager] = None, **kwargs: Any) -> None:
        super().__init__(title, **kwargs)
        self.layout_manager = layout_manager
        self._original_title = title
        self._update_title()

    def _update_title(self) -> None:
        """Update title based on layout constraints."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()

        # Truncate title for very small screens
        if breakpoint.name in ["xs", "horizontal_ultra_tight"]:
            # Use abbreviated title
            abbreviated = self._abbreviate_title(self._original_title)
            self.update(abbreviated)
        else:
            self.update(self._original_title)

    def _abbreviate_title(self, title: str) -> str:
        """Create abbreviated version of title for small screens."""
        if len(title) <= 10:
            return title

        # Take first and last words
        words = title.split()
        if len(words) <= 2:
            return title[:10] + "..."

        return f"{words[0]}...{words[-1]}"


def create_responsive_layout(
    content: Any,
    title: Optional[str] = None,
    sidebar_content: Any = None,
    layout_manager: Optional[ResponsiveLayoutManager] = None,
    **kwargs: Any
) -> Container:
    """Create a responsive layout with optional sidebar."""

    layout = BaseLayout(layout_manager)

    with ResponsiveContainer(layout_manager=layout_manager, id="main-layout", **kwargs) as container:
        # Add title if provided
        if title:
            title_bar = TitleBar(
                title, layout_manager=layout_manager, id="title-bar")
            container.mount(title_bar)

        # Create content area
        if layout.should_use_vertical_layout():
            # Vertical layout for small screens
            with Vertical(id="content-area-vertical") as content_area:
                content_area.mount(content)
        else:
            # Horizontal layout with optional sidebar
            with Horizontal(id="content-area-horizontal") as content_area:
                # Add sidebar if provided and should be visible
                if sidebar_content and layout.get_layout_config("sidebar").get("visible", True):
                    with Vertical(id="sidebar", classes="sidebar") as sidebar:
                        sidebar.mount(sidebar_content)

                # Add main content
                with Vertical(id="main-content", classes="main-content") as main:
                    main.mount(content)

    return container
