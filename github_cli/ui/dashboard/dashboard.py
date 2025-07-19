"""
Refactored Dashboard component with improved organization.
"""

import asyncio
from typing import Optional
from rich.console import Console
from rich.live import Live

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from .data_loader import DashboardDataLoader
from .layout_manager import DashboardLayoutManager


class Dashboard:
    """Interactive dashboard for GitHub CLI with modular components."""

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.console = Console()
        self.running = False
        self.update_interval = 60  # Refresh every minute
        
        # Initialize components
        self.data_loader = DashboardDataLoader(client, terminal)
        self.layout_manager = DashboardLayoutManager()

    async def start(self) -> None:
        """Start the dashboard."""
        if not self.client.authenticator.is_authenticated():
            self.terminal.display_error(
                "You must be authenticated to use the dashboard")
            return

        self.terminal.display_info("Starting GitHub dashboard...")
        self.running = True

        # Initial data load
        data = await self.data_loader.load_all_data()
        
        # Add rate limit info to data if available
        if hasattr(self.client, 'rate_limit_remaining') and self.client.rate_limit_remaining is not None:
            data["rate_limit_info"] = {"remaining": self.client.rate_limit_remaining}

        try:
            # Setup layout
            layout = self.layout_manager.create_layout(data)

            with Live(layout, console=self.console, screen=True, refresh_per_second=1/4) as live:
                while self.running:
                    # Refresh data periodically
                    data = await self.data_loader.load_all_data()
                    
                    # Update rate limit info
                    if hasattr(self.client, 'rate_limit_remaining') and self.client.rate_limit_remaining is not None:
                        data["rate_limit_info"] = {"remaining": self.client.rate_limit_remaining}
                    
                    layout = self.layout_manager.create_layout(data)
                    live.update(layout)

                    try:
                        await asyncio.sleep(self.update_interval)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        self.terminal.display_error(
                            f"Error updating dashboard: {str(e)}")

        except KeyboardInterrupt:
            self.running = False
            self.terminal.display_info("Dashboard stopped")

    def stop(self) -> None:
        """Stop the dashboard."""
        self.running = False

    async def refresh_data(self) -> None:
        """Manually refresh dashboard data."""
        await self.data_loader.load_all_data()

    def get_cached_data(self) -> dict:
        """Get currently cached data."""
        return self.data_loader.get_cached_data()

    def clear_cache(self) -> None:
        """Clear dashboard cache."""
        self.data_loader.clear_cache()

    def set_update_interval(self, seconds: int) -> None:
        """Set the update interval in seconds."""
        if seconds > 0:
            self.update_interval = seconds

    def create_compact_view(self) -> None:
        """Switch to compact view for smaller terminals."""
        # This could be implemented to switch layout managers
        pass
