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
from functools import lru_cache
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
            name="xs",          # Extra small (mobile-like) - keep sidebar visible as requested
            min_width=0,
            min_height=0,
            sidebar_width=12,   # Minimal sidebar width for xs screens
            sidebar_visible=True,  # Keep sidebar visible as requested by user
            tabs_horizontal=False,
            compact_mode=True,
            header_height=1,
            footer_height=0,
            status_bar_height=1,
            compact_header=True,
            collapsible_sidebar=True,
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
        # Enhanced breakpoints for horizontal screens with optimized sidebar handling
        LayoutBreakpoint(
            name="horizontal_comfortable",  # Wide screens with moderate height constraints
            min_width=140,
            min_height=15,
            sidebar_width=18,  # Comfortable sidebar width
            sidebar_visible=True,
            tabs_horizontal=True,
            compact_mode=False,  # Can afford normal mode
            header_height=2,
            footer_height=1,
            status_bar_height=1,
            compact_header=False,
            collapsible_sidebar=True,
            priority_based_layout=False
        ),
        LayoutBreakpoint(
            name="horizontal_tight",  # Wide but short screens
            min_width=100,
            min_height=12,
            sidebar_width=15,  # Reduced width for horizontal screens
            sidebar_visible=True,  # Keep sidebar visible as requested
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
            sidebar_width=12,  # Minimal width for ultra tight screens
            sidebar_visible=True,  # Keep sidebar visible as requested
            tabs_horizontal=True,
            compact_mode=True,
            header_height=1,
            footer_height=0,
            status_bar_height=0,  # Hide status bar to save space
            compact_header=True,
            collapsible_sidebar=True,  # Allow collapsing if needed
            priority_based_layout=True
        ),
        LayoutBreakpoint(
            name="horizontal_micro",  # Extremely small height screens
            min_width=80,
            min_height=5,
            sidebar_width=10,  # Absolute minimum sidebar width
            sidebar_visible=True,  # Keep minimal sidebar
            tabs_horizontal=True,
            compact_mode=True,
            header_height=0,  # No header to save space
            footer_height=0,
            status_bar_height=0,
            compact_header=True,
            collapsible_sidebar=True,
            priority_based_layout=True
        ),
        LayoutBreakpoint(
            name="vertical_micro",  # Extremely small height for any width
            min_width=0,
            min_height=3,
            sidebar_width=8,  # Ultra minimal sidebar width
            sidebar_visible=True,  # Try to keep sidebar visible even in micro mode
            tabs_horizontal=False,
            compact_mode=True,
            header_height=0,  # No header
            footer_height=0,
            status_bar_height=0,
            compact_header=True,
            collapsible_sidebar=True,
            priority_based_layout=True
        ),
    ]

    def __init__(self, app: App) -> None:
        """Initialize the responsive layout manager."""
        self.app = app
        self.current_breakpoint: LayoutBreakpoint | None = None
        self._callbacks: list[Callable] = []
        self._cache_key: str = ""  # Cache invalidation key based on size and breakpoint
        self._last_update_time: float = 0.0  # Throttle rapid updates
        self._pending_update: bool = False  # Debounce updates

    def add_resize_callback(self, callback: Callable) -> None:
        """Add a callback to be called when layout changes."""
        self._callbacks.append(callback)

    def remove_resize_callback(self, callback: Callable) -> None:
        """Remove a resize callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def schedule_delayed_update(self, delay: float = 0.1) -> None:
        """Schedule a delayed layout update for better performance during rapid resizing."""
        if hasattr(self.app, 'set_timer'):
            self.app.set_timer(delay, self._process_delayed_update)

    def _process_delayed_update(self) -> None:
        """Process any pending delayed updates."""
        if self._pending_update:
            self._pending_update = False
            # Force a layout update
            self.update_layout(self.app.size)

    def get_current_breakpoint(self) -> LayoutBreakpoint:
        """Get the current breakpoint based on terminal size with height optimization."""
        size = self.app.size

        # Priority handling for extremely small heights (critical for usability)
        if size.height <= 3:
            return next(bp for bp in self.BREAKPOINTS if bp.name == "vertical_micro")
        elif size.height <= 5 and size.width >= 80:
            return next(bp for bp in self.BREAKPOINTS if bp.name == "horizontal_micro")

        # Enhanced handling for horizontal screens with optimized breakpoint selection
        if size.width >= 100 and size.height <= 20:  # Extended range for horizontal detection
            if size.height <= 8:
                return next(bp for bp in self.BREAKPOINTS if bp.name == "horizontal_ultra_tight")
            elif size.height <= 12:
                return next(bp for bp in self.BREAKPOINTS if bp.name == "horizontal_tight")
            elif size.height <= 15 and size.width >= 140:
                return next(bp for bp in self.BREAKPOINTS if bp.name == "horizontal_comfortable")
            # Fall through to regular breakpoint selection for other horizontal cases

        # Find the largest breakpoint that fits (excluding horizontal-specific ones)
        regular_breakpoints = [
            bp for bp in self.BREAKPOINTS if not bp.name.startswith("horizontal")]
        selected_breakpoint = regular_breakpoints[0]  # Default to smallest

        for breakpoint in reversed(regular_breakpoints):
            if size.width >= breakpoint.min_width and size.height >= breakpoint.min_height:
                selected_breakpoint = breakpoint
                break

        return selected_breakpoint

    def _invalidate_cache(self) -> None:
        """Invalidate cached layout calculations."""
        # Update cache key to invalidate all cached methods
        size = self.app.size
        breakpoint_name = self.current_breakpoint.name if self.current_breakpoint else "none"
        self._cache_key = f"{size.width}x{size.height}_{breakpoint_name}"

        # Clear method caches
        self._get_cached_sidebar_config.cache_clear()
        self._get_cached_content_config.cache_clear()
        self._get_cached_available_height.cache_clear()

    def update_layout(self, size: Size) -> bool:
        """Update layout based on new terminal size with performance optimizations."""
        import time

        current_time = time.time()

        # Throttle rapid updates (debounce within 50ms)
        if current_time - self._last_update_time < 0.05:
            self._pending_update = True
            return False

        # Process any pending update
        if self._pending_update:
            self._pending_update = False

        self._last_update_time = current_time

        new_breakpoint = self.get_current_breakpoint()

        # Quick size-only check before expensive breakpoint comparison
        if (self.current_breakpoint and
            new_breakpoint.name == self.current_breakpoint.name and
            abs(size.width - getattr(self, '_last_width', 0)) < 5 and
            abs(size.height - getattr(self, '_last_height', 0)) < 2):
            # Minor size change within same breakpoint - skip update
            return False

        if self.current_breakpoint is None or new_breakpoint.name != self.current_breakpoint.name:
            old_breakpoint = self.current_breakpoint
            self.current_breakpoint = new_breakpoint

            # Cache size for future comparisons
            self._last_width = size.width
            self._last_height = size.height

            # Invalidate caches when layout changes
            self._invalidate_cache()

            logger.info(
                f"Layout breakpoint changed: {old_breakpoint.name if old_breakpoint else 'None'} "
                f"-> {new_breakpoint.name} (size: {size.width}x{size.height})"
            )

            # Batch callback notifications to reduce overhead
            if self._callbacks:
                self._notify_callbacks_batch(old_breakpoint, new_breakpoint)

            return True

        return False

    def _notify_callbacks_batch(self, old_breakpoint: LayoutBreakpoint | None, new_breakpoint: LayoutBreakpoint) -> None:
        """Notify callbacks in batch with error isolation."""
        failed_callbacks = []

        for callback in self._callbacks:
            try:
                callback(old_breakpoint, new_breakpoint)
            except Exception as e:
                logger.error(f"Error in resize callback: {e}")
                failed_callbacks.append(callback)

        # Remove failed callbacks to prevent repeated errors
        for failed_callback in failed_callbacks:
            try:
                self._callbacks.remove(failed_callback)
                logger.warning(f"Removed failed callback: {failed_callback}")
            except ValueError:
                pass

    def _calculate_adaptive_sidebar_width(self) -> int:
        """Calculate optimal sidebar width based on available space and breakpoint."""
        if not self.current_breakpoint:
            return 20  # Default fallback

        available_width = self.app.size.width
        available_height = self.app.size.height
        base_width = self.current_breakpoint.sidebar_width

        # For horizontal screens, adapt width based on available space
        if self.current_breakpoint.name.startswith("horizontal"):
            # Ensure minimum content area width of 50 characters
            min_content_width = 50
            max_sidebar_width = max(10, available_width - min_content_width - 2)  # Account for borders

            # Scale sidebar width based on available width
            if available_width >= 150:
                # Wide horizontal screens can afford slightly larger sidebar
                optimal_width = min(18, max_sidebar_width)
            elif available_width >= 120:
                # Medium horizontal screens
                optimal_width = min(15, max_sidebar_width)
            else:
                # Narrow horizontal screens
                optimal_width = min(12, max_sidebar_width)

            return max(10, optimal_width)  # Minimum 10 characters for usability

        # For vertical screens, use standard logic with slight adaptations
        if available_width < 80:
            # Very narrow screens
            return max(12, min(base_width, available_width // 4))
        elif available_width < 120:
            # Narrow screens
            return max(15, min(base_width, available_width // 5))
        else:
            # Wide screens can use full base width
            return base_width

    @lru_cache(maxsize=32)
    def _get_cached_sidebar_config(self, cache_key: str, width: int, height: int, breakpoint_name: str) -> dict:
        """Cached sidebar configuration calculation."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        adaptive_width = self._calculate_adaptive_sidebar_width()

        return {
            "visible": self.current_breakpoint.sidebar_visible,
            "width": adaptive_width,
            "min_width": max(10, adaptive_width - 3),
            "max_width": min(50, adaptive_width + 5),
            "collapsible": self.current_breakpoint.collapsible_sidebar,
        }

    def get_sidebar_config(self) -> dict:
        """Get sidebar configuration for current breakpoint with adaptive width."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        size = self.app.size
        return self._get_cached_sidebar_config(
            self._cache_key, size.width, size.height, self.current_breakpoint.name
        )

    @lru_cache(maxsize=32)
    def _get_cached_content_config(self, cache_key: str, width: int, height: int, breakpoint_name: str) -> dict:
        """Cached content configuration calculation."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        sidebar_config = self.get_sidebar_config()
        available_width = width

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

    def get_content_config(self) -> dict:
        """Get main content area configuration for current breakpoint."""
        if not self.current_breakpoint:
            self.current_breakpoint = self.get_current_breakpoint()

        size = self.app.size
        return self._get_cached_content_config(
            self._cache_key, size.width, size.height, self.current_breakpoint.name
        )

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

    @lru_cache(maxsize=32)
    def _get_cached_available_height(self, cache_key: str, width: int, height: int, breakpoint_name: str) -> int:
        """Cached available content height calculation."""
        if not self.current_breakpoint:
            return max(10, height - 5)

        total_height = height
        used_height = (
            self.current_breakpoint.header_height +
            self.current_breakpoint.footer_height +
            self.current_breakpoint.status_bar_height +
            1  # Tab bar
        )

        return max(5, total_height - used_height)

    def _get_available_content_height(self) -> int:
        """Calculate available height for content after UI chrome."""
        if not self.current_breakpoint:
            return max(10, self.app.size.height - 5)

        size = self.app.size
        return self._get_cached_available_height(
            self._cache_key, size.width, size.height, self.current_breakpoint.name
        )

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

    def should_hide_component(self, component_name: str, priority: str = "medium", context: dict = None) -> bool:
        """Determine if a component should be hidden based on available space and intelligent context."""
        if not self.current_breakpoint:
            return False

        # Skip priority-based hiding if not enabled
        if not self.current_breakpoint.priority_based_layout:
            return False

        available_height = self._get_available_content_height()
        available_width = self.app.size.width

        # Get component-specific context
        context = context or {}

        # Enhanced priority-based hiding with context awareness
        priority_thresholds = self._get_priority_thresholds(available_height, available_width)

        # Check if component should be hidden based on priority
        if priority in priority_thresholds:
            threshold = priority_thresholds[priority]
            if available_height < threshold["height"] or available_width < threshold.get("width", 0):
                return True

        # Component-specific intelligent hiding
        return self._should_hide_component_intelligent(component_name, available_height, available_width, context)

    def _get_priority_thresholds(self, height: int, width: int) -> dict:
        """Get dynamic priority thresholds based on available space."""
        # Base thresholds
        thresholds = {
            "low": {"height": 15, "width": 80},
            "medium": {"height": 10, "width": 60},
            "high": {"height": 6, "width": 40}
        }

        # Adjust thresholds for micro heights
        if height <= 3:
            # Extremely aggressive hiding for micro heights
            thresholds = {
                "low": {"height": 3, "width": 40},
                "medium": {"height": 2, "width": 30},
                "high": {"height": 1, "width": 20}
            }
        elif height <= 5:
            # Very aggressive hiding for extremely small heights
            thresholds = {
                "low": {"height": 5, "width": 50},
                "medium": {"height": 4, "width": 40},
                "high": {"height": 3, "width": 30}
            }
        elif self.current_breakpoint and self.current_breakpoint.name.startswith("horizontal"):
            # More aggressive hiding on horizontal screens due to height constraints
            thresholds["low"]["height"] = 12
            thresholds["medium"]["height"] = 8
            thresholds["high"]["height"] = 5

            # Less strict width requirements on horizontal screens
            for priority in thresholds:
                thresholds[priority]["width"] = max(40, thresholds[priority]["width"] - 20)

        return thresholds

    def _should_hide_component_intelligent(self, component_name: str, height: int, width: int, context: dict) -> bool:
        """Intelligent component-specific hiding logic."""
        # Search component - hide if very limited space or no query
        if component_name == "search":
            if height < 12 or width < 70:
                return True
            # Hide if no recent search activity (could be tracked in context)
            if context.get("search_activity", 0) == 0 and height < 15:
                return True

        # Settings component - hide unless explicitly needed
        elif component_name == "settings":
            if height < 20 or width < 100:
                return True
            # Hide if not recently accessed
            if not context.get("settings_accessed", False) and height < 25:
                return True

        # Actions component - context-aware hiding
        elif component_name == "actions":
            # Hide if no repositories or very limited space
            if context.get("repository_count", 0) == 0 and height < 15:
                return True
            if height < 8 or width < 60:
                return True

        # Notifications - hide if no unread notifications and space is limited
        elif component_name == "notifications":
            unread_count = context.get("unread_notifications", 0)
            if unread_count == 0 and height < 12:
                return True
            if height < 6 or width < 50:
                return True

        return False

    def _get_component_space_requirements(self, component: str, priority: str, context: dict) -> dict:
        """Get space requirements for a specific component with micro-height support."""
        # Base requirements by component type
        requirements = {
            "repositories": {"height": 8, "width": 60, "compact_height": 6, "micro_height": 3},
            "pull_requests": {"height": 8, "width": 70, "compact_height": 6, "micro_height": 3},
            "issues": {"height": 8, "width": 65, "compact_height": 6, "micro_height": 3},
            "notifications": {"height": 6, "width": 55, "compact_height": 4, "micro_height": 2},
            "actions": {"height": 7, "width": 80, "compact_height": 5, "micro_height": 3},
            "search": {"height": 5, "width": 50, "compact_height": 3, "micro_height": 2},
            "settings": {"height": 6, "width": 60, "compact_height": 4, "micro_height": 2},
            "dashboard": {"height": 10, "width": 80, "compact_height": 7, "micro_height": 3},
        }

        base_req = requirements.get(component, {"height": 6, "width": 50, "compact_height": 4, "micro_height": 2})
        available_height = self._get_available_content_height()

        # Select appropriate height based on available space
        if available_height <= 3:
            # Micro height mode
            base_req["height"] = base_req.get("micro_height", 2)
            base_req["compact_height"] = base_req["height"]
        elif available_height <= 5:
            # Extremely tight mode
            base_req["height"] = max(2, base_req.get("micro_height", 2))
            base_req["compact_height"] = base_req["height"]
        elif self.current_breakpoint and (self.current_breakpoint.name.startswith("horizontal") or "micro" in self.current_breakpoint.name):
            # Horizontal or micro screens
            base_req["height"] = max(2, base_req["height"] - 2)
            base_req["compact_height"] = max(1, base_req.get("compact_height", base_req["height"]) - 1)

        # Context-based adjustments
        if component == "notifications":
            unread_count = context.get("unread_notifications", 0)
            if unread_count > 10 and available_height > 5:
                base_req["height"] += min(2, available_height - 5)  # Add space for many notifications

        return base_req

    def get_micro_layout_config(self) -> dict:
        """Get configuration for micro layouts with minimal UI elements."""
        if not self.current_breakpoint:
            return {}

        available_height = self._get_available_content_height()

        return {
            "show_header": available_height > 5,
            "show_footer": available_height > 8,
            "show_status_bar": available_height > 10,
            "show_tabs": available_height > 3,
            "show_borders": available_height > 5,
            "compact_buttons": available_height <= 8,
            "minimal_padding": available_height <= 6,
            "single_line_items": available_height <= 5,
            "hide_icons": available_height <= 4,
            "ultra_compact": available_height <= 3,
        }

    def get_component_priorities(self, context: dict = None) -> dict[str, str]:
        """Get dynamic component priorities for layout optimization with context awareness."""
        context = context or {}

        # Base priorities
        priorities = {
            "repositories": "high",
            "pull_requests": "high",
            "issues": "high",
            "actions": "medium",
            "notifications": "medium",
            "search": "low",
            "settings": "low",
            "dashboard": "medium",
        }

        # Dynamic priority adjustments based on context

        # Boost notifications priority if there are unread items
        unread_notifications = context.get("unread_notifications", 0)
        if unread_notifications > 0:
            priorities["notifications"] = "high"
        elif unread_notifications == 0:
            priorities["notifications"] = "low"

        # Boost actions priority if user has many repositories
        repository_count = context.get("repository_count", 0)
        if repository_count > 10:
            priorities["actions"] = "high"
        elif repository_count == 0:
            priorities["actions"] = "low"

        # Boost search priority if recently used
        if context.get("search_activity", 0) > 0:
            priorities["search"] = "medium"

        # Boost settings priority if configuration needed
        if context.get("needs_configuration", False):
            priorities["settings"] = "high"

        # Adjust for horizontal screens - prioritize core functionality
        if self.current_breakpoint and self.current_breakpoint.name.startswith("horizontal"):
            # On horizontal screens, prioritize data over configuration
            priorities["repositories"] = "high"
            priorities["pull_requests"] = "high"
            priorities["issues"] = "high"
            priorities["notifications"] = "medium" if unread_notifications > 0 else "low"
            priorities["search"] = "low"
            priorities["settings"] = "low"
            priorities["actions"] = "medium" if repository_count > 0 else "low"

        return priorities

    def optimize_layout_for_height(self, components: list[str], context: dict = None) -> list[str]:
        """Optimize component layout for height constraints with intelligent prioritization."""
        if not self.current_breakpoint or not self.current_breakpoint.priority_based_layout:
            return components

        context = context or {}
        priorities = self.get_component_priorities(context)
        available_height = self._get_available_content_height()

        # Sort components by priority with intelligent weighting
        def get_priority_score(component: str) -> float:
            base_score = {"high": 3.0, "medium": 2.0, "low": 1.0}.get(
                priorities.get(component, "medium"), 2.0)

            # Apply context-based adjustments
            if component == "notifications" and context.get("unread_notifications", 0) > 5:
                base_score += 0.5  # Boost for many unread notifications
            elif component == "repositories" and context.get("repository_count", 0) > 20:
                base_score += 0.3  # Boost for power users
            elif component == "search" and context.get("search_activity", 0) > 0:
                base_score += 0.2  # Boost for active searchers

            return base_score

        prioritized_components = sorted(components, key=get_priority_score, reverse=True)

        # Enhanced filtering with context awareness and micro-height support
        if available_height <= 3:
            # Micro height - only the most essential component
            essential_components = ["repositories", "dashboard"]
            for comp in essential_components:
                if comp in prioritized_components:
                    return [comp]
            return prioritized_components[:1] if prioritized_components else []
        elif available_height <= 5:
            # Extremely tight - only one critical component
            critical_components = [c for c in prioritized_components
                                 if priorities.get(c, "medium") == "high" and
                                 not self.should_hide_component(c, "high", context)]
            return critical_components[:1]  # Maximum 1 component
        elif available_height < 8:
            # Ultra tight - maximum 2 critical components
            critical_components = [c for c in prioritized_components
                                 if priorities.get(c, "medium") == "high" and
                                 not self.should_hide_component(c, "high", context)]
            return critical_components[:2]  # Maximum 2 components
        elif available_height < 12:
            # Very tight - high priority only
            return [c for c in prioritized_components
                   if priorities.get(c, "medium") == "high" and
                   not self.should_hide_component(c, "high", context)]
        elif available_height < 18:
            # Tight - high and important medium priority
            visible = []
            for c in prioritized_components:
                if priorities.get(c, "medium") in ["high", "medium"] and \
                   not self.should_hide_component(c, priorities.get(c, "medium"), context):
                    visible.append(c)
                    if len(visible) >= 4:  # Limit to 4 components
                        break
            return visible
        else:
            # Normal - show all that fit
            return [c for c in prioritized_components
                   if not self.should_hide_component(c, priorities.get(c, "medium"), context)]

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
