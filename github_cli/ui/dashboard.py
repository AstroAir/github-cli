"""GitHub CLI Dashboard UI - Refactored for better organization.

This module provides backward compatibility while using the new modular components.
"""
import asyncio
from typing import Optional
from rich.console import Console
from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI

# Import the new modular dashboard components
from .dashboard import Dashboard as ModularDashboard


class Dashboard:
    """
    Backward-compatible wrapper for the modular dashboard.

    This class maintains the same API as the original Dashboard while
    delegating to the new modular implementation.
    """

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.console = Console()

        # Use the new modular dashboard
        self._dashboard = ModularDashboard(client, terminal)

        # Maintain backward compatibility properties
        self.running = False
        self.update_interval = 60
        self.data = {}

    async def run(self) -> None:
        """Run the dashboard UI (legacy method)."""
        await self.start()

    async def start(self) -> None:
        """Start the dashboard."""
        await self._dashboard.start()

        # Update legacy properties for backward compatibility
        self.running = self._dashboard.running
        self.data = self._dashboard.get_cached_data()

    def stop(self) -> None:
        """Stop the dashboard."""
        self._dashboard.stop()
        self.running = False

    # Legacy methods for backward compatibility
    async def _load_data(self) -> None:
        """Load data for the dashboard (legacy method)."""
        await self._dashboard.refresh_data()
        self.data = self._dashboard.get_cached_data()

    def _create_layout(self):
        """Create the dashboard layout (legacy method)."""
        data = self._dashboard.get_cached_data()
        return self._dashboard.layout_manager.create_layout(data)

    def _create_header(self):
        """Create the header panel (legacy method)."""
        data = self._dashboard.get_cached_data()
        return self._dashboard.layout_manager._create_header(data)

    def _create_repositories_panel(self):
        """Create the repositories panel (legacy method)."""
        data = self._dashboard.get_cached_data()
        repos = data.get("repositories", [])
        return self._dashboard.layout_manager.repo_panel.create_repositories_panel(repos)

    def _create_prs_panel(self):
        """Create the pull requests panel (legacy method)."""
        data = self._dashboard.get_cached_data()
        prs = data.get("pull_requests", [])
        return self._dashboard.layout_manager.pr_panel.create_pull_requests_panel(prs)

    def _create_issues_panel(self):
        """Create the issues panel (legacy method)."""
        data = self._dashboard.get_cached_data()
        issues = data.get("issues", [])
        return self._dashboard.layout_manager.issue_panel.create_issues_panel(issues)

    def _create_notifications_panel(self):
        """Create the notifications panel (legacy method)."""
        data = self._dashboard.get_cached_data()
        notifications = data.get("notifications", [])
        return self._dashboard.layout_manager.notification_panel.create_notifications_panel(notifications)

    def _create_footer(self):
        """Create the footer panel (legacy method)."""
        return self._dashboard.layout_manager._create_footer()

    # New enhanced methods
    async def refresh_data(self) -> None:
        """Manually refresh dashboard data."""
        await self._dashboard.refresh_data()
        self.data = self._dashboard.get_cached_data()

    def get_cached_data(self) -> dict:
        """Get currently cached data."""
        return self._dashboard.get_cached_data()

    def clear_cache(self) -> None:
        """Clear dashboard cache."""
        self._dashboard.clear_cache()
        self.data = {}

    def set_update_interval(self, seconds: int) -> None:
        """Set the update interval in seconds."""
        self._dashboard.set_update_interval(seconds)
        self.update_interval = seconds
