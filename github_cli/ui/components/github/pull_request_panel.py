"""
Pull request panel component for displaying GitHub pull requests.
"""

from typing import List, Dict, Any
from datetime import datetime
from rich.panel import Panel

from github_cli.ui.components.common.panels import InfoPanel
from github_cli.ui.components.common.tables import GitHubTable


class PullRequestPanel:
    """Component for displaying pull request information."""

    def __init__(self) -> None:
        self.info_panel = InfoPanel()
        self.table_factory = GitHubTable("Your Pull Requests")

    def create_pull_requests_panel(self, prs: List[Dict[str, Any]]) -> Panel:
        """Create a panel displaying pull requests."""
        if not prs:
            return self.info_panel.create_empty_state_panel(
                "No open pull requests", "Your Pull Requests"
            )

        table = self.table_factory.create_pull_request_table()

        for pr in prs[:5]:  # Show up to 5 PRs
            # Extract data safely
            title = pr.get("title", "Untitled")
            if len(title) > 50:
                title = title[:47] + "..."

            # Extract repository name from URL
            repo_url = pr.get("repository_url", "")
            repo_name = repo_url.split(
                "/repos/")[-1] if "/repos/" in repo_url else "Unknown"

            # Format status
            status = pr.get("state", "unknown").capitalize()
            if pr.get("draft", False):
                status = "Draft"

            # Format date
            updated = "Unknown"
            if pr.get("updated_at"):
                try:
                    dt = datetime.fromisoformat(
                        pr["updated_at"].replace("Z", "+00:00"))
                    updated = dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    updated = "Unknown"

            table.add_row(title, repo_name, status, updated)

        return Panel(table, title="Your Pull Requests", border_style="magenta")

    def create_pull_request_details_panel(self, pr: Dict[str, Any]) -> Panel:
        """Create a detailed panel for a single pull request."""
        from rich.text import Text

        content = Text()

        # PR title and number
        title = pr.get("title", "Untitled")
        number = pr.get("number", "Unknown")
        content.append(f"PR #{number}: ", style="bold")
        content.append(f"{title}\n", style="cyan")

        # PR state and metadata
        state = pr.get("state", "unknown").capitalize()
        content.append(f"State: ", style="bold")
        content.append(f"{state}\n", style="green" if state ==
                       "Open" else "red")

        if pr.get("draft", False):
            content.append("Status: ", style="bold")
            content.append("Draft\n", style="yellow")

        # Author information
        author = pr.get("user", {}).get("login", "Unknown")
        content.append(f"Author: ", style="bold")
        content.append(f"{author}\n", style="blue")

        # Repository information
        repo_url = pr.get("repository_url", "")
        repo_name = repo_url.split(
            "/repos/")[-1] if "/repos/" in repo_url else "Unknown"
        content.append(f"Repository: ", style="bold")
        content.append(f"{repo_name}\n", style="cyan")

        # Dates
        if pr.get("created_at"):
            try:
                created = datetime.fromisoformat(
                    pr["created_at"].replace("Z", "+00:00"))
                content.append(f"Created: ", style="bold")
                content.append(
                    f"{created.strftime('%Y-%m-%d %H:%M')}\n", style="white")
            except (ValueError, TypeError):
                pass

        return Panel(content, title="Pull Request Details", border_style="magenta")
