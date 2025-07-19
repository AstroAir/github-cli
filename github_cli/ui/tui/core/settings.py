from __future__ import annotations

from typing import Generator, Any, cast
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, Checkbox, Input, Label, Static,
    Switch, TabbedContent, TabPane, LoadingIndicator
)
from textual.widgets._select import Select
from loguru import logger

from github_cli.utils.config import Config
# Add responsive imports
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager


class SettingsWidget(Container):
    """Complete settings and configuration widget with adaptive capabilities."""

    # Valid theme options
    VALID_THEMES = ["auto", "light", "dark", "github", "monokai"]

    def __init__(self, config: Config, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.config = config
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def _validate_numeric_input(self, value: str, min_val: int = 1, max_val: int = 9999) -> bool:
        """Validate numeric input within range."""
        try:
            num_val = int(value)
            return min_val <= num_val <= max_val
        except ValueError:
            return False

    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        if not url:
            return False
        return url.startswith(('http://', 'https://')) and '.' in url

    def compose(self) -> ComposeResult:
        """Compose the settings widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")

        with TabbedContent(id="settings-tabs", classes="adaptive-tabs"):
            # General settings
            with TabPane("General", id="general-tab"):
                with Container(id="general-settings", classes="settings-section adaptive-panel"):
                    yield Static("General Settings", classes="settings-title")

                    # Default repository view
                    with Container(classes="setting-row adaptive-horizontal priority-high"):
                        yield Label("Default Repository View:", classes="setting-label")
                        yield Select(
                            options=[
                                ("List View", "list"),
                                ("Grid View", "grid"),
                                ("Tree View", "tree")
                            ],
                            value=self.config.get(
                                "ui.default_repo_view", "list"),
                            id="default-repo-view",
                            classes="adaptive-select"
                        )

                    # Items per page
                    with Container(classes="setting-row adaptive-horizontal priority-medium"):
                        yield Label("Items per Page:", classes="setting-label")
                        yield Select(
                            options=[
                                ("25", "25"),
                                ("50", "50"),
                                ("100", "100")
                            ],
                            value=str(self.config.get(
                                "ui.items_per_page", "50")),
                            id="items-per-page",
                            classes="adaptive-select"
                        )

                    # Auto-refresh interval with validation
                    with Container(classes="setting-row adaptive-horizontal priority-medium"):
                        yield Label("Auto-refresh Interval (seconds):", classes="setting-label")
                        yield Input(
                            value=str(self.config.get(
                                "ui.auto_refresh_interval", "60")),
                            id="auto-refresh-interval",
                            classes="adaptive-input numeric-input",
                            placeholder="60"
                        )

                    # Enable auto-refresh
                    with Container(classes="setting-row adaptive-horizontal priority-low"):
                        yield Label("Enable Auto-refresh:", classes="setting-label")
                        yield Switch(
                            value=self.config.get(
                                "ui.auto_refresh_enabled", True),
                            id="auto-refresh-enabled",
                            classes="adaptive-switch"
                        )

                    # Show tooltips
                    with Container(classes="setting-row adaptive-horizontal priority-low"):
                        yield Label("Show Tooltips:", classes="setting-label")
                        yield Switch(
                            value=self.config.get("ui.show_tooltips", True),
                            id="show-tooltips",
                            classes="adaptive-switch"
                        )

            # Appearance settings
            with TabPane("Appearance", id="appearance-tab"):
                with Container(id="appearance-settings", classes="settings-section adaptive-panel"):
                    yield Static("Appearance Settings", classes="settings-title")

                    # Theme selection
                    with Container(classes="setting-row adaptive-horizontal priority-high"):
                        yield Label("Theme:")
                        yield Select(
                            options=[
                                ("Auto (System)", "auto"),
                                ("Light", "light"),
                                ("Dark", "dark"),
                                ("GitHub", "github"),
                                ("Monokai", "monokai")
                            ],
                            value=self._validate_theme(
                                self.config.get("ui.theme", "auto")),
                            id="theme-select"
                        )

                    # Color scheme
                    with Horizontal(classes="setting-row"):
                        yield Label("Color Scheme:")
                        yield Select(
                            options=[
                                ("Default", "default"),
                                ("GitHub", "github"),
                                ("Vibrant", "vibrant"),
                                ("Minimal", "minimal")
                            ],
                            value=self.config.get(
                                "ui.color_scheme", "default"),
                            id="color-scheme"
                        )

                    # Font size
                    with Horizontal(classes="setting-row"):
                        yield Label("Font Size:")
                        yield Select(
                            options=[
                                ("Small", "small"),
                                ("Medium", "medium"),
                                ("Large", "large")
                            ],
                            value=self.config.get("ui.font_size", "medium"),
                            id="font-size"
                        )

                    # Show line numbers
                    with Horizontal(classes="setting-row"):
                        yield Label("Show Line Numbers in Code:")
                        yield Switch(
                            value=self.config.get(
                                "ui.show_line_numbers", True),
                            id="show-line-numbers"
                        )

                    # Syntax highlighting
                    with Horizontal(classes="setting-row"):
                        yield Label("Enable Syntax Highlighting:")
                        yield Switch(
                            value=self.config.get(
                                "ui.syntax_highlighting", True),
                            id="syntax-highlighting"
                        )

                    # Show status bar
                    with Horizontal(classes="setting-row"):
                        yield Label("Show Status Bar:")
                        yield Switch(
                            value=self.config.get("ui.show_status_bar", True),
                            id="show-status-bar"
                        )

            # API settings
            with TabPane("API", id="api-tab"):
                with Container(id="api-settings", classes="settings-section"):
                    yield Static("API Settings", classes="settings-title")

                    # API timeout with validation
                    with Horizontal(classes="setting-row"):
                        yield Label("API Timeout (seconds):")
                        yield Input(
                            value=str(self.config.get("api.timeout", "30")),
                            id="api-timeout",
                            placeholder="30",
                            classes="numeric-input"
                        )

                    # Max retries
                    with Horizontal(classes="setting-row"):
                        yield Label("Max Retries:")
                        yield Select(
                            options=[
                                ("1", "1"),
                                ("3", "3"),
                                ("5", "5")
                            ],
                            value=str(self.config.get("api.max_retries", "3")),
                            id="max-retries"
                        )

                    # Cache enabled
                    with Horizontal(classes="setting-row"):
                        yield Label("Enable API Caching:")
                        yield Switch(
                            value=self.config.get("api.cache_enabled", True),
                            id="cache-enabled"
                        )

                    # Cache TTL with validation
                    with Horizontal(classes="setting-row"):
                        yield Label("Cache TTL (seconds):")
                        yield Input(
                            value=str(self.config.get("api.cache_ttl", "300")),
                            id="cache-ttl",
                            placeholder="300",
                            classes="numeric-input"
                        )

                    # Rate limiting
                    with Horizontal(classes="setting-row"):
                        yield Label("Respect Rate Limits:")
                        yield Switch(
                            value=self.config.get(
                                "api.respect_rate_limits", True),
                            id="respect-rate-limits"
                        )

                    # API base URL (for GitHub Enterprise) with validation
                    with Horizontal(classes="setting-row"):
                        yield Label("API Base URL:")
                        yield Input(
                            value=self.config.get(
                                "api.base_url", "https://api.github.com"),
                            id="api-base-url",
                            placeholder="https://api.github.com",
                            classes="url-input"
                        )

            # Notifications settings
            with TabPane("Notifications", id="notifications-tab"):
                with Container(id="notifications-settings", classes="settings-section"):
                    yield Static("Notification Settings", classes="settings-title")

                    # Enable desktop notifications
                    with Horizontal(classes="setting-row"):
                        yield Label("Desktop Notifications:")
                        yield Switch(
                            value=self.config.get(
                                "notifications.desktop_enabled", False),
                            id="desktop-notifications"
                        )

                    # Notification types
                    yield Static("Notification Types:", classes="subsection-title")

                    with Vertical(classes="checkbox-group"):
                        yield Checkbox(
                            "Pull Request Updates",
                            value=self.config.get(
                                "notifications.pr_updates", True),
                            id="notif-pr-updates"
                        )
                        yield Checkbox(
                            "Issue Updates",
                            value=self.config.get(
                                "notifications.issue_updates", True),
                            id="notif-issue-updates"
                        )
                        yield Checkbox(
                            "Review Requests",
                            value=self.config.get(
                                "notifications.review_requests", True),
                            id="notif-review-requests"
                        )
                        yield Checkbox(
                            "Action Failures",
                            value=self.config.get(
                                "notifications.action_failures", True),
                            id="notif-action-failures"
                        )
                        yield Checkbox(
                            "Security Alerts",
                            value=self.config.get(
                                "notifications.security_alerts", True),
                            id="notif-security-alerts"
                        )

                    # Check interval
                    with Horizontal(classes="setting-row"):
                        yield Label("Check Interval (minutes):")
                        yield Select(
                            options=[
                                ("5", "5"),
                                ("10", "10"),
                                ("15", "15"),
                                ("30", "30")
                            ],
                            value=str(self.config.get(
                                "notifications.check_interval", "10")),
                            id="notification-interval"
                        )

            # Advanced settings
            with TabPane("Advanced", id="advanced-tab"):
                with Container(id="advanced-settings", classes="settings-section"):
                    yield Static("Advanced Settings", classes="settings-title")

                    # Debug mode
                    with Horizontal(classes="setting-row"):
                        yield Label("Debug Mode:")
                        yield Switch(
                            value=self.config.get("debug.enabled", False),
                            id="debug-mode"
                        )

                    # Log level
                    with Horizontal(classes="setting-row"):
                        yield Label("Log Level:")
                        yield Select(
                            options=[
                                ("DEBUG", "DEBUG"),
                                ("INFO", "INFO"),
                                ("WARNING", "WARNING"),
                                ("ERROR", "ERROR")
                            ],
                            value=self.config.get("debug.log_level", "INFO"),
                            id="log-level"
                        )

                    # Performance monitoring
                    with Horizontal(classes="setting-row"):
                        yield Label("Performance Monitoring:")
                        yield Switch(
                            value=self.config.get(
                                "performance.monitoring_enabled", False),
                            id="performance-monitoring"
                        )

                    # Enable plugins
                    with Horizontal(classes="setting-row"):
                        yield Label("Enable Plugins:")
                        yield Switch(
                            value=self.config.get("plugins.enabled", True),
                            id="plugins-enabled"
                        )

                    # Plugin directory
                    with Horizontal(classes="setting-row"):
                        yield Label("Plugin Directory:")
                        yield Input(
                            value=self.config.get(
                                "plugins.directory", "~/.github-cli/plugins"),
                            id="plugin-directory"
                        )

                    # Experimental features
                    with Horizontal(classes="setting-row"):
                        yield Label("Enable Experimental Features:")
                        yield Switch(
                            value=self.config.get(
                                "experimental.enabled", False),
                            id="experimental-features"
                        )

        # Action buttons with adaptive layout
        with Horizontal(id="settings-actions", classes="adaptive-horizontal"):
            yield Button("💾 Save Settings", id="save-settings", variant="primary", classes="adaptive-button")
            yield Button("🔄 Reset to Defaults", id="reset-settings", variant="error", classes="adaptive-button priority-medium")
            yield Button("📥 Import Settings", id="import-settings", classes="adaptive-button priority-low")
            yield Button("📤 Export Settings", id="export-settings", classes="adaptive-button priority-low")
            yield Button("🔍 Validate Settings", id="validate-settings", classes="adaptive-button priority-medium")

        # Loading indicator for long operations
        yield LoadingIndicator(id="settings-loading")

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        # Apply initial responsive styles if layout manager available
        if self.layout_manager:
            self._apply_responsive_styles()

        # Hide loading indicator initially
        loading_indicator = self.query_one("#settings-loading")
        loading_indicator.display = False

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_styles()

    @on(Input.Changed, ".numeric-input")
    def validate_numeric_input(self, event: Input.Changed) -> None:
        """Validate numeric inputs in real-time."""
        if event.value and not self._validate_numeric_input(event.value):
            event.input.add_class("input-error")
            self.notify("Please enter a valid number (1-9999)",
                        severity="warning")
        else:
            event.input.remove_class("input-error")

    @on(Input.Changed, ".url-input")
    def validate_url_input(self, event: Input.Changed) -> None:
        """Validate URL inputs in real-time."""
        if event.value and not self._validate_url(event.value):
            event.input.add_class("input-error")
            self.notify("Please enter a valid URL", severity="warning")
        else:
            event.input.remove_class("input-error")
        """Apply responsive styles based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes
        self.remove_class("xs", "sm", "md", "lg", "xl")
        self.add_class(breakpoint.name)

        # Adapt setting rows layout for small screens
        try:
            if breakpoint.name in ["xs", "sm"]:
                # Stack labels and controls vertically on small screens
                for setting_row in self.query(".setting-row"):
                    setting_row.add_class("vertical-stack")
                    setting_row.remove_class("horizontal-layout")
            else:
                # Side by side on larger screens
                for setting_row in self.query(".setting-row"):
                    setting_row.add_class("horizontal-layout")
                    setting_row.remove_class("vertical-stack")
        except Exception:
            pass

    @on(Button.Pressed, "#save-settings")
    async def save_settings(self) -> None:
        """Save all settings to configuration with validation."""
        loading_indicator = self.query_one("#settings-loading")

        try:
            loading_indicator.display = True

            # Validate all inputs before saving
            if not self._validate_all_inputs():
                self.notify(
                    "Please fix validation errors before saving", severity="error")
                return
            # Get typed widget values
            default_repo_view = cast(
                Select[str], self.query_one("#default-repo-view"))
            items_per_page = cast(
                Select[str], self.query_one("#items-per-page"))
            auto_refresh_interval = cast(
                Input, self.query_one("#auto-refresh-interval"))
            auto_refresh_enabled = cast(
                Switch, self.query_one("#auto-refresh-enabled"))
            show_tooltips = cast(Switch, self.query_one("#show-tooltips"))

            theme_select = cast(Select[str], self.query_one("#theme-select"))
            color_scheme = cast(Select[str], self.query_one("#color-scheme"))
            font_size = cast(Select[str], self.query_one("#font-size"))
            show_line_numbers = cast(
                Switch, self.query_one("#show-line-numbers"))
            syntax_highlighting = cast(
                Switch, self.query_one("#syntax-highlighting"))
            show_status_bar = cast(Switch, self.query_one("#show-status-bar"))

            api_timeout = cast(Input, self.query_one("#api-timeout"))
            max_retries = cast(Select[str], self.query_one("#max-retries"))
            cache_enabled = cast(Switch, self.query_one("#cache-enabled"))
            cache_ttl = cast(Input, self.query_one("#cache-ttl"))
            respect_rate_limits = cast(
                Switch, self.query_one("#respect-rate-limits"))
            api_base_url = cast(Input, self.query_one("#api-base-url"))

            desktop_notifications = cast(
                Switch, self.query_one("#desktop-notifications"))
            notif_pr_updates = cast(
                Checkbox, self.query_one("#notif-pr-updates"))
            notif_issue_updates = cast(
                Checkbox, self.query_one("#notif-issue-updates"))
            notif_review_requests = cast(
                Checkbox, self.query_one("#notif-review-requests"))
            notif_action_failures = cast(
                Checkbox, self.query_one("#notif-action-failures"))
            notif_security_alerts = cast(
                Checkbox, self.query_one("#notif-security-alerts"))
            notification_interval = cast(
                Select[str], self.query_one("#notification-interval"))

            debug_mode = cast(Switch, self.query_one("#debug-mode"))
            log_level = cast(Select[str], self.query_one("#log-level"))
            performance_monitoring = cast(
                Switch, self.query_one("#performance-monitoring"))
            plugins_enabled = cast(Switch, self.query_one("#plugins-enabled"))
            plugin_directory = cast(Input, self.query_one("#plugin-directory"))
            experimental_features = cast(
                Switch, self.query_one("#experimental-features"))

            # General settings
            self.config.set("ui.default_repo_view", default_repo_view.value)
            if items_per_page.value != items_per_page.BLANK:
                self.config.set("ui.items_per_page", int(
                    str(items_per_page.value)))
            self.config.set("ui.auto_refresh_interval",
                            int(auto_refresh_interval.value))
            self.config.set("ui.auto_refresh_enabled",
                            auto_refresh_enabled.value)
            self.config.set("ui.show_tooltips", show_tooltips.value)

            # Appearance settings
            self.config.set("ui.theme", theme_select.value)
            self.config.set("ui.color_scheme", color_scheme.value)
            self.config.set("ui.font_size", font_size.value)
            self.config.set("ui.show_line_numbers", show_line_numbers.value)
            self.config.set("ui.syntax_highlighting",
                            syntax_highlighting.value)
            self.config.set("ui.show_status_bar", show_status_bar.value)

            # API settings
            self.config.set("api.timeout", int(api_timeout.value))
            if max_retries.value != max_retries.BLANK:
                self.config.set("api.max_retries", int(str(max_retries.value)))
            self.config.set("api.cache_enabled", cache_enabled.value)
            self.config.set("api.cache_ttl", int(cache_ttl.value))
            self.config.set("api.respect_rate_limits",
                            respect_rate_limits.value)
            self.config.set("api.base_url", api_base_url.value)

            # Notification settings
            self.config.set("notifications.desktop_enabled",
                            desktop_notifications.value)
            self.config.set("notifications.pr_updates", notif_pr_updates.value)
            self.config.set("notifications.issue_updates",
                            notif_issue_updates.value)
            self.config.set("notifications.review_requests",
                            notif_review_requests.value)
            self.config.set("notifications.action_failures",
                            notif_action_failures.value)
            self.config.set("notifications.security_alerts",
                            notif_security_alerts.value)
            if notification_interval.value != notification_interval.BLANK:
                self.config.set("notifications.check_interval",
                                int(str(notification_interval.value)))

            # Advanced settings
            self.config.set("debug.enabled", debug_mode.value)
            self.config.set("debug.log_level", log_level.value)
            self.config.set("performance.monitoring_enabled",
                            performance_monitoring.value)
            self.config.set("plugins.enabled", plugins_enabled.value)
            self.config.set("plugins.directory", plugin_directory.value)
            self.config.set("experimental.enabled",
                            experimental_features.value)

            # Save to file
            self.config.save()

            self.notify("Settings saved successfully!", severity="information")
            logger.info("Settings saved successfully")

        except Exception as e:
            self.notify(f"Failed to save settings: {e}", severity="error")
            logger.error(f"Failed to save settings: {e}")
        finally:
            loading_indicator.display = False

    @on(Button.Pressed, "#reset-settings")
    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        try:
            self.config.reset()
            self.config.save()

            # Refresh the UI with default values
            self._refresh_ui_values()

            self.notify("Settings reset to defaults", severity="information")
            logger.info("Settings reset to defaults")

        except Exception as e:
            self.notify(f"Failed to reset settings: {e}", severity="error")
            logger.error(f"Failed to reset settings: {e}")

    @on(Button.Pressed, "#import-settings")
    def import_settings(self) -> None:
        """Import settings from file."""
        self.notify("Import settings functionality coming soon",
                    severity="information")

    @on(Button.Pressed, "#validate-settings")
    def validate_all_settings(self) -> None:
        """Validate all current settings."""
        if self._validate_all_inputs():
            self.notify("All settings are valid ✅", severity="information")
        else:
            self.notify("Some settings have validation errors ❌",
                        severity="warning")

    def _validate_all_inputs(self) -> bool:
        """Validate all input fields and return True if all are valid."""
        all_valid = True

        # Validate numeric inputs
        for widget in self.query(".numeric-input"):
            if hasattr(widget, 'value'):
                input_widget = cast(Input, widget)
                if input_widget.value and not self._validate_numeric_input(input_widget.value):
                    input_widget.add_class("input-error")
                    all_valid = False
                else:
                    input_widget.remove_class("input-error")

        # Validate URL inputs
        for widget in self.query(".url-input"):
            if hasattr(widget, 'value'):
                input_widget = cast(Input, widget)
                if input_widget.value and not self._validate_url(input_widget.value):
                    input_widget.add_class("input-error")
                    all_valid = False
                else:
                    input_widget.remove_class("input-error")

        return all_valid

    def _refresh_ui_values(self) -> None:
        """Refresh UI elements with current config values."""
        try:
            # General settings
            default_repo_view = cast(
                Select[str], self.query_one("#default-repo-view"))
            items_per_page = cast(
                Select[str], self.query_one("#items-per-page"))
            auto_refresh_interval = cast(
                Input, self.query_one("#auto-refresh-interval"))
            auto_refresh_enabled = cast(
                Switch, self.query_one("#auto-refresh-enabled"))
            show_tooltips = cast(Switch, self.query_one("#show-tooltips"))

            theme_select = cast(Select[str], self.query_one("#theme-select"))
            color_scheme = cast(Select[str], self.query_one("#color-scheme"))
            font_size = cast(Select[str], self.query_one("#font-size"))
            show_line_numbers = cast(
                Switch, self.query_one("#show-line-numbers"))
            syntax_highlighting = cast(
                Switch, self.query_one("#syntax-highlighting"))
            show_status_bar = cast(Switch, self.query_one("#show-status-bar"))

            default_repo_view.value = self.config.get(
                "ui.default_repo_view", "list")
            items_per_page.value = str(
                self.config.get("ui.items_per_page", "50"))
            auto_refresh_interval.value = str(
                self.config.get("ui.auto_refresh_interval", "60"))
            auto_refresh_enabled.value = self.config.get(
                "ui.auto_refresh_enabled", True)
            show_tooltips.value = self.config.get("ui.show_tooltips", True)

            # Appearance settings
            theme_select.value = self._validate_theme(
                self.config.get("ui.theme", "auto"))
            color_scheme.value = self.config.get("ui.color_scheme", "default")
            font_size.value = self.config.get("ui.font_size", "medium")
            show_line_numbers.value = self.config.get(
                "ui.show_line_numbers", True)
            syntax_highlighting.value = self.config.get(
                "ui.syntax_highlighting", True)
            show_status_bar.value = self.config.get("ui.show_status_bar", True)
            # Continue for other sections...
        except Exception as e:
            logger.warning(f"Failed to refresh some UI values: {e}")

    def _apply_responsive_styles(self) -> None:
        """Apply responsive styles based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes
        self.remove_class("xs", "sm", "md", "lg", "xl")
        self.add_class(breakpoint.name)

        # Adapt setting rows layout for small screens
        try:
            if breakpoint.name in ["xs", "sm"]:
                # Stack labels and controls vertically on small screens
                for setting_row in self.query(".setting-row"):
                    setting_row.add_class("vertical-stack")
                    setting_row.remove_class("horizontal-layout")
            else:
                # Side by side on larger screens
                for setting_row in self.query(".setting-row"):
                    setting_row.add_class("horizontal-layout")
                    setting_row.remove_class("vertical-stack")
        except Exception:
            pass

    def _validate_theme(self, theme: str) -> str:
        """Validate and return a valid theme value."""
        if theme in self.VALID_THEMES:
            return theme
        logger.warning(f"Invalid theme '{theme}', falling back to 'auto'")
        return "auto"


# Function to replace placeholder in main TUI app
def create_settings_widget(config: Config, layout_manager: ResponsiveLayoutManager | None = None) -> SettingsWidget:
    """Create a settings widget with responsive capabilities."""
    return SettingsWidget(config, layout_manager)
