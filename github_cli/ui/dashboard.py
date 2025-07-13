"""
GitHub CLI Dashboard UI
"""

import asyncio
import os
import time
from typing import List, Dict, Any, Optional, Callable, TypeVar
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.live import Live

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError


class Dashboard:
    """Interactive dashboard for GitHub CLI"""

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.console = Console()
        
    async def run(self):
        """Run the dashboard UI"""
        # Load initial data
        await self._load_data()
        
        # Create layout
        layout = self._create_layout()
        
        # Display dashboard with live updates
        try:
            with Live(layout, refresh_per_second=1, screen=True) as live:
                while True:
                    # Update data every 30 seconds
                    await asyncio.sleep(30)
                    await self._load_data()
                    live.update(self._create_layout())
        except KeyboardInterrupt:
            # Handle clean exit on Ctrl+C
            pass
        self.running = False
        self.update_interval = 60  # Refresh every minute
        self.data = {
            "user": None,
            "repositories": [],
            "pull_requests": [],
            "issues": [],
            "notifications": [],
            "workflow_runs": []
        }

    async def start(self) -> None:
        """Start the dashboard"""
        if not self.client.authenticator.is_authenticated():
            self.terminal.display_error(
                "You must be authenticated to use the dashboard")
            return

        self.terminal.display_info("Starting GitHub dashboard...")
        self.running = True

        # Initial data load
        await self._load_data()

        try:
            # Setup layout
            layout = self._create_layout()

            with Live(layout, console=self.console, screen=True, refresh_per_second=1/4) as live:
                while self.running:
                    # Refresh data periodically
                    layout = self._create_layout()
                    live.update(layout)

                    try:
                        await asyncio.sleep(self.update_interval)
                        await self._load_data()
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        self.terminal.display_error(
                            f"Error updating dashboard: {str(e)}")

        except KeyboardInterrupt:
            self.running = False
            self.terminal.display_info("Dashboard stopped")

    async def _load_data(self) -> None:
        """Load data for the dashboard"""
        try:
            # Load user info
            if not self.data["user"]:
                self.data["user"] = await self.client.authenticator.fetch_user_info()

            # Load repositories
            try:
                response = await self.client.get("user/repos", params={"sort": "updated", "per_page": 5})
                from github_cli.models.repository import Repository
                # response.data should contain the list of repositories
                repos_data = response.data if hasattr(response, 'data') else response
                if isinstance(repos_data, list):
                    self.data["repositories"] = [
                        Repository.from_json(repo) for repo in repos_data if isinstance(repo, dict)]
                else:
                    self.data["repositories"] = []
            except Exception as e:
                self.terminal.display_error(
                    f"Error loading repositories: {str(e)}")

            # Load pull requests
            try:
                response = await self.client.get("search/issues", params={
                    "q": "is:pr is:open author:@me",
                    "sort": "updated",
                    "per_page": 5
                })
                # Extract data from APIResponse and get items
                response_data = response.data if hasattr(response, 'data') else response
                if isinstance(response_data, dict):
                    self.data["pull_requests"] = response_data.get("items", [])
                else:
                    self.data["pull_requests"] = []
            except Exception as e:
                self.terminal.display_error(
                    f"Error loading pull requests: {str(e)}")

            # Load issues
            try:
                response = await self.client.get("search/issues", params={
                    "q": "is:issue is:open assignee:@me",
                    "sort": "updated",
                    "per_page": 5
                })
                # Extract data from APIResponse and get items
                response_data = response.data if hasattr(response, 'data') else response
                if isinstance(response_data, dict):
                    self.data["issues"] = response_data.get("items", [])
                else:
                    self.data["issues"] = []
            except Exception as e:
                self.terminal.display_error(f"Error loading issues: {str(e)}")

            # Load notifications
            try:
                response = await self.client.get("notifications", params={"per_page": 5})
                self.data["notifications"] = response
            except Exception as e:
                self.terminal.display_error(
                    f"Error loading notifications: {str(e)}")

        except GitHubCLIError as e:
            self.terminal.display_error(
                f"Error loading dashboard data: {str(e)}")

    def _create_layout(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout(name="root")

        # Split layout into header, body, and footer
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=1)
        )

        # Create header
        layout["header"].update(self._create_header())

        # Split body into two columns
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )

        # Split left column for repositories and pull requests
        layout["body"]["left"].split(
            Layout(name="repositories", ratio=1),
            Layout(name="pull_requests", ratio=1)
        )

        # Split right column for issues and notifications
        layout["body"]["right"].split(
            Layout(name="issues", ratio=1),
            Layout(name="notifications", ratio=1)
        )

        # Add panels to each section
        layout["body"]["left"]["repositories"].update(
            self._create_repositories_panel())
        layout["body"]["left"]["pull_requests"].update(
            self._create_prs_panel())
        layout["body"]["right"]["issues"].update(self._create_issues_panel())
        layout["body"]["right"]["notifications"].update(
            self._create_notifications_panel())

        # Create footer
        layout["footer"].update(self._create_footer())

        return layout

    def _create_header(self) -> Panel:
        """Create the header panel"""
        user = self.data["user"] or {}
        username = user.get("login", "Unknown")

        title = Text()
        title.append("GitHub CLI", style="bold cyan")
        title.append(" | ")
        title.append(f"User: {username}", style="green")

        # Add rate limit info if available
        if self.client.rate_limit_remaining is not None:
            title.append(" | ")
            title.append(f"API Rate Limit: {self.client.rate_limit_remaining}",
                         style="yellow" if self.client.rate_limit_remaining < 100 else "green")

        return Panel(title, style="white on blue")

    def _create_repositories_panel(self) -> Panel:
        """Create the repositories panel"""
        repos = self.data["repositories"]

        if not repos:
            content = Text("No recent repositories")
            return Panel(content, title="Recent Repositories", border_style="cyan")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Repository", style="cyan")
        table.add_column("Stars", style="yellow", justify="right")
        table.add_column("Language", style="green")

        for repo in repos[:5]:  # Show up to 5 repos
            table.add_row(
                repo.full_name,
                str(repo.stargazers_count),
                repo.language or "None"
            )

        return Panel(table, title="Recent Repositories", border_style="cyan")

    def _create_prs_panel(self) -> Panel:
        """Create the pull requests panel"""
        prs = self.data["pull_requests"]

        if not prs:
            content = Text("No open pull requests")
            return Panel(content, title="Your Pull Requests", border_style="magenta")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Title", style="cyan")
        table.add_column("Repo", style="green")
        table.add_column("Updated", style="yellow")

        for pr in prs[:5]:  # Show up to 5 PRs
            # Extract repository name from URL
            repo_url = pr.get("repository_url", "")
            repo_name = repo_url.split(
                "/repos/")[-1] if "/repos/" in repo_url else ""

            # Format date
            updated = datetime.fromisoformat(
                pr.get("updated_at", "").replace("Z", "+00:00"))
            updated_str = updated.strftime("%Y-%m-%d")

            table.add_row(
                pr.get("title", "Untitled"),
                repo_name,
                updated_str
            )

        return Panel(table, title="Your Pull Requests", border_style="magenta")

    def _create_issues_panel(self) -> Panel:
        """Create the issues panel"""
        issues = self.data["issues"]

        if not issues:
            content = Text("No assigned issues")
            return Panel(content, title="Your Issues", border_style="red")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Title", style="cyan")
        table.add_column("Repo", style="green")
        table.add_column("Updated", style="yellow")

        for issue in issues[:5]:  # Show up to 5 issues
            # Extract repository name from URL
            repo_url = issue.get("repository_url", "")
            repo_name = repo_url.split(
                "/repos/")[-1] if "/repos/" in repo_url else ""

            # Format date
            updated = datetime.fromisoformat(
                issue.get("updated_at", "").replace("Z", "+00:00"))
            updated_str = updated.strftime("%Y-%m-%d")

            table.add_row(
                issue.get("title", "Untitled"),
                repo_name,
                updated_str
            )

        return Panel(table, title="Your Issues", border_style="red")

    def _create_notifications_panel(self) -> Panel:
        """Create the notifications panel"""
        notifications = self.data["notifications"]

        if not notifications:
            content = Text("No recent notifications")
            return Panel(content, title="Recent Notifications", border_style="yellow")

        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("Repository", style="green")
        table.add_column("Updated", style="yellow")

        for notif in notifications[:5]:  # Show up to 5 notifications
            # Extract notification type
            notif_type = notif.get("subject", {}).get("type", "Unknown")

            # Extract repository name
            repo = notif.get("repository", {}).get("full_name", "Unknown")

            # Format date
            updated = datetime.fromisoformat(
                notif.get("updated_at", "").replace("Z", "+00:00"))
            updated_str = updated.strftime("%Y-%m-%d")

            table.add_row(
                notif_type,
                repo,
                updated_str
            )

        return Panel(table, title="Recent Notifications", border_style="yellow")

    def _create_footer(self) -> Panel:
        """Create the footer panel"""
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        footer_text = Text()
        footer_text.append("Press Ctrl+C to exit", style="cyan")
        footer_text.append(" | ")
        footer_text.append(f"Last updated: {last_updated}", style="green")

        return Panel(footer_text, style="white on blue")
