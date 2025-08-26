"""
Issue panel component for displaying GitHub issues.
"""

from typing import List, Dict, Any
from datetime import datetime
from rich.panel import Panel

from github_cli.ui.components.common.panels import InfoPanel
from github_cli.ui.components.common.tables import GitHubTable


class IssuePanel:
    """Component for displaying issue information."""

    def __init__(self) -> None:
        self.info_panel = InfoPanel()
        self.table_factory = GitHubTable("Your Issues")

    def create_issues_panel(self, issues: List[Dict[str, Any]]) -> Panel:
        """Create a panel displaying issues."""
        if not issues:
            return self.info_panel.create_empty_state_panel(
                "No assigned issues", "Your Issues"
            )

        table = self.table_factory.create_issue_table()

        for issue in issues[:5]:  # Show up to 5 issues
            # Extract data safely
            title = issue.get("title", "Untitled")
            if len(title) > 50:
                title = title[:47] + "..."

            # Extract repository name from URL
            repo_url = issue.get("repository_url", "")
            repo_name = repo_url.split(
                "/repos/")[-1] if "/repos/" in repo_url else "Unknown"

            # Format state
            state = issue.get("state", "unknown").capitalize()

            # Format date
            updated = "Unknown"
            if issue.get("updated_at"):
                try:
                    dt = datetime.fromisoformat(
                        issue["updated_at"].replace("Z", "+00:00"))
                    updated = dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    updated = "Unknown"

            table.add_row(title, repo_name, state, updated)

        return Panel(table, title="Your Issues", border_style="red")

    def create_issue_details_panel(self, issue: Dict[str, Any]) -> Panel:
        """Create a detailed panel for a single issue."""
        from rich.text import Text

        content = Text()

        # Issue title and number
        title = issue.get("title", "Untitled")
        number = issue.get("number", "Unknown")
        content.append(f"Issue #{number}: ", style="bold")
        content.append(f"{title}\n", style="cyan")

        # Issue state
        state = issue.get("state", "unknown").capitalize()
        content.append(f"State: ", style="bold")
        content.append(f"{state}\n", style="green" if state ==
                       "Open" else "red")

        # Author information
        author = issue.get("user", {}).get("login", "Unknown")
        content.append(f"Author: ", style="bold")
        content.append(f"{author}\n", style="blue")

        # Assignee information
        assignees = issue.get("assignees", [])
        if assignees:
            assignee_names = [a.get("login", "Unknown") for a in assignees]
            content.append(f"Assignees: ", style="bold")
            content.append(f"{', '.join(assignee_names)}\n", style="yellow")

        # Labels
        labels = issue.get("labels", [])
        if labels:
            label_names = [label.get("name", "Unknown") for label in labels]
            content.append(f"Labels: ", style="bold")
            content.append(f"{', '.join(label_names)}\n", style="magenta")

        # Repository information
        repo_url = issue.get("repository_url", "")
        repo_name = repo_url.split(
            "/repos/")[-1] if "/repos/" in repo_url else "Unknown"
        content.append(f"Repository: ", style="bold")
        content.append(f"{repo_name}\n", style="cyan")

        # Dates
        if issue.get("created_at"):
            try:
                created = datetime.fromisoformat(
                    issue["created_at"].replace("Z", "+00:00"))
                content.append(f"Created: ", style="bold")
                content.append(
                    f"{created.strftime('%Y-%m-%d %H:%M')}\n", style="white")
            except (ValueError, TypeError):
                pass

        return Panel(content, title="Issue Details", border_style="red")
