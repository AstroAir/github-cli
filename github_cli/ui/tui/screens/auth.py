"""
Authentication screen for GitHub CLI TUI.

This module contains the authentication screen that handles the OAuth flow
for GitHub authentication with responsive design capabilities.
"""

import asyncio
from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from github_cli.auth.authenticator import Authenticator
from github_cli.auth.common import AuthResult, AuthenticationError
from github_cli.ui.auth.responsive_layout import ResponsiveAuthLayout
from github_cli.ui.auth.error_handler import AuthErrorHandler
from github_cli.ui.auth.progress_tracker import AuthProgressTracker, AuthStep
from github_cli.utils.config import Config
from github_cli.utils.performance import logger
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager


class AuthScreen(Screen[AuthResult]):
    """Enhanced authentication screen with responsive capabilities."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("ctrl+c", "dismiss", "Cancel"),
        Binding("r", "retry", "Retry"),
        Binding("h", "help", "Help"),
    ]

    def __init__(self, authenticator: Authenticator, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.authenticator = authenticator
        self._auth_task: asyncio.Task | None = None
        self.layout_manager = layout_manager
        
        # Initialize responsive components (defer app-dependent initialization)
        self.responsive_layout: ResponsiveAuthLayout | None = None
        self.error_handler: AuthErrorHandler | None = None
        self.current_config = None
        self.progress_tracker: AuthProgressTracker | None = None
        
        # Authentication state
        self.current_auth_view = None
        self.device_code: str | None = None
        self.verification_uri: str | None = None
        
        logger.info("Enhanced AuthScreen initialized with responsive capabilities")

    def compose(self) -> ComposeResult:
        """Compose the responsive authentication interface."""
        # Initialize responsive components if not already done
        if self.responsive_layout is None:
            if self.layout_manager is None:
                # Create a basic layout manager if none provided
                self.layout_manager = ResponsiveLayoutManager(self.app)
            
            self.responsive_layout = ResponsiveAuthLayout(self.layout_manager)
            self.error_handler = AuthErrorHandler(self.app, self)
            
            # Register for layout changes
            self.responsive_layout.add_resize_callback(self._on_layout_change)
        
        # Get optimal layout configuration
        self.current_config = self.responsive_layout.get_optimal_layout()
        
        # Initialize progress tracker with current config
        self.progress_tracker = AuthProgressTracker(self.current_config)
        
        # Create auth view for current layout
        self.current_auth_view = self.responsive_layout.create_auth_view(self.current_config)
        
        # Compose based on layout type
        if self.current_config.layout_type == "compact":
            yield from self._compose_compact_layout()
        elif self.current_config.layout_type == "standard":
            yield from self._compose_standard_layout()
        else:  # expanded
            yield from self._compose_expanded_layout()

    def _compose_compact_layout(self) -> ComposeResult:
        """Compose compact layout for small terminals."""
        with Container(id="auth-container", classes="auth-screen compact"):
            # Header
            yield Static("🔐 GitHub Auth", id="auth-header", classes="auth-header compact")
            
            # Device code display
            yield Static("Code: ----", id="device-code", classes="device-code compact")
            
            # Progress indicator
            if self.progress_tracker:
                progress_widgets = self.progress_tracker.get_progress_widgets()
                yield progress_widgets["progress_indicator"]
            else:
                yield Static("⏳ Loading...", id="progress-indicator")
            
            # Status display
            if self.progress_tracker:
                progress_widgets = self.progress_tracker.get_progress_widgets()
                yield progress_widgets["status_display"]
            else:
                yield Static("Ready", id="status-display")
            
            # Action buttons (vertical layout)
            with Vertical(id="auth-actions", classes="actions-container compact"):
                yield Button("Retry", id="retry-btn", variant="primary", classes="retry-btn")
                yield Button("Cancel", id="cancel-btn", variant="error", classes="cancel-btn")

    def _compose_standard_layout(self) -> ComposeResult:
        """Compose standard layout for medium terminals."""
        with Container(id="auth-container", classes="auth-screen standard"):
            # Header
            yield Static("🔐 GitHub Authentication", id="auth-header", classes="auth-header standard")
            
            # Instructions
            instructions = (
                "1. Your browser will open automatically\n"
                "2. Enter the device code shown below\n"
                "3. Authorize GitHub CLI access\n"
                "4. Return to this terminal"
            )
            yield Static(instructions, id="auth-instructions", classes="auth-instructions standard")
            
            # Content row with device code and progress
            with Horizontal(id="auth-content-row", classes="auth-content-row"):
                # Device code section
                with Vertical(id="device-code-section", classes="device-code-section"):
                    yield Static("Device Code:", id="device-code-label", classes="device-code-label")
                    yield Static("Loading...", id="device-code", classes="device-code standard")
                    yield Static("URL: Loading...", id="verification-url", classes="verification-url")
                
                # Progress section
                with Vertical(id="progress-section", classes="progress-section"):
                    if self.progress_tracker:
                        progress_widgets = self.progress_tracker.get_progress_widgets()
                        yield progress_widgets["progress_indicator"]
                        if "countdown_timer" in progress_widgets:
                            yield progress_widgets["countdown_timer"]
                    else:
                        yield Static("⏳ Loading...", id="progress-indicator")
            
            # Status display
            if self.progress_tracker:
                progress_widgets = self.progress_tracker.get_progress_widgets()
                yield progress_widgets["status_display"]
            else:
                yield Static("Ready", id="status-display")
            
            # Action buttons (horizontal layout)
            with Horizontal(id="auth-actions", classes="actions-container standard"):
                yield Button("Retry Authentication", id="retry-btn", variant="primary", classes="retry-btn")
                yield Button("Cancel", id="cancel-btn", variant="error", classes="cancel-btn")

    def _compose_expanded_layout(self) -> ComposeResult:
        """Compose expanded layout for large terminals."""
        with Container(id="auth-container", classes="auth-screen expanded"):
            # Header
            yield Static("🔐 GitHub CLI Authentication", id="auth-header", classes="auth-header expanded")
            
            # Main content grid
            with Horizontal(id="auth-main-content", classes="auth-main-content"):
                # Left column: Instructions and help
                with Vertical(id="auth-left-column", classes="auth-left-column"):
                    instructions = (
                        "Welcome to GitHub CLI Authentication\n\n"
                        "To authenticate with GitHub:\n"
                        "1. Your default browser will open automatically\n"
                        "2. Copy and enter the device code displayed below\n"
                        "3. Review and authorize GitHub CLI access permissions\n"
                        "4. Return to this terminal to continue\n\n"
                        "If the browser doesn't open, manually visit the URL shown."
                    )
                    yield Static(instructions, id="auth-instructions", classes="auth-instructions expanded")
                    
                    # Help section
                    help_text = (
                        "Troubleshooting:\n\n"
                        "• Browser not opening? Copy the URL manually\n"
                        "• Code expired? Click 'Retry Authentication'\n"
                        "• Network issues? Check your connection\n"
                        "• Still having trouble? Press 'h' for more options"
                    )
                    yield Static(help_text, id="auth-help", classes="help-section expanded")
                
                # Right column: Device code and progress
                with Vertical(id="auth-right-column", classes="auth-right-column"):
                    # Device code container
                    with Container(id="device-code-container", classes="device-code-container expanded"):
                        yield Static("Device Code", id="device-code-label", classes="device-code-label")
                        yield Static("Loading...", id="device-code", classes="device-code-value expanded")
                        yield Static("Verification URL: Loading...", id="verification-url", classes="verification-url expanded")
                    
                    # Progress container
                    if self.progress_tracker:
                        progress_widgets = self.progress_tracker.get_progress_widgets()
                        yield progress_widgets["progress_indicator"]
                        if "countdown_timer" in progress_widgets:
                            yield progress_widgets["countdown_timer"]
                        yield progress_widgets["status_display"]
                    else:
                        yield Static("⏳ Loading...", id="progress-indicator")
                        yield Static("Ready", id="status-display")
            
            # Bottom action area
            with Horizontal(id="auth-actions", classes="actions-container expanded"):
                yield Button("Retry Authentication", id="retry-btn", variant="primary", classes="retry-btn")
                yield Button("Help", id="help-btn", variant="default", classes="help-btn")
                yield Button("Cancel", id="cancel-btn", variant="error", classes="cancel-btn")

    async def on_mount(self) -> None:
        """Start the authentication flow when mounted."""
        logger.info("AuthScreen mounted, starting authentication flow")
        
        # Initialize responsive components now that app is available
        if self.layout_manager is None:
            # Create a basic layout manager if none provided
            self.layout_manager = ResponsiveLayoutManager(self.app)
        
        self.responsive_layout = ResponsiveAuthLayout(self.layout_manager)
        self.error_handler = AuthErrorHandler(self.app, self)
        
        # Register for layout changes
        self.responsive_layout.add_resize_callback(self._on_layout_change)
        
        await self._start_auth_flow()

    async def _start_auth_flow(self) -> None:
        """Start the enhanced authentication flow with comprehensive error handling."""
        try:
            # Initialize progress tracking
            if self.progress_tracker:
                self.progress_tracker.update_step(AuthStep.INITIALIZING)
            
            # Reset UI state
            self._reset_ui_state()
            
            # Start the OAuth flow with error handling
            if self.error_handler:
                async with self.error_handler.auth_error_boundary("oauth_flow"):
                    self._auth_task = asyncio.create_task(self._run_auth_flow())
                    result = await self._auth_task
                    
                    # Show success and dismiss
                    if self.progress_tracker:
                        self.progress_tracker.show_success("Authentication successful!")
                    await asyncio.sleep(1.5)
                    self.dismiss(result)
            else:
                # Fallback without error boundary
                self._auth_task = asyncio.create_task(self._run_auth_flow())
                result = await self._auth_task
                
                # Show success and dismiss
                if self.progress_tracker:
                    self.progress_tracker.show_success("Authentication successful!")
                await asyncio.sleep(1.5)
                self.dismiss(result)
                
        except asyncio.CancelledError:
            logger.info("Authentication cancelled by user")
            if self.progress_tracker:
                self.progress_tracker.show_error("Authentication cancelled by user")
            self._show_retry_option()
            
        except AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            if self.error_handler:
                auth_result = await self.error_handler.handle_auth_error(e, {"screen": "auth_screen"})
                
                if auth_result.retry_suggested:
                    self._show_retry_option()
                else:
                    self.dismiss(auth_result)
            else:
                # Fallback without error handler
                if self.progress_tracker:
                    self.progress_tracker.show_error(f"Authentication error: {e}")
                self._show_retry_option()
                
        except Exception as e:
            logger.exception(f"Unexpected authentication error: {e}")
            auth_error = AuthenticationError("Unexpected authentication error", cause=e)
            if self.error_handler:
                auth_result = await self.error_handler.handle_auth_error(auth_error)
                self.dismiss(auth_result)
            else:
                # Fallback without error handler
                if self.progress_tracker:
                    self.progress_tracker.show_error(f"Unexpected error: {e}")
                self._show_retry_option()

    async def _run_auth_flow(self) -> AuthResult:
        """Run the core authentication flow with progress tracking."""
        try:
            # Step 1: Request device code
            if self.progress_tracker:
                self.progress_tracker.update_step(AuthStep.REQUESTING_CODE)
            
            # Use the actual authenticator to request device code
            device_flow_data = await self._request_device_code()
            
            self.device_code = device_flow_data.get("user_code", "XXXX-XXXX")
            self.verification_uri = device_flow_data.get("verification_uri", "https://github.com/login/device")
            
            # Update UI with device code
            self._update_device_code_display()
            
            # Try to open browser automatically (like the CLI version does)
            await self._open_browser_for_auth()
            
            # Step 2: Wait for user authorization
            if self.progress_tracker:
                self.progress_tracker.update_step(AuthStep.WAITING_FOR_USER, {
                    "device_code": self.device_code,
                    "verification_uri": self.verification_uri
                })
            
            # Show countdown for device code expiration
            expires_in = device_flow_data.get("expires_in", 900)  # 15 minutes default
            if self.progress_tracker:
                self.progress_tracker.show_countdown(
                    expires_in,
                    "Device code expires in",
                    self._on_device_code_expired
                )
            
            # Step 3: Poll for token
            if self.progress_tracker:
                self.progress_tracker.update_step(AuthStep.POLLING_TOKEN)
            
            # Use the actual authenticator to poll for token
            token_data = await self._poll_for_token(device_flow_data)
            
            # Step 4: Validate token
            if self.progress_tracker:
                self.progress_tracker.update_step(AuthStep.VALIDATING)
            
            # Use the actual authenticator to validate token
            user_info = await self._validate_token(token_data)
            
            # Step 5: Complete
            if self.progress_tracker:
                self.progress_tracker.update_step(AuthStep.COMPLETE)
            
            return AuthResult(
                success=True,
                user_info=user_info,
                preferences_updated=False
            )
            
        except Exception as e:
            logger.error(f"Error in auth flow: {e}")
            raise

    async def _open_browser_for_auth(self) -> None:
        """Open browser for authentication with user notification using multiple fallback methods."""
        try:
            if not self.verification_uri:
                logger.warning("No verification URI available for browser opening")
                return
                
            import webbrowser
            import subprocess
            import sys
            
            browser_opened = False
            
            # Try the default browser first
            try:
                if webbrowser.open(self.verification_uri):
                    self.app.notify(
                        "🚀 Opened browser for authentication. Please authorize GitHub CLI access.",
                        severity="information",
                        timeout=5
                    )
                    logger.info("Successfully opened browser for authentication")
                    browser_opened = True
            except Exception as e:
                logger.debug(f"Default browser failed: {e}")
            
            # Try platform-specific commands as fallback
            if not browser_opened:
                try:
                    if sys.platform.startswith('win'):
                        # Windows
                        process = await asyncio.create_subprocess_exec(
                            'cmd', '/c', 'start', self.verification_uri,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        await process.wait()
                        browser_opened = True
                    elif sys.platform.startswith('darwin'):
                        # macOS
                        process = await asyncio.create_subprocess_exec(
                            'open', self.verification_uri,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        await process.wait()
                        browser_opened = True
                    elif sys.platform.startswith('linux'):
                        # Linux
                        process = await asyncio.create_subprocess_exec(
                            'xdg-open', self.verification_uri,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        await process.wait()
                        browser_opened = True
                    
                    if browser_opened:
                        self.app.notify(
                            "🚀 Opened browser for authentication. Please authorize GitHub CLI access.",
                            severity="information",
                            timeout=5
                        )
                        logger.info("Successfully opened browser using platform-specific command")
                except Exception as e:
                    logger.debug(f"Platform-specific browser command failed: {e}")
            
            # If still not opened, provide manual instructions
            if not browser_opened:
                self.app.notify(
                    f"Please manually open: {self.verification_uri}",
                    severity="warning",
                    timeout=10
                )
                logger.warning("Could not open browser automatically")
                
                # Try to copy to clipboard as a fallback
                try:
                    import pyperclip
                    pyperclip.copy(self.verification_uri)
                    self.app.notify(
                        "📋 URL copied to clipboard!",
                        severity="information",
                        timeout=3
                    )
                except ImportError:
                    logger.debug("pyperclip not available for clipboard support")
                except Exception as e:
                    logger.debug(f"Could not copy to clipboard: {e}")
                
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            # Provide manual instructions
            self.app.notify(
                f"Please manually open: {self.verification_uri or 'GitHub device activation page'}",
                severity="warning",
                timeout=10
            )

    async def _request_device_code(self) -> dict:
        """Request device code from GitHub using the actual authenticator."""
        try:
            # Use the actual authenticator to request device code
            device_code_data = await self.authenticator._request_device_code(
                self.authenticator._auth_config.default_scopes
            )
            
            if device_code_data:
                logger.info("Device code request successful")
                return device_code_data
            else:
                raise AuthenticationError("Failed to request device code")
                
        except Exception as e:
            logger.error(f"Error requesting device code: {e}")
            raise AuthenticationError(f"Failed to request device code: {e}") from e

    async def _poll_for_token(self, device_flow_data: dict) -> dict:
        """Poll for authentication token using the actual authenticator."""
        try:
            device_code = device_flow_data.get("device_code")
            interval = device_flow_data.get("interval", 5)
            
            if not device_code:
                raise AuthenticationError("Invalid device code data")
                
            # Use the actual authenticator to poll for token
            token_data = await self.authenticator._poll_for_token(device_code, interval)
            
            if token_data and "access_token" in token_data:
                logger.info("Token polling successful")
                return token_data
            else:
                raise AuthenticationError("Failed to obtain access token")
                
        except Exception as e:
            logger.error(f"Error polling for token: {e}")
            raise AuthenticationError(f"Failed to poll for token: {e}") from e

    async def _validate_token(self, token_data: dict) -> dict:
        """Validate token and fetch user info using the actual authenticator."""
        try:
            # Save the token to the authenticator
            access_token = token_data.get("access_token")
            if not access_token:
                raise AuthenticationError("No access token received")
                
            # Save the token
            saved_token = self.authenticator.token_manager.save_token(token_data)
            self.authenticator._token = saved_token
            
            # Fetch user info to validate the token
            user_info = await self.authenticator.fetch_user_info()
            if user_info:
                logger.info(f"Token validation successful for user: {user_info.login}")
                return {
                    "login": user_info.login,
                    "id": user_info.id,
                    "name": user_info.name,
                    "email": user_info.email
                }
            else:
                raise AuthenticationError("Token validation failed - unable to fetch user info")
                
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            raise AuthenticationError(f"Failed to validate token: {e}") from e

    def _update_device_code_display(self) -> None:
        """Update the device code display in the UI."""
        try:
            device_code_widget = self.query_one("#device-code", Static)
            verification_url_widget = self.query_one("#verification-url", Static)
            
            if self.current_config and self.current_config.layout_type == "compact":
                device_code_widget.update(f"Code: {self.device_code or 'Loading...'}")
            else:
                device_code_widget.update(self.device_code or "Loading...")
                verification_url_widget.update(f"URL: {self.verification_uri or 'Loading...'}")
                
        except Exception as e:
            logger.warning(f"Could not update device code display: {e}")

    def _reset_ui_state(self) -> None:
        """Reset UI state for new authentication attempt."""
        try:
            retry_btn = self.query_one("#retry-btn", Button)
            retry_btn.display = False
        except Exception:
            pass  # Widget might not exist in all layouts

    def _show_retry_option(self) -> None:
        """Show retry option after authentication failure."""
        try:
            retry_btn = self.query_one("#retry-btn", Button)
            retry_btn.display = True
        except Exception:
            pass  # Widget might not exist in all layouts

    def _on_device_code_expired(self) -> None:
        """Handle device code expiration."""
        if self.progress_tracker:
            self.progress_tracker.show_error("Device code expired. Please retry authentication.")
        self._show_retry_option()

    def _on_layout_change(self, old_config, new_config) -> None:
        """Handle layout changes during authentication."""
        logger.info(f"Auth layout changed: {old_config.layout_type if old_config else 'None'} -> {new_config.layout_type}")
        
        # Update progress tracker configuration
        if self.progress_tracker:
            self.progress_tracker.update_layout_config(new_config)
        
        # Store new configuration
        self.current_config = new_config
        
        # Note: Dynamic layout switching would require more complex implementation
        # For now, we just update the progress tracker configuration

    @on(Button.Pressed, "#cancel-btn")
    def cancel_auth(self) -> None:
        """Cancel authentication."""
        if self._auth_task and not self._auth_task.done():
            self._auth_task.cancel()
        
        result = AuthResult(success=False, error=AuthenticationError("Authentication cancelled by user"))
        self.dismiss(result)

    @on(Button.Pressed, "#retry-btn")
    async def retry_auth(self) -> None:
        """Retry authentication."""
        logger.info("Retrying authentication")
        await self._start_auth_flow()

    @on(Button.Pressed, "#help-btn")
    def show_help(self) -> None:
        """Show authentication help."""
        help_message = (
            "Authentication Help:\n\n"
            "1. Make sure you have internet access\n"
            "2. Check if GitHub.com is accessible\n"
            "3. Try refreshing the page if browser doesn't load\n"
            "4. Contact support if issues persist"
        )
        self.app.notify(help_message, title="Authentication Help", timeout=10)

    def action_retry(self) -> None:
        """Handle retry action from keyboard shortcut."""
        self.query_one("#retry-btn", Button).press()

    def action_help(self) -> None:
        """Handle help action from keyboard shortcut."""
        try:
            help_btn = self.query_one("#help-btn", Button)
            help_btn.press()
        except Exception:
            # Fallback if help button doesn't exist
            self.show_help()

    async def on_resize(self, event) -> None:
        """Handle terminal resize during authentication."""
        if self.responsive_layout and hasattr(self.responsive_layout, 'handle_resize'):
            self.responsive_layout.handle_resize(event.size)

    def on_unmount(self) -> None:
        """Clean up when screen is unmounted."""
        # Cancel any running authentication task
        if self._auth_task and not self._auth_task.done():
            self._auth_task.cancel()
        
        # Clean up progress tracker
        if self.progress_tracker:
            self.progress_tracker.cleanup()
        
        # Clean up responsive layout
        if self.responsive_layout and hasattr(self.responsive_layout, 'cleanup'):
            self.responsive_layout.cleanup()
        
        logger.info("AuthScreen unmounted and cleaned up")
