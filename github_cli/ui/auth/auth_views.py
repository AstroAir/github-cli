"""
Authentication view implementations for different layout configurations.

This module provides concrete implementations of authentication views that adapt
to different terminal sizes and layout requirements.
"""

from __future__ import annotations

from github_cli.auth.common import (
    Any, Container, Horizontal, Vertical, Grid, Static, Label, Button, 
    ProgressBar, ComposeResult
)
from textual.widget import Widget

from github_cli.ui.auth.responsive_layout import AuthLayoutConfig


class BaseAuthView:
    """Base class for authentication views with common functionality."""

    def __init__(self, config: AuthLayoutConfig) -> None:
        self.config = config
        self.current_step = "initializing"
        self.progress_details: dict[str, Any] = {}

    def _create_header(self) -> Widget:
        """Create the authentication header."""
        if self.config.layout_type == "compact":
            return Label("🔐 GitHub Auth", classes="auth-header compact")
        elif self.config.layout_type == "standard":
            return Label("🔐 GitHub Authentication", classes="auth-header standard")
        else:  # expanded
            return Label("🔐 GitHub CLI Authentication", classes="auth-header expanded")

    def _create_instructions(self) -> Widget:
        """Create instruction text based on layout configuration."""
        if self.config.layout_type == "compact":
            text = "1. Open browser\n2. Enter code\n3. Authorize"
        elif self.config.layout_type == "standard":
            text = ("1. Your browser will open automatically\n"
                    "2. Enter the device code shown below\n"
                    "3. Authorize GitHub CLI access\n"
                    "4. Return to this terminal")
        else:  # expanded
            text = ("Welcome to GitHub CLI Authentication\n\n"
                    "To authenticate with GitHub:\n"
                    "1. Your default browser will open automatically\n"
                    "2. Copy and enter the device code displayed below\n"
                    "3. Review and authorize GitHub CLI access permissions\n"
                    "4. Return to this terminal to continue\n\n"
                    "If the browser doesn't open, manually visit the URL shown.")

        return Static(text, classes=f"auth-instructions {self.config.layout_type}")

    def _create_device_code_display(self, code: str = "XXXX-XXXX") -> Widget:
        """Create device code display with appropriate emphasis."""
        if self.config.layout_type == "compact":
            return Static(f"Code: {code}", classes="device-code compact")
        elif self.config.layout_type == "standard":
            return Static(f"Device Code:\n{code}", classes="device-code standard")
        else:  # expanded
            return Container(
                Label("Device Code", classes="device-code-label"),
                Static(code, classes="device-code-value expanded"),
                classes="device-code-container expanded"
            )

    def _create_progress_indicator(self) -> Widget:
        """Create progress indicator based on layout configuration."""
        if self.config.layout_type == "compact":
            return Static("⏳ Waiting...", classes="progress-indicator compact")
        elif self.config.layout_type == "standard":
            return Container(
                ProgressBar(classes="auth-progress"),
                Static("Waiting for authorization...",
                       classes="progress-text"),
                classes="progress-container standard"
            )
        else:  # expanded
            return Container(
                Label("Authentication Progress", classes="progress-label"),
                ProgressBar(classes="auth-progress expanded"),
                Static("Waiting for authorization in browser...",
                       classes="progress-text expanded"),
                classes="progress-container expanded"
            )

    def _create_action_buttons(self) -> Widget:
        """Create action buttons based on layout configuration."""
        cancel_btn = Button("Cancel", variant="error", classes="cancel-btn")

        if self.config.layout_type == "compact":
            return Vertical(
                cancel_btn,
                classes="actions-container compact"
            )
        elif self.config.layout_type == "standard":
            retry_btn = Button("Retry", variant="primary", classes="retry-btn")
            return Horizontal(
                retry_btn,
                cancel_btn,
                classes="actions-container standard"
            )
        else:  # expanded
            retry_btn = Button("Retry Authentication",
                               variant="primary", classes="retry-btn")
            help_btn = Button("Help", variant="default", classes="help-btn")
            return Grid(
                retry_btn,
                help_btn,
                cancel_btn,
                classes="actions-container expanded"
            )

    def _create_status_display(self) -> Widget:
        """Create status display for current authentication state."""
        if self.config.layout_type == "compact":
            return Static("Ready", classes="status-display compact")
        elif self.config.layout_type == "standard":
            return Container(
                Static("Status: Ready", classes="status-text"),
                classes="status-container standard"
            )
        else:  # expanded
            return Container(
                Label("Authentication Status", classes="status-label"),
                Static("Ready to authenticate",
                       classes="status-text expanded"),
                Static("", classes="status-details"),
                classes="status-container expanded"
            )

    def render_auth_screen(self, config: AuthLayoutConfig) -> None:
        """Base implementation of auth screen rendering."""
        self.config = config

    def update_progress(self, step: str, details: dict[str, str] | None = None) -> None:
        """Update the progress display."""
        self.current_step = step
        if details:
            self.progress_details.update(details)
        # Note: Widget updates should be handled by the parent Screen

    def show_error(self, error_message: str, recovery_options: list[str] | None = None) -> None:
        """Show error message with optional recovery options."""
        # Note: Widget updates should be handled by the parent Screen
        pass

    def _update_progress_widget(self, step: str, details: dict[str, str] | None = None) -> None:
        """Update progress widget with current step information."""
        # Implementation depends on specific widget structure
        pass

    def _update_status_with_error(self, error_message: str, recovery_options: list[str] | None = None) -> None:
        """Update status widget with error information."""
        # Implementation depends on specific widget structure
        pass


