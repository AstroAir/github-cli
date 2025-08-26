"""
Reusable table components for GitHub CLI UI.
"""

from typing import List, Dict, Any, Optional
from rich.table import Table
from rich import box


class BaseTable:
    """Base class for creating tables."""

    def __init__(self, title: Optional[str] = None, box_style: Any = box.ROUNDED):
        self.title = title
        self.box_style = box_style

    def create_table(self, show_header: bool = True) -> Table:
        """Create a basic table."""
        return Table(
            title=self.title,
            box=self.box_style,
            show_header=show_header
        )


class GitHubTable(BaseTable):
    """Table specifically designed for GitHub data."""

    def create_repository_table(self) -> Table:
        """Create a table for repositories."""
        table = self.create_table()
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        table.add_column("Language", style="magenta")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Updated", style="blue")
        return table

    def create_pull_request_table(self) -> Table:
        """Create a table for pull requests."""
        table = self.create_table()
        table.add_column("Title", style="cyan")
        table.add_column("Repository", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Updated", style="yellow")
        return table

    def create_issue_table(self) -> Table:
        """Create a table for issues."""
        table = self.create_table()
        table.add_column("Title", style="cyan")
        table.add_column("Repository", style="green")
        table.add_column("State", style="magenta")
        table.add_column("Updated", style="yellow")
        return table

    def create_notification_table(self) -> Table:
        """Create a table for notifications."""
        table = self.create_table()
        table.add_column("Type", style="cyan")
        table.add_column("Repository", style="green")
        table.add_column("Subject", style="magenta")
        table.add_column("Updated", style="yellow")
        return table
