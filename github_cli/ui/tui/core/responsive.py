"""
Responsive layout manager for GitHub CLI TUI.

This module provides utilities for dynamically optimizing terminal layouts
based on available terminal size and content requirements. It includes special
support for horizontal screens with limited height, priority-based component
management, and adaptive UI elements.

Key Features:
- Breakpoint-based responsive design
- Height-optimized layouts for horizontal screens
- Priority-based component filtering
- Dynamic UI element visibility
- Adaptive table configurations
"""

from __future__ import annotations

from typing import NamedTuple, Literal, Callable
from textual.app import App
from textual.geometry import Size
from loguru import logger


class LayoutBreakpoint(NamedTuple):
    """Layout breakpoint configuration."""
    name: str
    min_width: int
    min_height: int
    sidebar_width: int
    sidebar_visible: bool
    tabs_horizontal: bool
    compact_mode: bool
    header_height: int
    footer_height: int
    status_bar_height: int
    compact_header: bool
    collapsible_sidebar: bool
    priority_based_layout: bool


class ResponsiveLayoutManager:
    """Manages responsive layout configurations for different terminal sizes."""

    # Define breakpoints for different screen sizes
    BREAKPOINTS = [
        LayoutBreakpoint(
            name="xs",          # Extra small (mobile-like)
            min_width=0,
            min_height=0,
            sidebar_width=0,
            sidebar_visible=False,
            tabs_horizontal=False,
            compact_mode=True,
            header_height=1,
            footer_height=0,
            status_bar_height=1,
            compact_header=True,
            collapsible_sidebar=False,
            priority_based_layout=True
        ),
        LayoutBreakpoint(
            name="sm",          # Small
            min_width=60,
            min_height=15,
            sidebar_width=15,
            sidebar_visible=True,
            tabs_horizontal=False,
            compact_mode=True,
            header_height=2,
            footer_height=1,
            status_bar_height=1,
            compact_header=True,
            collapsible_sidebar=True,
            priority_based_layout=True
        ),
        LayoutBreakpoint(
            name="md",          # Medium
            min_width=80,
            min_height=20,
            sidebar_width=20,
            sidebar_visible=True,
            tabs_horizontal=True,
            compact_mode=False,
            header_height=3,
            footer_height=1,
            status_bar_height=1,
            compact_header=False,
            collapsible_sidebar=True,
            priority_based_layout=False
        ),
        LayoutBreakpoint(
            name="lg",          # Large
            min_width=120,
            min_height=30,
            sidebar_width=25,
            sidebar_visible=True,
            tabs_horizontal=True,
            compact_mode=False,
            header_height=3,
            footer_height=1,
            status_bar_height=1,
            compact_header=False,
            collapsible_sidebar=False,
            priority_based_layout=False
        ),
        LayoutBreakpoint(
            name="xl",          # Extra large
            min_width=160,
            min_height=40,
            sidebar_width=30,
            sidebar_visible=True,
            tabs_horizontal=True,
            compact_mode=False,
            header_height=3,
            footer_height=1,
            status_bar_height=1,
            compact_header=False,
            collapsible_sidebar=False,
            priority_based_layout=False
        ),
        # New breakpoints for horizontal screens with limited height
        LayoutBreakpoint(
            name="horizontal_tight",  # Wide but short screens
            min_width=100,
            min_height=12,
            sidebar_width=20,
            sidebar_visible=False,  # Hide sidebar to save horizontal space
            tabs_horizontal=True,
            compact_mode=True,
            header_height=1,
            footer_height=0,
            status_bar_height=1,
            compact_header=True,
            collapsible_sidebar=True,
            priority_based_layout=True
        ),
        LayoutBreakpoint(
            name="horizontal_ultra_tight",  # Very wide but very short screens
            min_width=120,
            min_height=8,
            sidebar_width=0,
            sidebar_visible=False,
            tabs_horizontal=True,
            compact_mode=True,
            header_height=1,
            footer_height=0,
            status_bar_height=0,  # Hide status bar to save space
            compact_header=True,
            collapsible_sidebar=False,
            priority_based_layout=True
        ),
    ]

    def __init__(self, app: App) -> None:
        """Initialize the responsive layout manager."""
        self.app = app
        self.current_breakpoint: LayoutBreakpoint | None = None
        self._callbacks: list[Callable] = []

    def add_resize_callback(self, callback: Callable) -> None:
        """Add a callback to be called when layout changes."""
        self._callbacks.append(callback)

    def remove_resize_callback(self, callback: Callable) -> None:
        """Remove a resize callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_current_breakpoint(self) -> LayoutBreakpoint:
        """Get the current breakpoint based on terminal size with height optimization."""
        size = self.app.size

        # Special handling for horizontal screens with limited height
        if size.width >= 100 and size.height <= 12:
            if size.height <= 8:
                return next(bp for bp in self.BREAKPOINTS if bp.name == "horizontal_ultra_tight")
            else:
                return next(bp for bp in self.BREAKPOINTS if bp.name == "horizontal_tight")

        # Find the largest breakpoint that fits (excluding horizontal-specific ones)
        regular_breakpoints = [bp for bp in self.BREAKPOINTS if not bp.name.startswith("horizontal")]
        selected_breakpoint = regular_breakpoints[0]  # Default to smallest

        for breakpoint in reversed(regular_breakpoints):
            if size.width >= breakpoint.min_width and size.height >= breakpoint.min_height:
                selected_breakpoint = breakpoint
                break

        return selected_breakpoint

    def update_layout(self, size: Size) -> bool:
        """Update layout based on new terminal size. Returns True if layout changed."""
        new_breakpoint = self.get_current_breakpoint()

        if self.current_breakpoint is None or new_breakpoint.name != self.current_breakpoint.name:
            old_breakpoint = self.current_breakpoint
            self.current_breakpoint = new_breakpoint

            logger.info(
                f"Layout breakpoint changed: {old_breakpoint.name if old_breakpoint else 'None'} "
                f"-> {new_breakpoint.name} (size: {size.width}x{size.height})"
            )

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(old_breakpoint, new_breakpoint)
                except Exception as e:
                    logger.error(f"Error in resize callback: {e}")

            return True

        return False

    def get_sidebar_config(self) -> dict:
        """Get sidebar configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        return {
            "visible": self.current_breakpoint.sidebar_visible,
            "width": self.current_breakpoint.sidebar_width,
            "min_width": max(15, self.current_breakpoint.sidebar_width - 5),
            "max_width": min(50, self.current_breakpoint.sidebar_width + 10),
        }

    def get_content_config(self) -> dict:
        """Get main content area configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        sidebar_config = self.get_sidebar_config()
        available_width = self.app.size.width

        if sidebar_config["visible"]:
            content_width = available_width - \
                sidebar_config["width"] - 2  # Account for borders
        else:
            content_width = available_width

        return {
            "width": max(40, content_width),  # Minimum content width
            "compact_mode": self.current_breakpoint.compact_mode,
            "tabs_horizontal": self.current_breakpoint.tabs_horizontal,
            "priority_based_layout": self.current_breakpoint.priority_based_layout,
            "max_tab_count": self._get_max_tab_count(),
            "available_height": self._get_available_content_height(),
        }

    def _get_max_tab_count(self) -> int:
        """Get maximum number of tabs that can be displayed."""
        if not self.current_breakpoint:
            return 6
        
        if self.current_breakpoint.name.startswith("horizontal_ultra"):
            return 4
        elif self.current_breakpoint.name.startswith("horizontal_tight"):
            return 5
        elif self.current_breakpoint.compact_mode:
            return 4
        else:
            return 6

    def _get_available_content_height(self) -> int:
        """Calculate available height for content after UI chrome."""
        if not self.current_breakpoint:
            return max(10, self.app.size.height - 5)
        
        total_height = self.app.size.height
        used_height = (
            self.current_breakpoint.header_height + 
            self.current_breakpoint.footer_height + 
            self.current_breakpoint.status_bar_height +
            1  # Tab bar
        )
        
        return max(5, total_height - used_height)

    def get_header_config(self) -> dict:
        """Get header configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        return {
            "height": self.current_breakpoint.header_height,
            "compact": self.current_breakpoint.compact_header,
            "show_subtitle": not self.current_breakpoint.compact_header,
            "visible": self.current_breakpoint.header_height > 0,
        }

    def get_footer_config(self) -> dict:
        """Get footer configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        return {
            "height": self.current_breakpoint.footer_height,
            "visible": self.current_breakpoint.footer_height > 0,
        }

    def get_status_bar_config(self) -> dict:
        """Get status bar configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        return {
            "height": self.current_breakpoint.status_bar_height,
            "visible": self.current_breakpoint.status_bar_height > 0,
            "compact": self.current_breakpoint.compact_mode,
        }

    def should_hide_component(self, component_name: str, priority: str = "medium") -> bool:
        """Determine if a component should be hidden based on available space."""
        if not self.current_breakpoint:
            return False

        # Priority levels: high, medium, low
        if not self.current_breakpoint.priority_based_layout:
            return False

        available_height = self._get_available_content_height()
        
        # Hide low priority components first
        if priority == "low" and available_height < 15:
            return True
        
        # Hide medium priority components in very tight spaces
        if priority == "medium" and available_height < 10:
            return True
        
        # Only hide high priority components in extreme cases
        if priority == "high" and available_height < 6:
            return True
        
        return False

    def get_component_priorities(self) -> dict[str, str]:
        """Get component priorities for layout optimization."""
        return {
            "repositories": "high",
            "pull_requests": "high", 
            "issues": "high",
            "actions": "medium",
            "notifications": "medium",
            "search": "low",
            "settings": "low",
            "dashboard": "medium",
        }

    def optimize_layout_for_height(self, components: list[str]) -> list[str]:
        """Optimize component layout for height constraints."""
        if not self.current_breakpoint or not self.current_breakpoint.priority_based_layout:
            return components

        priorities = self.get_component_priorities()
        available_height = self._get_available_content_height()

        # Sort components by priority
        prioritized_components = sorted(
            components, 
            key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(priorities.get(x, "medium"), 2),
            reverse=True
        )

        # Filter components based on available height
        if available_height < 10:
            # Very tight - only show high priority
            return [c for c in prioritized_components if priorities.get(c, "medium") == "high"]
        elif available_height < 15:
            # Tight - show high and medium priority
            return [c for c in prioritized_components if priorities.get(c, "medium") in ["high", "medium"]]
        else:
            # Normal - show all
            return prioritized_components

    def get_table_config(self) -> dict:
        """Get data table configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        content_config = self.get_content_config()
        available_height = self._get_available_content_height()

        # Calculate optimal column widths based on available space
        if content_config["compact_mode"]:
            return {
                "show_header": True,
                "show_row_labels": False,
                "column_widths": self._get_compact_column_widths(),
                "max_visible_rows": min(max(5, available_height - 2), 10),
            }
        else:
            return {
                "show_header": True,
                "show_row_labels": True,
                "column_widths": self._get_normal_column_widths(),
                "max_visible_rows": min(max(8, available_height - 3), 20),
            }

    def _get_compact_column_widths(self) -> dict[str, int]:
        """Get column widths for compact mode."""
        content_width = self.get_content_config()["width"]

        # Distribute width among essential columns only
        return {
            "name": max(15, content_width // 3),
            "status": max(8, content_width // 6),
            "updated": max(12, content_width // 5),
        }

    def _get_normal_column_widths(self) -> dict[str, int]:
        """Get column widths for normal mode."""
        content_width = self.get_content_config()["width"]

        # More generous column widths for normal mode
        return {
            "name": max(20, content_width // 4),
            "description": max(30, content_width // 3),
            "language": max(10, content_width // 8),
            "stars": max(8, content_width // 10),
            "updated": max(15, content_width // 6),
        }

    def should_use_vertical_layout(self) -> bool:
        """Determine if vertical layout should be used instead of horizontal."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        # Use vertical layout for small screens or tall narrow terminals
        return (
            self.current_breakpoint.name in ["xs", "sm"] or
            (self.app.size.width < 100 and self.app.size.height >
             self.app.size.width * 0.8)
        )

    def get_adaptive_padding(self) -> dict[str, int]:
        """Get adaptive padding based on terminal size."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        if self.current_breakpoint.compact_mode:
            return {"horizontal": 0, "vertical": 0}
        else:
            return {"horizontal": 1, "vertical": 1}

    def get_adaptive_margins(self) -> dict[str, int]:
        """Get adaptive margins based on terminal size."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        if self.current_breakpoint.compact_mode:
            return {"horizontal": 0, "vertical": 0}
        else:
            return {"horizontal": 1, "vertical": 1}


