from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, cast

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator,
    Markdown, Static, Switch, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager


class Notification(BaseModel):
    """GitHub notification data model."""
    id: str
    unread: bool
    reason: str
    updated_at: str
    last_read_at: str | None = None
    subject: dict[str, Any]
    repository: dict[str, Any]
    url: str
    subscription_url: str

    @property
    def display_title(self) -> str:
        """Get display title with status indicators."""
        unread_indicator = "🔴" if self.unread else "⚪"
        reason_emoji = {
            "assign": "👤",
            "author": "✍️",
            "comment": "💬",
            "invitation": "📨",
            "manual": "🖱️",
            "mention": "@",
            "review_requested": "👀",
            "security_alert": "🚨",
            "state_change": "🔄",
            "subscribed": "📧",
            "team_mention": "👥"
        }.get(self.reason, "📌")

        title = self.subject.get('title', 'No title')
        return f"{unread_indicator} {reason_emoji} {title}"

    @property
    def repository_name(self) -> str:
        """Get repository name."""
        return self.repository.get('full_name', 'Unknown')

    @property
    def subject_type(self) -> str:
        """Get subject type with emoji."""
        subject_type = self.subject.get('type', 'unknown')
        type_emoji = {
            "Issue": "🐛",
            "PullRequest": "🔄",
            "Release": "🚀",
            "Commit": "📝",
            "Discussion": "💭"
        }.get(subject_type, "📄")
        return f"{type_emoji} {subject_type}"

    @property
    def updated_date(self) -> str:
        """Get formatted update date."""
        try:
            dt = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return self.updated_at

    @property
    def reason_display(self) -> str:
        """Get human-readable reason."""
        return {
            "assign": "Assigned",
            "author": "Author",
            "comment": "Comment",
            "invitation": "Invitation",
            "manual": "Manual",
            "mention": "Mentioned",
            "review_requested": "Review Requested",
            "security_alert": "Security Alert",
            "state_change": "State Changed",
            "subscribed": "Subscribed",
            "team_mention": "Team Mentioned"
        }.get(self.reason, self.reason.title())