class CompactAuthView(BaseAuthView):
    """Authentication view optimized for small terminals (< 60 cols)."""

    def __init__(self, config: AuthLayoutConfig) -> None:
        super().__init__(config)

    def compose(self) -> ComposeResult:
        """Compose the compact authentication interface."""
        # Create minimal vertical layout for small terminals
        with Container(classes="auth-screen compact"):
            yield self._create_header()
            yield self._create_device_code_display()
            yield self._create_progress_indicator()
            yield self._create_action_buttons()

    def render_auth_screen(self, config: AuthLayoutConfig) -> None:
        """Render compact authentication screen."""
        super().render_auth_screen(config)
        # Note: Widget references are handled by the parent Screen/Container
        # that actually mounts the widgets from compose()

    def update_device_code(self, code: str, url: str) -> None:
        """Update device code display for compact layout."""
        # Note: This method is kept for interface compatibility
        # but actual updates should be handled by the parent Screen
        pass

    def _update_progress_widget(self, step: str, details: dict[str, str] | None = None) -> None:
        """Update progress for compact layout."""
        # Note: This method is kept for interface compatibility
        # but actual updates should be handled by the parent Screen
        pass


class StandardAuthView(BaseAuthView):
    """Authentication view for medium terminals (60-100 cols)."""

    def __init__(self, config: AuthLayoutConfig) -> None:
        super().__init__(config)

    def compose(self) -> ComposeResult:
        """Compose the standard authentication interface."""
        with Container(classes="auth-screen standard"):
            yield self._create_header()
            yield self._create_instructions()

            # Horizontal layout for device code and progress
            with Horizontal(classes="auth-content-row"):
                yield self._create_device_code_display()
                yield self._create_progress_indicator()

            yield self._create_status_display()
            yield self._create_action_buttons()

    def render_auth_screen(self, config: AuthLayoutConfig) -> None:
        """Render standard authentication screen."""
        super().render_auth_screen(config)
        # Note: Widget references are handled by the parent Screen/Container
        # that actually mounts the widgets from compose()

    def update_device_code(self, code: str, url: str) -> None:
        """Update device code display for standard layout."""
        # Note: This method is kept for interface compatibility
        # but actual updates should be handled by the parent Screen
        pass

    def show_countdown_timer(self, seconds: int) -> None:
        """Show countdown timer in standard layout."""
        # Note: This method is kept for interface compatibility
        # but actual updates should be handled by the parent Screen
        pass

    def _update_progress_widget(self, step: str, details: dict[str, str] | None = None) -> None:
        """Update progress for standard layout."""
        # Note: This method is kept for interface compatibility
        # but actual updates should be handled by the parent Screen
        pass


