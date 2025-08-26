"""
GitHub Notifications API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, cast
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError
from rich.table import Table
from rich import box


class NotificationsAPI:
    """API for working with GitHub Notifications"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def list_notifications(self,
                                 all: bool = False,
                                 participating: bool = False,
                                 since: Optional[str] = None,
                                 before: Optional[str] = None,
                                 per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List notifications for the authenticated user

        Args:
            all: If True, show all notifications, including ones marked as read
            participating: If True, only show notifications where the user is participating
            since: Only show notifications updated after the given time
            before: Only show notifications updated before the given time
            per_page: Number of notifications per page

        Returns:
            List of notification objects
        """
        params = {
            "all": "true" if all else "false",
            "participating": "true" if participating else "false",
            "per_page": str(per_page)
        }

        if since:
            params["since"] = since

        if before:
            params["before"] = before

        try:
            response = await self.client.get("notifications", params=params)
            return cast(List[Dict[str, Any]], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list notifications: {str(e)}")

    async def mark_as_read(self, notification_id: Optional[str] = None,
                           repo: Optional[str] = None,
                           thread_id: Optional[str] = None,
                           last_read_at: Optional[str] = None) -> bool:
        """
        Mark notifications as read

        Args:
            notification_id: Specific notification ID to mark as read
            repo: Repository to mark notifications as read (format: owner/repo)
            thread_id: Specific thread ID to mark as read
            last_read_at: Timestamp used to determine which notifications to mark as read

        Returns:
            True if successful
        """
        data = {}
        if last_read_at:
            data["last_read_at"] = last_read_at

        try:
            if thread_id:
                # Mark a specific thread as read
                endpoint = f"notifications/threads/{thread_id}"
                await self.client.patch(endpoint, data={})
            elif repo:
                # Mark all notifications in a repository as read
                endpoint = f"repos/{repo}/notifications"
                await self.client.put(endpoint, data=data)
            else:
                # Mark all notifications as read
                endpoint = "notifications"
                await self.client.put(endpoint, data=data)

            return True
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to mark notifications as read: {str(e)}")

    async def get_notification_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get a specific notification thread"""
        endpoint = f"notifications/threads/{thread_id}"

        try:
            response = await self.client.get(endpoint)
            return cast(Dict[str, Any], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to get notification thread: {str(e)}")

    async def subscribe_to_thread(self, thread_id: str, subscribed: bool, ignored: bool) -> Dict[str, Any]:
        """Subscribe or unsubscribe from a thread"""
        endpoint = f"notifications/threads/{thread_id}/subscription"
        data = {
            "subscribed": subscribed,
            "ignored": ignored
        }

        try:
            response = await self.client.put(endpoint, data=data)
            return cast(Dict[str, Any], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to update subscription: {str(e)}")


# Handler function for CLI commands
async def handle_notification_command(args: Dict[str, Any], client: GitHubClient, ui: TerminalUI) -> None:
    """Handle notification commands from the CLI"""
    notifications_api = NotificationsAPI(client, ui)

    action = args.get("action")

    if action == "list":
        all = args.get("all", False)
        participating = args.get("participating", False)
        since = args.get("since")

        try:
            ui.display_info("Fetching notifications...")
            notifications = await notifications_api.list_notifications(
                all=all,
                participating=participating,
                since=since
            )

            if not notifications:
                ui.display_info("No notifications found")
                return

            _display_notifications(notifications, ui)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "read":
        repo = args.get("repo")
        thread_id = args.get("thread")

        try:
            if thread_id:
                ui.display_info(f"Marking thread {thread_id} as read...")
                await notifications_api.mark_as_read(thread_id=thread_id)
                ui.display_success("Thread marked as read")
            elif repo:
                ui.display_info(
                    f"Marking all notifications for {repo} as read...")
                await notifications_api.mark_as_read(repo=repo)
                ui.display_success(
                    f"All notifications for {repo} marked as read")
            else:
                # Confirm before marking all as read
                confirmed = ui.confirm(
                    "Are you sure you want to mark all notifications as read", default=False)
                if not confirmed:
                    ui.display_info("Operation cancelled")
                    return

                ui.display_info("Marking all notifications as read...")
                await notifications_api.mark_as_read()
                ui.display_success("All notifications marked as read")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "subscribe":
        thread_id = args.get("thread")
        if not thread_id:
            ui.display_error("Thread ID required")
            return

        subscribed = args.get("subscribed", True)
        ignored = args.get("ignored", False)

        try:
            ui.display_info(f"Updating subscription for thread {thread_id}...")
            await notifications_api.subscribe_to_thread(thread_id, subscribed, ignored)

            if subscribed:
                ui.display_success(f"Subscribed to thread {thread_id}")
            elif ignored:
                ui.display_success(f"Ignoring thread {thread_id}")
            else:
                ui.display_success(f"Unsubscribed from thread {thread_id}")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    else:
        ui.display_error(f"Unknown notification action: {action}")
        ui.display_info("Available actions: list, read, subscribe")


def _display_notifications(notifications: List[Dict[str, Any]], ui: TerminalUI) -> None:
    """Display a list of notifications"""
    table = Table(title="Notifications", box=box.ROUNDED)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Repository", style="green")
    table.add_column("Type", style="blue")
    table.add_column("Reason", style="yellow")
    table.add_column("Subject", style="magenta")
    table.add_column("Updated", style="cyan")

    for notification in notifications:
        # Extract notification details
        notification_id = notification.get("id", "Unknown")
        repo_name = notification.get(
            "repository", {}).get("full_name", "Unknown")

        subject = notification.get("subject", {})
        subject_type = subject.get("type", "Unknown")
        subject_title = subject.get("title", "Unknown")

        reason = notification.get("reason", "Unknown")

        # Format the updated timestamp
        updated_at = notification.get("updated_at", "")
        updated = ""
        if updated_at:
            updated = datetime.fromisoformat(updated_at.replace(
                "Z", "+00:00")).strftime("%Y-%m-%d %H:%M")

        table.add_row(
            notification_id,
            repo_name,
            subject_type,
            reason,
            subject_title,
            updated
        )

    ui.console.print(table)

    # Add some helpful info
    ui.display_info(
        "\nUse 'github-cli notifications read --thread=ID' to mark a specific notification as read")
    ui.display_info(
        "Use 'github-cli notifications read' to mark all notifications as read")
