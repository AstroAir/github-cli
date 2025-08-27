from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Any, ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button, Checkbox, Collapsible, ContentSwitcher, DataTable, Digits, DirectoryTree,
    Footer, Header, Input, Label, Link, ListView, LoadingIndicator, Log, MarkdownViewer,
    OptionList, Placeholder, Pretty, ProgressBar, RadioButton, RadioSet, RichLog, Rule,
    SelectionList, Sparkline, Static, TabbedContent, TabPane, TextArea, Tree
)
from loguru import logger

from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError, AuthenticationError
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager, get_responsive_styles
from github_cli.ui.tui.screens.error import TUIErrorHandler
from github_cli.ui.auth.responsive_layout import ResponsiveAuthLayout, AuthLayoutConfig
from github_cli.auth.error_handler import AuthErrorHandler, AuthResult
from github_cli.auth.progress_tracker import AuthProgressTracker, AuthStep
from github_cli.ui.tui.screens.auth import AuthScreen
from github_cli.ui.tui.screens.help import HelpScreen


class StatusBar(Static):
    """Enhanced status bar with real-time information and responsive design."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    """

    user_info: reactive[str] = reactive("Not authenticated")
    rate_limit: reactive[str] = reactive("Rate limit: Unknown")
    connection_status: reactive[str] = reactive("Disconnected")
    terminal_size: reactive[str] = reactive("")

    def __init__(self, layout_manager: ResponsiveLayoutManager) -> None:
        super().__init__()
        self.layout_manager = layout_manager
        self.layout_manager.add_resize_callback(self._on_layout_change)

    def render(self) -> str:
        """Render the status bar with current information, adapting to terminal size."""
        breakpoint = self.layout_manager.current_breakpoint
        status_config = self.layout_manager.get_status_bar_config()

        if not breakpoint or not status_config["visible"]:
            return ""

        if status_config["compact"] or breakpoint.name.startswith("horizontal"):
            # Ultra compact status bar for horizontal tight layouts
            if breakpoint.name == "horizontal_ultra_tight":
                return f"{self.user_info.split()[0] if self.user_info else 'N/A'} | {self.connection_status.split()[0] if self.connection_status else 'N/A'}"
            # Compact status bar for small screens
            return f"{self.user_info} | {self.connection_status}"
        else:
            # Full status bar for larger screens
            return f"{self.user_info} | {self.rate_limit} | {self.connection_status} | {self.terminal_size}"

    def _on_layout_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
        """Handle layout changes."""
        self.terminal_size = f"📐 {self.layout_manager.app.size.width}×{self.layout_manager.app.size.height} ({new_breakpoint.name})"
        self.refresh()

    def update_user_info(self, username: str | None) -> None:
        """Update user information display."""
        self.user_info = f"👤 {username}" if username else "Not authenticated"

    def update_rate_limit(self, remaining: int, limit: int) -> None:
        """Update rate limit display."""
        percentage = (remaining / limit * 100) if limit > 0 else 0
        self.rate_limit = f"🔥 API: {remaining}/{limit} ({percentage:.0f}%)"

    def update_connection_status(self, connected: bool) -> None:
        """Update connection status display."""
        self.connection_status = "🟢 Connected" if connected else "🔴 Disconnected"