class NotificationDetailScreen(Screen[None]):
    """Detailed view for a notification with adaptive layout."""

    def __init__(self, notification: Notification, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.notification = notification
        self.client = client
        self.subject_details: dict[str, Any] = {}
        self.loading = False
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the notification detail screen with adaptive layout."""
        with Container(id="notification-detail-container", classes="adaptive-container"):
            yield Static(f"Notification: {self.notification.subject.get('title', 'No title')}", id="notification-title", classes="adaptive-title")

            with Container(id="notification-info", classes="adaptive-layout"):
                with Vertical(id="notification-basic-info", classes="adaptive-panel priority-high"):
                    yield Label(f"Repository: {self.notification.repository_name}", classes="info-item")
                    yield Label(f"Type: {self.notification.subject_type}", classes="info-item")
                    yield Label(f"Reason: {self.notification.reason_display}", classes="info-item")
                    yield Label(f"Updated: {self.notification.updated_at}", classes="info-item priority-medium")
                    yield Label(f"Status: {'Unread' if self.notification.unread else 'Read'}", classes="info-item priority-low")

                with Vertical(id="notification-actions-panel", classes="adaptive-panel priority-medium"):
                    if self.notification.unread:
                        yield Button("✅ Mark as Read", id="mark-read", variant="primary", classes="adaptive-button")
                    else:
                        yield Button("🔴 Mark as Unread", id="mark-unread", variant="warning", classes="adaptive-button")
                    yield Button("🌐 Open in Browser", id="open-browser", classes="adaptive-button priority-medium")
                    yield Button("📋 Copy URL", id="copy-url", classes="adaptive-button priority-low")
                    yield Button("🔔 Unsubscribe", id="unsubscribe", classes="adaptive-button priority-low")
                    yield Button("⬅️ Back", id="back", variant="error", classes="adaptive-button")

            with TabbedContent(id="notification-tabs", classes="adaptive-tabs"):
                with TabPane("Details", id="details-tab"):
                    with Container(id="details-content", classes="adaptive-content"):
                        yield Static("Loading details...", id="details-placeholder")

                with TabPane("Raw Data", id="raw-tab"):
                    yield Markdown(f"```json\n{self.notification.model_dump_json(indent=2)}\n```", classes="raw-data")

            yield LoadingIndicator(id="details-loading")

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        """Apply responsive layout based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes
        container = self.query_one("#notification-detail-container")
        container.remove_class("xs", "sm", "md", "lg", "xl")
        container.add_class(breakpoint.name)

        # Reorganize layout for small screens
        try:
            info_container = self.query_one("#notification-info")
            if breakpoint.name in ["xs", "sm"]:
                # Stack vertically on small screens
                info_container.add_class("vertical-stack")
                info_container.remove_class("horizontal-layout")
            else:
                # Side by side on larger screens
                info_container.add_class("horizontal-layout")
                info_container.remove_class("vertical-stack")
        except Exception:
            pass

    async def on_mount(self) -> None:
        """Initialize the detail screen."""
        details_loading = self.query_one("#details-loading")
        details_loading.display = False

        # Load subject details
        self.load_subject_details()

    @work(exclusive=True)
    async def load_subject_details(self) -> None:
        """Load detailed information about the notification subject."""
        details_loading = self.query_one("#details-loading")
        try:
            self.loading = True
            details_loading.display = True

            subject_url = self.notification.subject.get('url')
            if subject_url:
                # Extract API endpoint from URL
                api_endpoint = subject_url.replace(
                    'https://api.github.com', '')
                response = await self.client.get(api_endpoint)

                # Extract data from response
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    self.subject_details = response.data
                elif isinstance(response, dict):
                    self.subject_details = response
                else:
                    self.subject_details = {}

                # Update details content
                await self._update_details_content()

                logger.info(
                    f"Loaded details for notification {self.notification.id}")

        except GitHubCLIError as e:
            logger.error(f"Failed to load notification details: {e}")
            self.notify(f"Failed to load details: {e}", severity="error")
        finally:
            self.loading = False
            details_loading.display = False

    async def _update_details_content(self) -> None:
        """Update the details content area."""
        details_content = cast(Container, self.query_one("#details-content"))

        # Clear existing content
        await details_content.remove_children()

        if self.subject_details:
            # Show different content based on subject type
            subject_type = self.notification.subject.get('type')

            match subject_type:
                case "Issue" | "PullRequest":
                    await self._show_issue_pr_details(details_content)
                case "Release":
                    await self._show_release_details(details_content)
                case "Commit":
                    await self._show_commit_details(details_content)
                case _:
                    await details_content.mount(Static("No detailed view available for this type"))
        else:
            await details_content.mount(Static("No details available"))

    async def _show_issue_pr_details(self, container: Container) -> None:
        """Show details for issues and pull requests."""
        title = self.subject_details.get('title', 'No title')
        body = self.subject_details.get('body', '')
        state = self.subject_details.get('state', 'unknown')
        author = self.subject_details.get('user', {}).get('login', 'Unknown')

        await container.mount(Label(f"Title: {title}"))
        await container.mount(Label(f"State: {state.upper()}"))
        await container.mount(Label(f"Author: {author}"))

        if body:
            # Limit body length for display
            display_body = body[:500] + "..." if len(body) > 500 else body
            await container.mount(Markdown(display_body))

    async def _show_release_details(self, container: Container) -> None:
        """Show details for releases."""
        name = self.subject_details.get('name', 'No name')
        tag_name = self.subject_details.get('tag_name', 'No tag')
        draft = self.subject_details.get('draft', False)
        prerelease = self.subject_details.get('prerelease', False)

        await container.mount(Label(f"Release: {name}"))
        await container.mount(Label(f"Tag: {tag_name}"))
        if draft:
            await container.mount(Label("⚠️ Draft Release"))
        if prerelease:
            await container.mount(Label("🧪 Pre-release"))

    async def _show_commit_details(self, container: Container) -> None:
        """Show details for commits."""
        sha = self.subject_details.get('sha', 'No SHA')
        message = self.subject_details.get(
            'commit', {}).get('message', 'No message')
        author = self.subject_details.get('commit', {}).get(
            'author', {}).get('name', 'Unknown')

        await container.mount(Label(f"Commit: {sha[:7]}"))
        await container.mount(Label(f"Author: {author}"))
        await container.mount(Label(f"Message: {message}"))

    @on(Button.Pressed, "#mark-read")
    async def mark_as_read(self) -> None:
        """Mark notification as read."""
        try:
            await self.client.patch(f"/notifications/threads/{self.notification.id}", data={})
            self.notification.unread = False

            # Update the UI by switching buttons
            await self._update_read_status_ui()

            self.notify("Marked as read", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to mark as read: {e}")
            self.notify(f"Failed to mark as read: {e}", severity="error")

    @on(Button.Pressed, "#mark-unread")
    async def mark_as_unread(self) -> None:
        """Mark notification as unread."""
        try:
            await self.client.delete(f"/notifications/threads/{self.notification.id}/subscription")
            await self.client.put(f"/notifications/threads/{self.notification.id}/subscription", {
                "read": False
            })

            self.notification.unread = True

            # Update the UI by switching buttons
            await self._update_read_status_ui()

            self.notify("Marked as unread", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to mark as unread: {e}")
            self.notify(f"Failed to mark as unread: {e}", severity="error")

    @on(Button.Pressed, "#unsubscribe")
    async def unsubscribe(self) -> None:
        """Unsubscribe from notification thread."""
        try:
            await self.client.delete(f"/notifications/threads/{self.notification.id}/subscription")
            self.notify("Unsubscribed from thread", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to unsubscribe: {e}")
            self.notify(f"Failed to unsubscribe: {e}", severity="error")

    @on(Button.Pressed, "#open-browser")
    def open_in_browser(self) -> None:
        """Open notification in browser."""
        import webbrowser
        try:
            subject_url = self.notification.subject.get('url', '')
            if subject_url:
                # Convert API URL to web URL
                web_url = subject_url.replace(
                    'https://api.github.com/repos', 'https://github.com')
                webbrowser.open(web_url)
                self.notify("Opened in browser", severity="information")
            else:
                self.notify("No URL available", severity="warning")
        except Exception as e:
            self.notify(f"Failed to open browser: {e}", severity="error")

    @on(Button.Pressed, "#copy-url")
    def copy_url(self) -> None:
        """Copy notification URL to clipboard."""
        try:
            import pyperclip
            subject_url = self.notification.subject.get('url', '')
            if subject_url:
                web_url = subject_url.replace(
                    'https://api.github.com/repos', 'https://github.com')
                pyperclip.copy(web_url)
                self.notify("URL copied to clipboard", severity="information")
            else:
                self.notify("No URL available", severity="warning")
        except ImportError:
            self.notify(
                "pyperclip not available - install for clipboard support", severity="warning")
        except Exception as e:
            self.notify(f"Failed to copy URL: {e}", severity="error")

    async def _update_read_status_ui(self) -> None:
        """Update UI elements based on read status."""
        try:
            # Update status label by refreshing the entire widget
            # (Individual label updates are complex due to dynamic content)
            self.refresh()
        except Exception as e:
            logger.warning(f"Could not update read status UI: {e}")

    @on(Button.Pressed, "#refresh-notification")
    async def refresh_notification(self) -> None:
        """Refresh notification details."""
        self.load_subject_details()
        self.notify("Notification refreshed", severity="information")

    @on(Button.Pressed, "#back")
    def close_detail(self) -> None:
        """Close the detail screen."""
        self.dismiss()


class NotificationManager:
    """Notification management for the TUI."""

    def __init__(self, client: GitHubClient) -> None:
        self.client = client
        self.notifications: list[Notification] = []
        self.filtered_notifications: list[Notification] = []
        self.show_unread_only = True
        self.loading = False

    async def load_notifications(self, notifications_table: DataTable, unread_only: bool = True) -> None:
        """Load notifications from GitHub API."""
        if self.loading:
            return

        self.loading = True
        self.show_unread_only = unread_only
        loading_indicator = notifications_table.app.query_one(
            "#notifications-loading")
        loading_indicator.display = True

        try:
            logger.info(f"Loading notifications (unread_only={unread_only})")

            params = {
                "all": "false" if unread_only else "true",
                "per_page": 100
            }

            response = await self.client.get("/notifications", params=params)

            notifications_data = response.data if hasattr(
                response, 'data') else response

            self.notifications = []
            for notif_data in notifications_data:
                if isinstance(notif_data, dict):
                    try:
                        # Create notification with proper field mapping
                        notification = Notification(
                            id=str(notif_data.get("id", "")),
                            unread=bool(notif_data.get("unread", False)),
                            reason=str(notif_data.get("reason", "")),
                            updated_at=str(notif_data.get("updated_at", "")),
                            last_read_at=notif_data.get("last_read_at"),
                            subject=notif_data.get("subject", {}),
                            repository=notif_data.get("repository", {}),
                            url=str(notif_data.get("url", "")),
                            subscription_url=str(
                                notif_data.get("subscription_url", ""))
                        )
                        self.notifications.append(notification)
                    except (KeyError, TypeError) as e:
                        logger.warning(
                            f"Skipping notification due to data error: {e}")
                        continue
            self.filtered_notifications = self.notifications.copy()

            # Update table
            await self._update_table(notifications_table)

            logger.info(f"Loaded {len(self.notifications)} notifications")
            notifications_table.app.notify(
                f"Loaded {len(self.notifications)} notifications", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to load notifications: {e}")
            notifications_table.app.notify(
                f"Failed to load notifications: {e}", severity="error")
        except Exception as e:
            logger.error(f"Unexpected error loading notifications: {e}")
            notifications_table.app.notify(
                f"Unexpected error: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False

    async def _update_table(self, notifications_table: DataTable) -> None:
        """Update the notifications table with current data."""
        notifications_table.clear()

        for notification in self.filtered_notifications:
            notifications_table.add_row(
                notification.display_title,
                notification.repository_name,
                notification.reason_display,
                notification.updated_date,
                key=notification.id
            )

    def filter_notifications(self, search_term: str, notifications_table: DataTable) -> None:
        """Filter notifications based on search term."""
        if not search_term:
            self.filtered_notifications = self.notifications.copy()
        else:
            search_lower = search_term.lower()
            self.filtered_notifications = [
                notif for notif in self.notifications
                if search_lower in notif.subject.get('title', '').lower() or
                search_lower in notif.repository_name.lower() or
                search_lower in notif.reason.lower()
            ]

        asyncio.create_task(self._update_table(notifications_table))

    def get_notification_by_id(self, notif_id: str) -> Notification | None:
        """Get notification by ID."""
        for notification in self.notifications:
            if notification.id == notif_id:
                return notification
        return None

    async def mark_all_as_read(self, notifications_table: DataTable) -> None:
        """Mark all notifications as read."""
        try:
            await self.client.put("/notifications", data={})

            # Update local state
            for notification in self.notifications:
                notification.unread = False

            await self._update_table(notifications_table)
            notifications_table.app.notify(
                "All notifications marked as read", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to mark all as read: {e}")
            notifications_table.app.notify(
                f"Failed to mark all as read: {e}", severity="error")


class NotificationWidget(Container):
    """Complete notification management widget with adaptive capabilities."""

    def __init__(self, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.client = client
        self.notification_manager = NotificationManager(client)
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the notification widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")

        # Controls - adaptive horizontal layout
        with Horizontal(id="notification-controls", classes="adaptive-horizontal"):
            yield Input(placeholder="Search notifications...", id="notification-search", classes="adaptive-input")
            with Container(classes="switch-container priority-medium"):
                yield Switch(value=True, id="unread-only-switch", classes="adaptive-switch")
                yield Label("Unread only", classes="switch-label")
            yield Button("🔄 Refresh", id="refresh-notifications", classes="adaptive-button")
            yield Button("✅ Mark All Read", id="mark-all-read", variant="primary", classes="adaptive-button priority-medium")
            yield Button("🔕 Mark All Unread", id="mark-all-unread", variant="warning", classes="adaptive-button priority-low")

        # Notifications table with adaptive columns
        notifications_table = DataTable(
            id="notifications-table", classes="notification-table adaptive-table")
        notifications_table.add_columns(
            "Title", "Repository", "Reason", "Updated")
        yield notifications_table

        # Loading indicator
        yield LoadingIndicator(id="notifications-loading")

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        notifications_table = self.query_one("#notifications-table", DataTable)
        loading_indicator = self.query_one("#notifications-loading")
        loading_indicator.display = False

        # Apply initial responsive styles if layout manager available
        if self.layout_manager:
            self._apply_responsive_styles()

        # Load notifications (unread only by default)
        await self.notification_manager.load_notifications(notifications_table, unread_only=True)

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_styles()
            self._adapt_table_columns()

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

        # Adapt controls layout for small screens
        try:
            controls = self.query_one("#notification-controls")
            if breakpoint.compact_mode:
                controls.add_class("compact-layout")
                controls.remove_class("full-layout")
            else:
                controls.add_class("full-layout")
                controls.remove_class("compact-layout")
        except Exception:
            pass

    def _adapt_table_columns(self) -> None:
        """Adapt table columns based on breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        try:
            notifications_table = self.query_one(
                "#notifications-table", DataTable)

            # Hide/show columns based on screen size
            if breakpoint.name in ["xs", "sm"]:
                # Small screens: Show only essential columns
                self._hide_table_columns(notifications_table, [
                                         "Repository", "Updated"])
            elif breakpoint.name == "md":
                # Medium screens: Hide less important columns
                self._hide_table_columns(notifications_table, ["Updated"])
            else:
                # Large screens: Show all columns
                self._show_all_table_columns(notifications_table)

        except Exception as e:
            logger.warning(f"Could not adapt table columns: {e}")

    def _hide_table_columns(self, table: DataTable, columns: list[str]) -> None:
        """Hide specified table columns."""
        for col in columns:
            table.add_class(f"hide-{col.lower()}")

    def _show_all_table_columns(self, table: DataTable) -> None:
        """Show all table columns."""
        for col in ["repository", "reason", "updated"]:
            table.remove_class(f"hide-{col}")

    @on(Input.Changed, "#notification-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        notifications_table = self.query_one("#notifications-table", DataTable)
        self.notification_manager.filter_notifications(
            event.value, notifications_table)

    @on(Switch.Changed, "#unread-only-switch")
    async def on_unread_only_changed(self, event: Switch.Changed) -> None:
        """Handle unread only switch changes."""
        notifications_table = self.query_one("#notifications-table", DataTable)
        await self.notification_manager.load_notifications(notifications_table, unread_only=event.value)

    @on(Button.Pressed, "#refresh-notifications")
    async def on_refresh_notifications(self) -> None:
        """Handle refresh button press."""
        notifications_table = self.query_one("#notifications-table", DataTable)
        unread_switch = self.query_one("#unread-only-switch", Switch)
        await self.notification_manager.load_notifications(notifications_table, unread_only=unread_switch.value)

    @on(Button.Pressed, "#mark-all-read")
    async def on_mark_all_read(self) -> None:
        """Handle mark all read button press."""
        notifications_table = self.query_one("#notifications-table", DataTable)
        await self.notification_manager.mark_all_as_read(notifications_table)

    @on(Button.Pressed, "#mark-all-unread")
    async def on_mark_all_unread(self) -> None:
        """Handle mark all unread button press."""
        self.notify("Mark all as unread functionality coming soon",
                    severity="information")

    @on(DataTable.RowSelected, "#notifications-table")
    def on_notification_selected(self, event: DataTable.RowSelected) -> None:
        """Handle notification selection."""
        if event.row_key:
            notification = self.notification_manager.get_notification_by_id(
                str(event.row_key.value))
            if notification:
                # Pass layout manager to detail screen if available
                self.app.push_screen(NotificationDetailScreen(
                    notification, self.client, self.layout_manager))


# Function to replace placeholder in main TUI app
def create_notification_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> NotificationWidget:
    """Create a notification management widget with responsive capabilities."""
    return NotificationWidget(client, layout_manager)
