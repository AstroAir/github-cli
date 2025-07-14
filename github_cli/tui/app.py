from __future__ import annotations

import asyncio
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Footer, Input, Label, LoadingIndicator,
    Log, Placeholder, ProgressBar, Static, TabbedContent, TabPane, Tree
)
from textual.widgets._header import Header
from loguru import logger

from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError, AuthenticationError


class StatusBar(Static):
    """Enhanced status bar with real-time information."""
    
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """
    
    user_info: reactive[str] = reactive("Not authenticated")
    rate_limit: reactive[str] = reactive("Rate limit: Unknown")
    connection_status: reactive[str] = reactive("Disconnected")
    
    def render(self) -> str:
        """Render the status bar with current information."""
        return f"{self.user_info} | {self.rate_limit} | {self.connection_status}"
    
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
    """Modern GitHub CLI TUI application with comprehensive functionality."""
    
    TITLE = "GitHub CLI - Terminal User Interface"
    SUB_TITLE = "Advanced GitHub management in your terminal"
    
    CSS_PATH = "github_tui.tcss"  # External CSS file for styling
    
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
    ]
    
    # Reactive attributes for state management
    authenticated: reactive[bool] = reactive(False)
    current_user: reactive[str | None] = reactive(None)
    loading: reactive[bool] = reactive(False)
    
    def __init__(self) -> None:
        super().__init__()
        
        # Initialize GitHub CLI components
        self.config = Config()
        self.authenticator = Authenticator(self.config)
        self.client: GitHubClient | None = None
        self.status_bar: StatusBar | None = None
        
        logger.info("GitHub TUI application initialized")
    
    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        logger.info("GitHub TUI application mounted")
        
        # Initialize GitHub client
        self.client = GitHubClient(self.authenticator)
        
        # Check authentication status
        await self._check_authentication()
        
        # Start background tasks
        self._start_background_tasks()
    
    def compose(self) -> ComposeResult:
        """Create the main UI layout."""
        yield Header()
        
        with Container(id="main-container"):
            with Horizontal(id="content-area"):
                # Sidebar navigation
                with Vertical(id="sidebar", classes="sidebar"):
                    yield Tree("GitHub CLI", id="nav-tree")
                    yield Button("🔐 Login", id="login-btn", variant="primary")
                    yield Button("🚪 Logout", id="logout-btn", variant="error")
                    yield Button("🔄 Refresh", id="refresh-btn")
                
                # Main content area with tabs
                with TabbedContent(id="main-tabs"):
                    with TabPane("Dashboard", id="dashboard-tab"):
                        yield Placeholder("Dashboard content will go here", id="dashboard")
                    
                    with TabPane("Repositories", id="repos-tab"):
                        from github_cli.tui.repositories import create_repository_widget
                        if self.client:
                            yield create_repository_widget(self.client)
                        else:
                            yield Placeholder("Please login to GitHub first", id="repos-placeholder")
                    
                    with TabPane("Pull Requests", id="prs-tab"):
                        from github_cli.tui.pull_requests import create_pull_request_widget
                        if self.client:
                            yield create_pull_request_widget(self.client)
                        else:
                            yield Placeholder("Please login to GitHub first", id="prs-placeholder")
                    
                    with TabPane("Actions", id="actions-tab"):
                        from github_cli.tui.actions import create_actions_widget
                        if self.client:
                            yield create_actions_widget(self.client)
                        else:
                            yield Placeholder("Please login to GitHub first", id="actions-placeholder")
                    
                    with TabPane("Notifications", id="notifications-tab"):
                        from github_cli.tui.notifications import create_notification_widget
                        if self.client:
                            yield create_notification_widget(self.client)
                        else:
                            yield Placeholder("Please login to GitHub first", id="notifications-placeholder")
                    
                    with TabPane("Search", id="search-tab"):
                        from github_cli.tui.search import create_search_widget
                        if self.client:
                            yield create_search_widget(self.client)
                        else:
                            yield Placeholder("Please login to GitHub first", id="search-placeholder")
                    
                    with TabPane("Settings", id="settings-tab"):
                        from github_cli.tui.settings import create_settings_widget
                        yield create_settings_widget(self.config)
        
        # Status bar
        self.status_bar = StatusBar()
        yield self.status_bar
        
        yield Footer()
    
    async def _check_authentication(self) -> None:
        """Check and update authentication status."""
        try:
            if self.authenticator.is_authenticated():
                user_info = await self.authenticator.fetch_user_info()
                if user_info:
                    self.authenticated = True
                    self.current_user = user_info.login
                    logger.info(f"Authenticated as {user_info.login}")
                    
                    if self.status_bar:
                        self.status_bar.update_user_info(user_info.login)
                        self.status_bar.update_connection_status(True)
                else:
                    self.authenticated = False
                    self.current_user = None
            else:
                self.authenticated = False
                self.current_user = None
                
                if self.status_bar:
                    self.status_bar.update_user_info(None)
                    self.status_bar.update_connection_status(False)
                    
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            self.authenticated = False
            self.current_user = None
    
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
                    self.status_bar.update_rate_limit(remaining, 5000)  # GitHub's default limit
                    
            except Exception as e:
                logger.warning(f"Failed to update rate limit: {e}")
    
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
        """Handle login action."""
        if self.authenticated:
            self.notify("Already authenticated", severity="warning")
            return
        
        try:
            self.loading = True
            self.notify("Starting authentication flow...", timeout=3)
            
            # Push authentication screen and wait for result
            result = await self.push_screen(AuthScreen(self.authenticator))
            
            # Refresh authentication status after the screen returns
            await self._check_authentication()
            
            if self.authenticated:
                self.notify(f"Successfully logged in as {self.current_user}", severity="information", timeout=5)
                logger.info(f"User successfully authenticated: {self.current_user}")
                
                # Refresh all content that depends on authentication
                await self._refresh_authenticated_content()
            else:
                self.notify("Authentication was not completed", severity="warning")
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.notify(f"Login failed: {e}", severity="error", timeout=10)
        finally:
            self.loading = False
    
    async def _refresh_authenticated_content(self) -> None:
        """Refresh content that requires authentication."""
        try:
            # This method can be extended to refresh specific tabs or widgets
            # that depend on authentication status
            logger.debug("Refreshing authenticated content")
            
            # Example: Could refresh repositories, notifications, etc.
            # For now, we just log the action
            pass
            
        except Exception as e:
            logger.warning(f"Error refreshing authenticated content: {e}")
    
    async def action_logout(self) -> None:
        """Handle logout action."""
        if not self.authenticated:
            self.notify("Not authenticated", severity="warning")
            return
        
        try:
            await self.authenticator.logout()
            self.authenticated = False
            self.current_user = None
            
            if self.status_bar:
                self.status_bar.update_user_info(None)
                self.status_bar.update_connection_status(False)
            
            self.notify("Successfully logged out", severity="information")
            logger.info("User logged out")
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            self.notify(f"Logout failed: {e}", severity="error")
    
    async def action_refresh(self) -> None:
        """Handle refresh action."""
        try:
            self.loading = True
            self.notify("Refreshing...", timeout=2)
            
            # Refresh authentication status
            await self._check_authentication()
            
            # Update rate limit info
            self._update_rate_limit()
            
            self.notify("Refreshed successfully", severity="information")
            
        except Exception as e:
            logger.error(f"Refresh error: {e}")
            self.notify(f"Refresh failed: {e}", severity="error")
        finally:
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
        login_btn = self.query_one("#login-btn")
        logout_btn = self.query_one("#logout-btn")
        
        if authenticated:
            login_btn.display = False
            logout_btn.display = True
        else:
            login_btn.display = True
            logout_btn.display = False
    
    def watch_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        # You could show/hide a loading indicator here
        pass


class AuthScreen(Screen[None]):
    """Authentication screen for OAuth flow."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+c", "dismiss", "Cancel"),
    ]
    
    def __init__(self, authenticator: Authenticator) -> None:
        super().__init__()
        self.authenticator = authenticator
        self._auth_task: asyncio.Task | None = None
    
    def compose(self) -> ComposeResult:
        """Compose the authentication screen."""
        with Container(id="auth-container"):
            yield Static("🔐 GitHub Authentication", id="auth-title")
            yield Static("Starting authentication flow...", id="auth-subtitle")
            yield LoadingIndicator(id="auth-loading")
            yield Log(id="auth-log", auto_scroll=True)
            with Horizontal(id="auth-buttons"):
                yield Button("Cancel", id="cancel-btn", variant="error")
                yield Button("Retry", id="retry-btn", variant="primary")
    
    async def on_mount(self) -> None:
        """Start the authentication flow when mounted."""
        await self._start_auth_flow()
    
    async def _start_auth_flow(self) -> None:
        """Start the authentication flow with proper error handling."""
        log_widget = self.query_one("#auth-log", Log)
        subtitle_widget = self.query_one("#auth-subtitle", Static)
        loading_widget = self.query_one("#auth-loading", LoadingIndicator)
        retry_btn = self.query_one("#retry-btn", Button)
        
        try:
            # Reset UI state
            loading_widget.display = True
            retry_btn.display = False
            subtitle_widget.update("Starting authentication flow...")
            log_widget.clear()
            
            log_widget.write_line("🔐 Starting GitHub authentication...")
            log_widget.write_line("📋 Please follow the instructions that will appear...")
            
            # Start the OAuth flow in a task so we can cancel it
            self._auth_task = asyncio.create_task(self.authenticator.login_interactive())
            await self._auth_task
            
            log_widget.write_line("✅ Authentication successful!")
            subtitle_widget.update("Authentication completed successfully!")
            loading_widget.display = False
            
            # Brief pause to show success message
            await asyncio.sleep(1.5)
            self.dismiss()
            
        except asyncio.CancelledError:
            log_widget.write_line("❌ Authentication cancelled by user")
            subtitle_widget.update("Authentication cancelled")
            loading_widget.display = False
            retry_btn.display = True
            logger.info("Authentication cancelled by user")
            
        except AuthenticationError as e:
            log_widget.write_line(f"❌ Authentication failed: {e}")
            subtitle_widget.update("Authentication failed - Click Retry to try again")
            loading_widget.display = False
            retry_btn.display = True
            logger.error(f"Authentication error: {e}")
            
        except Exception as e:
            log_widget.write_line(f"❌ Unexpected error: {e}")
            subtitle_widget.update("An unexpected error occurred")
            loading_widget.display = False
            retry_btn.display = True
            logger.error(f"Unexpected authentication error: {e}")
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_auth(self) -> None:
        """Cancel authentication."""
        if self._auth_task and not self._auth_task.done():
            self._auth_task.cancel()
        self.dismiss()
    
    @on(Button.Pressed, "#retry-btn")
    async def retry_auth(self) -> None:
        """Retry authentication."""
        await self._start_auth_flow()