class GitHubTUIApp(App[None]):
    """Modern GitHub CLI TUI application with comprehensive functionality and responsive design."""

    TITLE = "GitHub CLI - Terminal User Interface"
    SUB_TITLE = "Advanced GitHub management in your terminal"

    # External CSS file for styling
    CSS_PATH = str(Path(__file__).parent.parent / "github_tui.tcss")

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+c,q", "quit", "Quit", priority=True),
        Binding("ctrl+n", "new_tab", "New Tab"),
        Binding("ctrl+w", "close_tab", "Close Tab"),
        Binding("ctrl+t", "toggle_tree", "Toggle Tree"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+s", "search", "Search"),
        Binding("ctrl+l", "login", "Login"),
        Binding("ctrl+o", "logout", "Logout"),
        Binding("f1", "help", "Help"),
        Binding("f5", "refresh_all", "Refresh All"),
        Binding("ctrl+alt+r", "toggle_responsive_debug",
                "Toggle Responsive Debug"),
    ]

    # Reactive attributes for state management
    authenticated: reactive[bool] = reactive(False)
    current_user: reactive[str | None] = reactive(None)
    loading: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()

        # Initialize responsive layout manager
        self.layout_manager = ResponsiveLayoutManager(self)

        # Initialize GitHub CLI components
        self.config = Config()
        self.authenticator = Authenticator(self.config)
        self.client: GitHubClient | None = None
        self.status_bar: StatusBar | None = None

        # Initialize error handler
        self.error_handler = TUIErrorHandler(self)

        # Initialize data loader for preemptive loading
        self.data_loader = None  # Will be initialized after client is ready

        # Layout state
        self._current_layout_config = None
        self._sidebar_visible = True

        logger.info("GitHub TUI application initialized with responsive layout")

    async def on_mount(self) -> None:
        """Called when the app is mounted with progressive loading."""
        logger.info("GitHub TUI application mounted - starting progressive initialization")

        # Phase 1: Immediate UI setup (show loading state)
        self.loading = True
        self.notify("Initializing GitHub CLI...", timeout=1)

        # Phase 2: Initialize responsive layout (optimized)
        logger.debug("Phase 1: Setting up responsive layout")
        # Batch layout initialization to avoid multiple updates
        self._initialize_responsive_layout()

        # Phase 3: Initialize GitHub client (medium speed)
        logger.debug("Phase 2: Initializing GitHub client")
        self.client = GitHubClient(self.authenticator)

        # Initialize data loader with client
        from github_cli.ui.tui.utils.data_loader import create_data_loader
        self.data_loader = create_data_loader(self.client, self.error_handler, cache_ttl_minutes=10)

        # Update loading state
        self.notify("Checking authentication...", timeout=1)

        # Phase 4: Check authentication status (potentially slow)
        logger.debug("Phase 3: Checking authentication")
        await self._check_authentication()

        # Phase 5: Start background tasks (fast)
        logger.debug("Phase 4: Starting background services")
        self._start_background_tasks()

        # Phase 6: Preload initial data if authenticated
        if self.authenticated:
            logger.debug("Phase 5: Preloading initial data")
            self.notify("Loading initial data...", timeout=1)
            await self._preload_initial_data()

        # Initialization complete
        self.loading = False
        self.notify("GitHub CLI ready!", severity="information", timeout=2)
        logger.info("GitHub TUI application initialization complete")

    def _initialize_responsive_layout(self) -> None:
        """Initialize responsive layout with optimized batch operations."""
        try:
            # Single layout update with callback registration
            layout_changed = self.layout_manager.update_layout(self.size)
            self.layout_manager.add_resize_callback(self._on_responsive_layout_change)

            # Pre-calculate and cache layout configurations
            breakpoint = self.layout_manager.get_current_breakpoint()

            # Cache frequently accessed configurations
            self.layout_manager.get_sidebar_config()
            self.layout_manager.get_content_config()
            self.layout_manager.get_header_config()
            self.layout_manager.get_footer_config()

            logger.debug(f"Responsive layout initialized with breakpoint: {breakpoint.name}")

        except Exception as e:
            logger.error(f"Error initializing responsive layout: {e}")
            # Fallback to basic initialization
            self.layout_manager.update_layout(self.size)
            self.layout_manager.add_resize_callback(self._on_responsive_layout_change)

    async def on_resize(self, event: Any) -> None:
        """Handle terminal resize events with optimized updates."""
        # Only update if layout actually changed
        layout_changed = self.layout_manager.update_layout(event.size)
        if layout_changed:
            await self._update_responsive_layout()

    def compose(self) -> ComposeResult:
        """Create the main UI layout with responsive design."""
        header_config = self.layout_manager.get_header_config()
        footer_config = self.layout_manager.get_footer_config()
        status_bar_config = self.layout_manager.get_status_bar_config()

        # Conditionally yield header with responsive classes
        if header_config["visible"]:
            header = Header()
            if header_config["compact"]:
                header.add_class("compact")
            if header_config["height"] == 1:
                header.add_class("ultra-compact")
            yield header

        with Container(id="main-container", classes="adaptive-container"):
            # Use responsive layout configuration
            layout_config = self.layout_manager.get_current_breakpoint()
            sidebar_config = self.layout_manager.get_sidebar_config()

            if self.layout_manager.should_use_vertical_layout():
                # Vertical layout for small screens
                yield from self._compose_vertical_layout()
            else:
                # Horizontal layout for larger screens
                yield from self._compose_horizontal_layout()

            # Modern loading overlay
            yield LoadingIndicator(id="loading-overlay")

        # Status bar with layout manager (conditionally visible)
        if status_bar_config["visible"]:
            self.status_bar = StatusBar(self.layout_manager)
            if status_bar_config["compact"]:
                self.status_bar.add_class("compact")
            yield self.status_bar

        # Conditionally yield footer with responsive classes
        if footer_config["visible"]:
            footer = Footer()
            yield footer
        else:
            # Add hidden class to indicate footer is hidden
            footer = Footer()
            footer.add_class("hidden")
            yield footer

    def _get_prioritized_sidebar_content(self) -> list[tuple[str, int, Any]]:
        """Get sidebar content items with priority levels for adaptive display.

        Returns list of tuples: (item_type, priority, content_data)
        Priority levels: 1=highest, 5=lowest
        """
        breakpoint = self.layout_manager.get_current_breakpoint()
        available_height = self.layout_manager._get_available_content_height()

        # Define sidebar content with priorities based on available height
        if available_height <= 3:
            # Micro height - only essential navigation
            content_items = [
                ("tree", 1, {"label": "CLI", "id": "nav-tree"}),  # Ultra compact label
            ]
        elif available_height <= 5:
            # Extremely tight - navigation and auth only
            content_items = [
                ("tree", 1, {"label": "GitHub", "id": "nav-tree"}),  # Compact label
                ("auth_button", 2, None),  # Login/logout - essential
            ]
        else:
            # Normal content with adaptive priorities
            content_items = [
                ("tree", 1, {"label": "GitHub CLI", "id": "nav-tree"}),  # Always show navigation
                ("auth_button", 2, None),  # Login/logout - high priority
                ("separator", 4, {"style": "heavy"}) if available_height > 8 else None,  # Skip separator on very tight screens
                ("refresh_button", 3, {"label": "🔄 Refresh", "id": "refresh-btn"}),  # Refresh functionality
            ]

        # Filter out None items and adjust for horizontal screens
        filtered_items = [item for item in content_items if item is not None]

        # For horizontal and micro screens, prioritize more compact content
        if breakpoint and (breakpoint.name.startswith("horizontal") or "micro" in breakpoint.name):
            # Use more compact labels and reduce separators
            for i, (item_type, priority, data) in enumerate(filtered_items):
                if item_type == "refresh_button" and data:
                    # Use compact refresh button for constrained screens
                    filtered_items[i] = (item_type, priority, {"label": "🔄", "id": "refresh-btn"})
                elif item_type == "tree" and data and available_height <= 5:
                    # Use ultra compact tree label for micro heights
                    filtered_items[i] = (item_type, priority, {"label": "GH", "id": "nav-tree"})

        return filtered_items

    def _compose_adaptive_sidebar_content(self) -> ComposeResult:
        """Compose sidebar content based on available space and priorities."""
        sidebar_config = self.layout_manager.get_sidebar_config()
        breakpoint = self.layout_manager.get_current_breakpoint()
        available_height = self.layout_manager._get_available_content_height()

        # Get prioritized content
        content_items = self._get_prioritized_sidebar_content()

        # Determine how many items we can fit based on height constraints
        if available_height <= 3:
            max_items = 1  # Micro height - only one item
        elif available_height <= 5:
            max_items = 2  # Extremely tight - maximum 2 items
        else:
            max_items = available_height - 2  # Reserve space for container padding
            if breakpoint and breakpoint.name.startswith("horizontal_ultra"):
                max_items = min(max_items, 4)  # Limit items on ultra tight screens
            elif breakpoint and "micro" in breakpoint.name:
                max_items = min(max_items, 2)  # Limit items on micro screens

        # Sort by priority and take top items
        sorted_items = sorted(content_items, key=lambda x: x[1])[:max_items]

        # Render items with height-aware styling
        for item_type, priority, data in sorted_items:
            if item_type == "tree" and data:
                yield Tree(data["label"], id=data["id"])
            elif item_type == "separator":
                if data and available_height > 6:  # Only show separators if we have space
                    yield Rule(line_style=data.get("style", "solid"))
            elif item_type == "auth_button":
                # Show appropriate auth button based on state and available space
                if available_height <= 5:
                    # Ultra compact auth buttons for micro heights
                    if self.authenticated:
                        yield Button("⚪", id="logout-btn", variant="error")
                    else:
                        yield Button("🔐", id="login-btn", variant="primary")
                else:
                    # Normal auth buttons
                    if self.authenticated:
                        yield Button("🚪 Logout", id="logout-btn", variant="error")
                    else:
                        yield Button("🔐 Login", id="login-btn", variant="primary")
            elif item_type == "refresh_button" and data:
                yield Button(data["label"], id=data["id"])

    def _compose_horizontal_layout(self) -> ComposeResult:
        """Compose horizontal layout for larger screens."""
        sidebar_config = self.layout_manager.get_sidebar_config()
        breakpoint = self.layout_manager.get_current_breakpoint()

        with Horizontal(id="content-area"):
            # Sidebar navigation (always visible when configured, including horizontal screens)
            if sidebar_config["visible"]:
                with Vertical(id="sidebar", classes="sidebar adaptive-sidebar"):
                    yield from self._compose_adaptive_sidebar_content()

            # Main content area with responsive tabs
            yield from self._compose_main_content()

    def _compose_vertical_layout(self) -> ComposeResult:
        """Compose vertical layout for small screens."""
        breakpoint = self.layout_manager.get_current_breakpoint()

        with Vertical(id="content-area-vertical"):
            # Compact navigation bar for small screens
            if breakpoint.name not in ["horizontal_ultra_tight"]:
                with Horizontal(id="compact-nav", classes="compact-nav"):
                    yield Button("🔐", id="login-btn", variant="primary")
                    yield Button("🚪", id="logout-btn", variant="error")
                    yield Button("🔄", id="refresh-btn")
                    if breakpoint.name not in ["horizontal_tight", "xs"]:
                        yield Button("📱", id="menu-btn", variant="default")

            # Main content area
            yield from self._compose_main_content()

    def _compose_main_content(self) -> ComposeResult:
        """Compose the main content area with responsive tabs."""
        content_config = self.layout_manager.get_content_config()

        # Define all available components
        all_components = [
            "dashboard", "repositories", "pull_requests", "actions",
            "notifications", "search", "settings"
        ]

        # Optimize layout based on height constraints
        if content_config.get("priority_based_layout", False):
            visible_components = self.layout_manager.optimize_layout_for_height(
                all_components)
        else:
            visible_components = all_components

        # Limit tabs based on available width
        max_tabs = content_config.get("max_tab_count", 6)
        if len(visible_components) > max_tabs:
            visible_components = visible_components[:max_tabs]

        with TabbedContent(id="main-tabs", classes="responsive-tabs"):
            if "dashboard" in visible_components:
                with TabPane("Dashboard", id="dashboard-tab"):
                    yield Placeholder("Dashboard content will go here", id="dashboard")

            if "repositories" in visible_components:
                with TabPane("Repos", id="repos-tab"):
                    if self.client:
                        from github_cli.ui.tui.screens.repository import create_repository_widget
                        yield create_repository_widget(self.client, self.layout_manager)
                    else:
                        yield Placeholder("Please login to GitHub first", id="repos-placeholder")

            if "pull_requests" in visible_components:
                with TabPane("PRs", id="prs-tab"):
                    from github_cli.ui.tui.screens.pull_request import create_pull_request_widget
                    if self.client:
                        yield create_pull_request_widget(self.client, self.layout_manager)
                    else:
                        yield Placeholder("Please login to GitHub first", id="prs-placeholder")

            if "actions" in visible_components:
                with TabPane("Actions", id="actions-tab"):
                    from github_cli.ui.tui.screens.actions import create_actions_widget
                    if self.client:
                        yield create_actions_widget(self.client, self.layout_manager)
                    else:
                        yield Placeholder("Please login to GitHub first", id="actions-placeholder")

            if "notifications" in visible_components:
                with TabPane("Notifs", id="notifications-tab"):
                    from github_cli.ui.tui.screens.notification import create_notification_widget
                    if self.client:
                        yield create_notification_widget(self.client, self.layout_manager)
                    else:
                        yield Placeholder("Please login to GitHub first", id="notifications-placeholder")

            if "search" in visible_components:
                with TabPane("Search", id="search-tab"):
                    from github_cli.ui.tui.screens.search import create_search_widget
                    if self.client:
                        yield create_search_widget(self.client, self.layout_manager)
                    else:
                        yield Placeholder("Please login to GitHub first", id="search-placeholder")

            if "settings" in visible_components:
                with TabPane("Settings", id="settings-tab"):
                    from github_cli.ui.tui.core.settings import create_settings_widget
                    yield create_settings_widget(self.config, self.layout_manager)

    async def _check_authentication(self) -> None:
        """Check and update authentication status."""
        try:
            authenticated = self.authenticator.is_authenticated()

            if authenticated:
                user_info = await self.authenticator.fetch_user_info()
                if user_info:
                    # Update authentication state
                    self.authenticated = True
                    self.current_user = user_info.login
                    logger.info(f"Authenticated as {user_info.login}")

                    # Update status bar
                    if self.status_bar:
                        self.status_bar.update_user_info(user_info.login)
                        self.status_bar.update_connection_status(True)

                    # Initialize GitHub client with authenticated state
                    if not self.client:
                        self.client = GitHubClient(self.authenticator)

                    # Update button visibility
                    self._update_auth_button_visibility(True)
                else:
                    # Token exists but user info fetch failed - possibly expired token
                    logger.warning(
                        "Token exists but user info fetch failed - token may be expired")
                    self._handle_authentication_failure()
            else:
                # Not authenticated
                self._handle_authentication_failure()

        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            self._handle_authentication_failure()

    def _handle_authentication_failure(self) -> None:
        """Handle authentication failure by updating UI state."""
        self.authenticated = False
        self.current_user = None

        if self.status_bar:
            self.status_bar.update_user_info(None)
            self.status_bar.update_connection_status(False)

        # Update button visibility
        self._update_auth_button_visibility(False)

        # Clear GitHub client
        self.client = None

    def _update_auth_button_visibility(self, authenticated: bool) -> None:
        """Update authentication button visibility based on auth state."""
        try:
            login_btn = self.query_one("#login-btn", Button)
            logout_btn = self.query_one("#logout-btn", Button)

            if authenticated:
                login_btn.display = False
                logout_btn.display = True
            else:
                login_btn.display = True
                logout_btn.display = False
        except Exception as e:
            logger.debug(f"Could not update button visibility: {e}")
            # Buttons might not be mounted yet or layout might not have them

    async def _preload_initial_data(self) -> None:
        """Preload initial data for faster user experience using DataLoader."""
        if not self.client or not self.authenticated or not self.data_loader:
            return

        try:
            # Start preloading in background without blocking UI
            logger.debug("Starting strategic background data preload")

            # Phase 1: Critical data (immediate)
            self.set_timer(0.1, self._preload_critical_data)

            # Phase 2: Commonly accessed data (short delay)
            self.set_timer(0.5, self._preload_common_data)

            # Phase 3: Nice-to-have data (longer delay)
            self.set_timer(2.0, self._preload_supplementary_data)

            # Start background refresh for critical data
            self._start_background_refresh()

        except Exception as e:
            logger.warning(f"Error during data preload setup: {e}")
            # Don't fail initialization if preload fails

    @work(exclusive=False)
    async def _preload_critical_data(self) -> None:
        """Preload critical data that users access immediately."""
        if not self.data_loader or not self.authenticated:
            return

        try:
            # User info (for header display)
            await self.data_loader.load(
                "user_info",
                self.client.get_user_info,
                use_cache=True
            )

            # Rate limit info (for status display)
            await self.data_loader.load(
                "rate_limit",
                self._get_rate_limit_info,
                use_cache=True
            )

            logger.debug("Critical data preloaded successfully")
        except Exception as e:
            logger.debug(f"Critical data preload failed: {e}")

    @work(exclusive=False)
    async def _preload_common_data(self) -> None:
        """Preload commonly accessed data."""
        if not self.data_loader or not self.authenticated:
            return

        try:
            # User repositories (most commonly accessed)
            await self.data_loader.load(
                "user_repositories",
                self.client.get_user_repositories,
                type="all",
                sort="updated",
                per_page=20,
                use_cache=True
            )

            # Recent notifications (frequently checked)
            await self.data_loader.load(
                "notifications",
                self.client.get_notifications,
                per_page=10,
                use_cache=True
            )

            logger.debug("Common data preloaded successfully")
        except Exception as e:
            logger.debug(f"Common data preload failed: {e}")

    @work(exclusive=False)
    async def _preload_supplementary_data(self) -> None:
        """Preload supplementary data for enhanced experience."""
        if not self.data_loader or not self.authenticated:
            return

        try:
            # Recent pull requests
            await self.data_loader.load(
                "user_pull_requests",
                self.client.search_pull_requests,
                query="author:@me",
                per_page=10,
                use_cache=True
            )

            # Recent issues
            await self.data_loader.load(
                "user_issues",
                self.client.search_issues,
                query="author:@me",
                per_page=10,
                use_cache=True
            )

            logger.debug("Supplementary data preloaded successfully")
        except Exception as e:
            logger.debug(f"Supplementary data preload failed: {e}")

    def _start_background_refresh(self) -> None:
        """Start background refresh for critical data."""
        if not self.data_loader:
            return

        try:
            # Refresh notifications every 2 minutes
            self.data_loader.start_background_refresh(
                "notifications",
                self.client.get_notifications,
                per_page=10,
                interval=timedelta(minutes=2)
            )

            # Refresh rate limit every 5 minutes
            self.data_loader.start_background_refresh(
                "rate_limit",
                self._get_rate_limit_info,
                interval=timedelta(minutes=5)
            )

            logger.debug("Background refresh started for critical data")
        except Exception as e:
            logger.debug(f"Background refresh setup failed: {e}")

    async def _get_rate_limit_info(self) -> dict:
        """Get current rate limit information."""
        if not self.client:
            return {"remaining": 0, "limit": 5000, "reset": 0}

        try:
            response = await self.client.get("/rate_limit")
            if hasattr(response, 'data') and 'rate' in response.data:
                return response.data['rate']
            return {"remaining": 0, "limit": 5000, "reset": 0}
        except Exception:
            return {"remaining": 0, "limit": 5000, "reset": 0}

    def _start_background_tasks(self) -> None:
        """Start background tasks for periodic updates."""
        # Start rate limit monitoring
        self.set_interval(30.0, self._update_rate_limit)

        # Start authentication check
        self.set_interval(60.0, self._check_authentication)

        logger.debug("Background tasks started")

    @work(exclusive=True)
    async def _update_rate_limit(self) -> None:
        """Update rate limit information periodically."""
        if self.client and self.authenticated:
            try:
                # The rate limit info is updated automatically in the client
                remaining = self.client.rate_limit_remaining
                reset_time = self.client.rate_limit_reset

                if self.status_bar and remaining is not None:
                    self.status_bar.update_rate_limit(
                        remaining, 5000)  # GitHub's default limit

            except Exception as e:
                logger.warning(f"Failed to update rate limit: {e}")

    async def _update_responsive_layout(self) -> None:
        """Update the layout based on current responsive configuration."""
        try:
            breakpoint = self.layout_manager.get_current_breakpoint()

            # Update main container classes (optimized)
            try:
                main_container = self.query_one("#main-container")
                # More efficient class management - batch update
                current_classes = set(main_container.classes)
                breakpoint_classes = {"xs", "sm", "md", "lg", "xl", "horizontal_comfortable", "horizontal_tight", "horizontal_ultra_tight", "horizontal_micro", "vertical_micro"}

                # Only update if classes actually changed
                new_classes = (current_classes - breakpoint_classes) | {breakpoint.name}
                if new_classes != current_classes:
                    main_container.set_classes(" ".join(new_classes))
                    logger.debug(f"Updated container classes for breakpoint: {breakpoint.name}")
            except Exception as e:
                logger.debug(f"Could not update main container classes: {e}")

            # Update header classes
            try:
                header = self.query_one("Header")
                header_config = self.layout_manager.get_header_config()

                if header_config["compact"]:
                    header.add_class("compact")
                else:
                    header.remove_class("compact")

                if header_config["height"] == 1:
                    header.add_class("ultra-compact")
                else:
                    header.remove_class("ultra-compact")
            except Exception:
                pass

            # Update footer visibility
            try:
                footer = self.query_one("Footer")
                footer_config = self.layout_manager.get_footer_config()

                if footer_config["visible"]:
                    footer.remove_class("hidden")
                    footer.display = True
                else:
                    footer.add_class("hidden")
                    footer.display = False
            except Exception:
                pass

            # Apply responsive CSS styles
            responsive_css = get_responsive_styles(self.layout_manager)

            # Update sidebar visibility
            sidebar_config = self.layout_manager.get_sidebar_config()
            try:
                sidebar = self.query_one("#sidebar")
                if sidebar:
                    sidebar.display = sidebar_config["visible"]
            except Exception:
                pass

            # Update content area based on layout
            if self.layout_manager.should_use_vertical_layout():
                await self._switch_to_vertical_layout()
            else:
                await self._switch_to_horizontal_layout()

        except Exception as e:
            logger.error(f"Error updating responsive layout: {e}")

    async def _switch_to_vertical_layout(self) -> None:
        """Switch to vertical layout for small screens."""
        # Implementation would depend on dynamic layout switching capabilities
        # For now, we'll just log the change
        logger.info("Switching to vertical layout")

    async def _switch_to_horizontal_layout(self) -> None:
        """Switch to horizontal layout for larger screens."""
        # Implementation would depend on dynamic layout switching capabilities
        # For now, we'll just log the change
        logger.info("Switching to horizontal layout")

    def _on_responsive_layout_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
        """Handle responsive layout changes with smooth transitions."""
        logger.info(
            f"Layout changed from {old_breakpoint.name if old_breakpoint else 'None'} to {new_breakpoint.name}")

        # Start transition animation
        self._start_layout_transition()

        # Schedule layout update with transition support
        self.call_after_refresh(self._update_responsive_layout_with_transition)

        # Update status bar
        if self.status_bar:
            self.status_bar.refresh()

        # Provide user feedback for significant layout changes
        if old_breakpoint and new_breakpoint:
            if old_breakpoint.name.startswith("horizontal") != new_breakpoint.name.startswith("horizontal"):
                # Major layout change - notify user
                layout_type = "horizontal" if new_breakpoint.name.startswith("horizontal") else "vertical"
                self.notify(f"Layout optimized for {layout_type} display", timeout=2)
            elif old_breakpoint.sidebar_visible != new_breakpoint.sidebar_visible:
                # Sidebar visibility change
                sidebar_state = "shown" if new_breakpoint.sidebar_visible else "hidden"
                self.notify(f"Sidebar {sidebar_state}", timeout=1.5)

        # Log layout change details
        if new_breakpoint.name.startswith("horizontal"):
            logger.info(
                f"Switched to horizontal layout optimized for limited height: {new_breakpoint.name}")
        elif new_breakpoint.compact_mode:
            logger.info(f"Switched to compact mode: {new_breakpoint.name}")
        else:
            logger.info(f"Switched to normal layout: {new_breakpoint.name}")

    def _start_layout_transition(self) -> None:
        """Start visual transition effects for layout changes."""
        try:
            # Add transitioning class to main container
            main_container = self.query_one("#main-container")
            main_container.add_class("layout-transitioning")

            # Add transitioning class to sidebar if present
            try:
                sidebar = self.query_one("#sidebar")
                sidebar.add_class("transitioning")
            except Exception:
                pass  # Sidebar might not be present

            # Remove transition classes after animation completes
            self.set_timer(0.4, self._end_layout_transition)

        except Exception as e:
            logger.debug(f"Could not start layout transition: {e}")

    def _end_layout_transition(self) -> None:
        """End visual transition effects."""
        try:
            # Remove transitioning classes
            main_container = self.query_one("#main-container")
            main_container.remove_class("layout-transitioning")

            try:
                sidebar = self.query_one("#sidebar")
                sidebar.remove_class("transitioning")
            except Exception:
                pass  # Sidebar might not be present

        except Exception as e:
            logger.debug(f"Could not end layout transition: {e}")

    async def _update_responsive_layout_with_transition(self) -> None:
        """Update responsive layout with transition support."""
        # Call the regular update method
        await self._update_responsive_layout()

        # Ensure transition classes are properly managed
        self.set_timer(0.1, self._end_layout_transition)

    def action_toggle_responsive_debug(self) -> None:
        """Toggle responsive debug information."""
        breakpoint = self.layout_manager.get_current_breakpoint()
        self.notify(
            f"Current breakpoint: {breakpoint.name} ({self.size.width}×{self.size.height})")

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        try:
            sidebar = self.query_one("#sidebar", expect_type=Vertical)
            sidebar.display = not sidebar.display
            self._sidebar_visible = sidebar.display
        except Exception as e:
            logger.error(f"Error toggling sidebar: {e}")

    # Button event handlers
    @on(Button.Pressed, "#login-btn")
    async def on_login_button(self) -> None:
        """Handle login button press."""
        await self.action_login()

    @on(Button.Pressed, "#logout-btn")
    async def on_logout_button(self) -> None:
        """Handle logout button press."""
        await self.action_logout()

    @on(Button.Pressed, "#refresh-btn")
    async def on_refresh_button(self) -> None:
        """Handle refresh button press."""
        await self.action_refresh()

    # Action methods for key bindings
    async def action_login(self) -> None:
        """Handle login action with enhanced error handling."""
        if self.authenticated:
            self.notify("Already authenticated", severity="warning")
            return

        try:
            async with self.error_handler.error_boundary("authentication"):
                self.loading = True
                self.notify("Starting authentication flow...", timeout=3)

                # Ensure authenticator is properly initialized
                if not self.authenticator:
                    self.authenticator = Authenticator(self.config)

                # Ensure client is refreshed
                if not self.client:
                    self.client = GitHubClient(self.authenticator)

                # Push authentication screen and wait for result
                try:
                    await self.push_screen(AuthScreen(self.authenticator, self.layout_manager))

                    # Refresh authentication status after screen closes
                    await self._check_authentication()

                    if self.authenticated:
                        self.notify(  # type: ignore[unreachable]
                            f"Successfully logged in as {self.current_user}",
                            severity="information",
                            timeout=5
                        )
                        logger.info(
                            f"User successfully authenticated: {self.current_user}")

                        # Refresh all content that depends on authentication
                        await self._refresh_authenticated_content()
                    else:
                        self.notify(
                            "Authentication was cancelled or failed", severity="information")

                except Exception as screen_error:
                    logger.error(f"Error in auth screen: {screen_error}")
                    self.notify(
                        f"Authentication screen error: {screen_error}", severity="error")

        except Exception as e:
            logger.error(f"Error in login action: {e}")
            # Fallback error handling if error_handler fails
            if "Network" in str(e) or "timeout" in str(e).lower():
                self.notify(
                    "Network error during authentication. Please check your connection.", severity="error")
            elif "Authentication" in str(e):
                self.notify(f"Authentication error: {e}", severity="error")
            else:
                self.notify(f"Login failed: {e}", severity="error")
        finally:
            self.loading = False

    async def _refresh_authenticated_content(self) -> None:
        """Refresh content that requires authentication."""
        try:
            logger.debug("Refreshing authenticated content")

            # Update any placeholders with auth-dependent content
            if self.authenticated and self.client:
                # Refresh repository content if visible
                try:
                    repos_tab = self.query_one("#repos-tab", TabPane)
                    if repos_tab.has_focus:
                        # Could trigger a refresh of repository data here
                        pass
                except Exception:
                    pass  # Tab might not exist or be visible

                # Refresh other auth-dependent tabs as needed
                # This can be extended to refresh specific widgets or data

            else:
                # Update placeholders to show login required messages
                auth_required_tabs = [
                    "#repos-tab", "#prs-tab", "#actions-tab", "#notifications-tab", "#search-tab"]

                for tab_id in auth_required_tabs:
                    try:
                        tab = self.query_one(tab_id, TabPane)
                        # Could update content to show login required message
                        pass
                    except Exception:
                        pass  # Tab might not exist

        except Exception as e:
            logger.warning(f"Error refreshing authenticated content: {e}")
            # Don't let content refresh errors break the app

    async def action_logout(self) -> None:
        """Handle logout action with enhanced error handling."""
        if not self.authenticated:
            self.notify("Not authenticated", severity="warning")
            return

        try:
            async with self.error_handler.error_boundary("logout"):
                self.loading = True
                self.notify("Logging out...", timeout=2)

                # Perform logout
                await self.authenticator.logout()

                # Update state
                self.authenticated = False
                self.current_user = None

                # Update status bar
                if self.status_bar:
                    self.status_bar.update_user_info(None)
                    self.status_bar.update_connection_status(False)

                # Clear the GitHub client
                self.client = None

                self.notify("Successfully logged out", severity="information")
                logger.info("User logged out")

                # Refresh UI to reflect unauthenticated state
                await self._refresh_authenticated_content()

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            self.notify(f"Logout failed: {e}", severity="error")

            # Force state cleanup even if logout failed
            self.authenticated = False
            self.current_user = None
            self.client = None

        finally:
            self.loading = False

    async def action_refresh(self) -> None:
        """Handle refresh action with enhanced error handling."""
        async with self.error_handler.error_boundary("refresh"):
            self.loading = True
            self.notify("Refreshing...", timeout=2)

            # Refresh authentication status
            await self._check_authentication()

            # Update rate limit info
            self._update_rate_limit()

            self.notify("Refreshed successfully", severity="information")

        self.loading = False

    async def action_refresh_all(self) -> None:
        """Handle refresh all action."""
        await self.action_refresh()

    def action_new_tab(self) -> None:
        """Handle new tab action."""
        self.notify("New tab functionality not yet implemented")

    def action_close_tab(self) -> None:
        """Handle close tab action."""
        self.notify("Close tab functionality not yet implemented")

    def action_toggle_tree(self) -> None:
        """Handle toggle tree action."""
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    def action_search(self) -> None:
        """Handle search action."""
        # Switch to search tab
        tabs = self.query_one(TabbedContent)
        tabs.active = "search-tab"

    def action_help(self) -> None:
        """Handle help action."""
        self.push_screen(HelpScreen())

    # Reactive watchers
    def watch_authenticated(self, authenticated: bool) -> None:
        """React to authentication state changes."""
        try:
            self._update_auth_button_visibility(authenticated)

            # Refresh content that depends on authentication
            self.call_after_refresh(self._refresh_authenticated_content)

            logger.debug(f"Authentication state updated: {authenticated}")
        except Exception as e:
            logger.debug(f"Could not update UI for auth state change: {e}")
            # UI might not be fully initialized yet

    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes with modern LoadingIndicator."""
        try:
            # Update status bar
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.update_loading_state(loading)

            # Show/hide loading overlay
            loading_overlay = self.query_one("#loading-overlay", LoadingIndicator)
            if loading_overlay:
                loading_overlay.display = loading
        except Exception as e:
            logger.debug(f"Could not update loading state: {e}")
            # UI might not be fully initialized yet


# Main entry point for the TUI application
def run_tui() -> None:
    """Run the GitHub CLI TUI application."""
    app = GitHubTUIApp()
    app.run()