class AdaptiveWidget:
    """Base mixin for widgets that need to adapt to layout changes."""

    def __init__(self, layout_manager: ResponsiveLayoutManager) -> None:
        """Initialize adaptive widget with layout manager."""
        self.layout_manager = layout_manager
        self.layout_manager.add_resize_callback(self._on_layout_change)

    def _on_layout_change(self, old_breakpoint: LayoutBreakpoint | None, new_breakpoint: LayoutBreakpoint) -> None:
        """Handle layout change. Override in subclasses."""
        pass

    def cleanup(self) -> None:
        """Clean up resources when widget is destroyed."""
        self.layout_manager.remove_resize_callback(self._on_layout_change)


def get_responsive_styles(layout_manager: ResponsiveLayoutManager) -> str:
    """Generate responsive CSS styles based on current layout."""
    if not layout_manager.current_breakpoint:
        layout_manager.current_breakpoint = layout_manager.get_current_breakpoint()

    breakpoint = layout_manager.current_breakpoint
    sidebar_config = layout_manager.get_sidebar_config()
    content_config = layout_manager.get_content_config()
    padding = layout_manager.get_adaptive_padding()
    margins = layout_manager.get_adaptive_margins()

    # Generate dynamic CSS
    css_rules = []

    # Sidebar rules
    if sidebar_config["visible"]:
        css_rules.append(f"""
        .sidebar {{
            width: {sidebar_config['width']};
            min-width: {sidebar_config['min_width']};
            max-width: {sidebar_config['max_width']};
            display: block;
        }}
        """)
    else:
        css_rules.append("""
        .sidebar {
            display: none;
        }
        """)

    # Content area rules
    css_rules.append(f"""
    #main-tabs {{
        width: {content_config['width']};
    }}
    
    .adaptive-container {{
        padding: {padding['vertical']} {padding['horizontal']};
        margin: {margins['vertical']} {margins['horizontal']};
    }}
    """)

    # Compact mode adjustments
    if breakpoint.compact_mode:
        css_rules.append("""
        .compact-hidden {
            display: none;
        }
        
        .compact-text {
            text-overflow: ellipsis;
            overflow: hidden;
        }
        
        DataTable {
            show-row-labels: false;
        }
        """)

    return "\n".join(css_rules)