class HelpScreen(Screen[None]):
    """Help screen showing keybindings and usage."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close Help"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Container(id="help-container"):
            yield Static("GitHub CLI - Help", id="help-title")
            
            help_text = """
GitHub CLI TUI - Keyboard Shortcuts

Navigation:
  Ctrl+C / Q      Quit application
  Ctrl+N          New tab
  Ctrl+W          Close tab
  Ctrl+T          Toggle sidebar
  Ctrl+R          Refresh current view
  Ctrl+S          Search
  F1              Show this help
  F5              Refresh all

Authentication:
  Ctrl+L          Login
  Ctrl+O          Logout

General:
  Tab             Navigate between widgets
  Enter           Activate/Select
  Escape          Cancel/Go back
  Arrow Keys      Navigate lists
  Page Up/Down    Scroll long lists
  Home/End        Go to first/last item

Repository View:
  Enter           View repository details
  D               Clone repository
  I               View issues
  P               View pull requests
  A               View actions

Pull Requests:
  Enter           View PR details
  M               Merge PR
  C               Close PR
  R               Review PR

Notifications:
  Enter           View notification
  M               Mark as read
  Del             Delete notification
  Ctrl+A          Mark all as read

Search:
  /               Focus search input
  Enter           Execute search
  Tab             Switch search type

For more information, visit: https://github.com/github/gh
            """
            
            yield Static(help_text.strip(), id="help-content")
            yield Button("Close", id="close-help", variant="primary")
    
    @on(Button.Pressed, "#close-help")
    def close_help(self) -> None:
        """Close help screen."""
        self.dismiss()


# Main entry point for the TUI application
def run_tui() -> None:
    """Run the GitHub CLI TUI application."""
    app = GitHubTUIApp()
    app.run()
