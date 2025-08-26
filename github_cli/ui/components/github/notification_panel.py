"""
Notification panel component for displaying GitHub notifications.
"""

from typing import List, Dict, Any
from datetime import datetime
from rich.panel import Panel

from github_cli.ui.components.common.panels import InfoPanel
from github_cli.ui.components.common.tables import GitHubTable


class NotificationPanel:
    """Component for displaying notification information."""

    def __init__(self) -> None:
        self.info_panel = InfoPanel()
        self.table_factory = GitHubTable("Recent Notifications")

    def create_notifications_panel(self, notifications: List[Dict[str, Any]]) -> Panel:
        """Create a panel displaying notifications."""
        if not notifications:
            return self.info_panel.create_empty_state_panel(
                "No recent notifications", "Recent Notifications"
            )

        table = self.table_factory.create_notification_table()

        for notif in notifications[:5]:  # Show up to 5 notifications
            # Extract notification type
            subject = notif.get("subject", {})
            notif_type = subject.get("type", "Unknown")

            # Extract repository name
            repository = notif.get("repository", {})
            repo_name = repository.get("full_name", "Unknown")

            # Extract subject title
            subject_title = subject.get("title", "No subject")
            if len(subject_title) > 40:
                subject_title = subject_title[:37] + "..."

            # Format date
            updated = "Unknown"
            if notif.get("updated_at"):
                try:
                    dt = datetime.fromisoformat(
                        notif["updated_at"].replace("Z", "+00:00"))
                    updated = dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    updated = "Unknown"

            table.add_row(notif_type, repo_name, subject_title, updated)

        return Panel(table, title="Recent Notifications", border_style="yellow")

    def create_notification_details_panel(self, notification: Dict[str, Any]) -> Panel:
        """Create a detailed panel for a single notification."""
        from rich.text import Text

        content = Text()

        # Notification subject
        subject = notification.get("subject", {})
        subject_title = subject.get("title", "No subject")
        subject_type = subject.get("type", "Unknown")

        content.append(f"Subject: ", style="bold")
        content.append(f"{subject_title}\n", style="cyan")

        content.append(f"Type: ", style="bold")
        content.append(f"{subject_type}\n", style="yellow")

        # Repository information
        repository = notification.get("repository", {})
        repo_name = repository.get("full_name", "Unknown")
        content.append(f"Repository: ", style="bold")
        content.append(f"{repo_name}\n", style="green")

        # Notification reason
        reason = notification.get("reason", "Unknown")
        content.append(f"Reason: ", style="bold")
        content.append(f"{reason}\n", style="blue")

        # Read status
        unread = notification.get("unread", False)
        content.append(f"Status: ", style="bold")
        status_style = "yellow" if unread else "green"
        status_text = "Unread" if unread else "Read"
        content.append(f"{status_text}\n", style=status_style)

        # Dates
        if notification.get("updated_at"):
            try:
                updated = datetime.fromisoformat(
                    notification["updated_at"].replace("Z", "+00:00"))
                content.append(f"Last Updated: ", style="bold")
                content.append(
                    f"{updated.strftime('%Y-%m-%d %H:%M')}\n", style="white")
            except (ValueError, TypeError):
                pass

        return Panel(content, title="Notification Details", border_style="yellow")