class ExpandedAuthView(BaseAuthView):
    """Authentication view for large terminals (> 100 cols)."""

    def __init__(self, config: AuthLayoutConfig) -> None:
        super().__init__(config)

    def compose(self) -> ComposeResult:
        """Compose the expanded authentication interface."""
        with Container(classes="auth-screen expanded"):
            yield self._create_header()

            # Main content area with grid layout
            with Grid(classes="auth-main-grid"):
                # Left column: Instructions and help
                with Vertical(classes="auth-left-column"):
                    yield self._create_instructions()
                    yield self._create_help_section()

                # Right column: Device code and progress
                with Vertical(classes="auth-right-column"):
                    yield self._create_device_code_display()
                    yield self._create_progress_indicator()
                    yield self._create_status_display()

            # Bottom action area
            yield self._create_action_buttons()

    def render_auth_screen(self, config: AuthLayoutConfig) -> None:
        """Render expanded authentication screen."""
        super().render_auth_screen(config)

        # Store widget references for updates
        self.widgets = {
            "header": self._create_header(),
            "instructions": self._create_instructions(),
            "device_code": self._create_device_code_display(),
            "progress": self._create_progress_indicator(),
            "status": self._create_status_display(),
            "actions": self._create_action_buttons(),
            "help": self._create_help_section()
        }

    def _create_help_section(self) -> Widget:
        """Create help section for expanded layout."""
        help_text = (
            "Troubleshooting:\n\n"
            "• Browser not opening? Copy the URL manually\n"
            "• Code expired? Click 'Retry Authentication'\n"
            "• Network issues? Check your connection\n"
            "• Still having trouble? Press 'Help' for more options"
        )

        return Container(
            Label("Help & Troubleshooting", classes="help-label"),
            Static(help_text, classes="help-text"),
            classes="help-section expanded"
        )

    def update_device_code(self, code: str, url: str) -> None:
        """Update device code display for expanded layout."""
        # Note: This method is kept for interface compatibility
        # but actual updates should be handled by the parent Screen
        pass

    def show_detailed_progress(self, step: str, details: dict[str, str] | None = None) -> None:
        """Show detailed progress information in expanded layout."""
        if "progress" in self.widgets and details:
            progress_details = "\n".join(
                [f"{k}: {v}" for k, v in details.items()])
            # Update progress widget with detailed information

    def show_network_diagnostics(self, diagnostics: dict[str, Any]) -> None:
        """Show network diagnostic information in expanded layout."""
        if "help" in self.widgets:
            # Update help section with network diagnostics
            diag_text = "Network Diagnostics:\n"
            for key, value in diagnostics.items():
                diag_text += f"• {key}: {value}\n"
            # Update help widget with diagnostic information

    def _update_progress_widget(self, step: str, details: dict[str, str] | None = None) -> None:
        """Update progress for expanded layout with detailed information."""
        detailed_progress_map = {
            "initializing": {
                "progress": 0.1,
                "status": "Initializing GitHub CLI authentication",
                "details": "Setting up secure connection to GitHub..."
            },
            "requesting_code": {
                "progress": 0.3,
                "status": "Requesting device authorization code",
                "details": "Contacting GitHub OAuth service..."
            },
            "waiting_for_user": {
                "progress": 0.5,
                "status": "Waiting for user authorization",
                "details": "Please complete authorization in your browser"
            },
            "polling_token": {
                "progress": 0.7,
                "status": "Checking authorization status",
                "details": "Polling GitHub for authorization completion..."
            },
            "validating": {
                "progress": 0.9,
                "status": "Validating authentication token",
                "details": "Verifying token and fetching user information..."
            },
            "complete": {
                "progress": 1.0,
                "status": "Authentication successful!",
                "details": "GitHub CLI is now authenticated and ready to use"
            }
        }

        if step in detailed_progress_map and "progress" in self.widgets:
            step_info = detailed_progress_map[step]
            # Update progress widget with detailed information
            # Implementation would depend on actual widget structure
