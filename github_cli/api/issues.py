"""
GitHub Issues API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, cast
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError
from github_cli.models.issue import Issue
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box


class IssuesAPI:
    """API for working with GitHub Issues"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def list_issues(self,
                          repo: Optional[str] = None,
                          state: str = "open",
                          labels: Optional[str] = None,
                          assignee: Optional[str] = None,
                          creator: Optional[str] = None,
                          mentioned: Optional[str] = None,
                          sort: str = "created",
                          direction: str = "desc") -> List[Issue]:
        """
        List issues based on filters

        Args:
            repo: Repository in owner/repo format (optional)
            state: Issue state (open, closed, all)
            labels: Comma-separated list of label names
            assignee: Username of assignee
            creator: Username of creator
            mentioned: Username mentioned in issue
            sort: Sort field (created, updated, comments)
            direction: Sort direction (asc, desc)

        Returns:
            List of Issue objects
        """
        params = {
            "state": state,
            "sort": sort,
            "direction": direction
        }

        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee
        if creator:
            params["creator"] = creator
        if mentioned:
            params["mentioned"] = mentioned

        if repo:
            endpoint = f"repos/{repo}/issues"
        else:
            # If no repo is specified, list user's issues
            endpoint = "issues"

        try:
            response = await self.client.get(endpoint, params=params)
            return [Issue.from_json(issue) for issue in response.data]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list issues: {str(e)}")

    async def get_issue(self, repo: str, number: int) -> Issue:
        """Get a specific issue by number"""
        endpoint = f"repos/{repo}/issues/{number}"

        try:
            response = await self.client.get(endpoint)
            return Issue.from_json(response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Issue #{number} not found in {repo}")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get issue: {str(e)}")

    async def create_issue(self, repo: str,
                           title: str,
                           body: Optional[str] = None,
                           assignees: Optional[List[str]] = None,
                           labels: Optional[List[str]] = None,
                           milestone: Optional[int] = None) -> Issue:
        """Create a new issue"""
        endpoint = f"repos/{repo}/issues"

        data: Dict[str, Any] = {"title": title}

        if body:
            data["body"] = body
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels
        if milestone:
            data["milestone"] = milestone

        try:
            response = await self.client.post(endpoint, data=data)
            return Issue.from_json(response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create issue: {str(e)}")

    async def update_issue(self, repo: str, number: int, **kwargs: Any) -> Issue:
        """Update an issue"""
        endpoint = f"repos/{repo}/issues/{number}"

        try:
            response = await self.client.patch(endpoint, data=kwargs)
            return Issue.from_json(response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to update issue: {str(e)}")

    async def add_comment(self, repo: str, number: int, body: str) -> Dict[str, Any]:
        """Add a comment to an issue"""
        endpoint = f"repos/{repo}/issues/{number}/comments"

        try:
            response = await self.client.post(endpoint, data={"body": body})
            return cast(Dict[str, Any], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to add comment: {str(e)}")

    async def list_comments(self, repo: str, number: int) -> List[Dict[str, Any]]:
        """List comments for an issue"""
        endpoint = f"repos/{repo}/issues/{number}/comments"

        try:
            response = await self.client.get(endpoint)
            return cast(List[Dict[str, Any]], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list comments: {str(e)}")


# Handler function for CLI commands
async def handle_issue_command(args: Dict[str, Any], client: GitHubClient, ui: TerminalUI) -> None:
    """Handle issue commands from the CLI"""
    issues_api = IssuesAPI(client, ui)

    action = args.get("action")

    if action == "list":
        repo = args.get("repo")
        state = args.get("state", "open")
        labels = args.get("labels")
        assignee = args.get("assignee")
        creator = args.get("creator")
        mentioned = args.get("mentioned")
        sort = args.get("sort", "created")
        direction = args.get("direction", "desc")

        try:
            if repo:
                ui.display_info(f"Fetching {state} issues for {repo}...")
            else:
                ui.display_info(f"Fetching your {state} issues...")

            issues = await issues_api.list_issues(
                repo=repo,
                state=state,
                labels=labels,
                assignee=assignee,
                creator=creator,
                mentioned=mentioned,
                sort=sort,
                direction=direction
            )

            ui.display_issues(issues)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "view":
        repo = args.get("repo")
        number = args.get("number")

        if not repo or not number:
            ui.display_error("Repository name and issue number required")
            return

        try:
            number = int(number)
        except ValueError:
            ui.display_error("Issue number must be a valid integer")
            return

        try:
            ui.display_info(f"Fetching issue #{number} from {repo}...")

            issue = await issues_api.get_issue(repo, number)
            _display_issue_details(issue, ui)

            # Get comments
            comments = await issues_api.list_comments(repo, number)

            if comments:
                ui.display_heading("Comments")
                _display_issue_comments(comments, ui)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "create":
        repo = args.get("repo")
        if not repo:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        title = args.get("title")
        if not title:
            title = ui.prompt("Enter issue title:")

        body = args.get("body")
        if not body:
            ui.display_info(
                "Enter issue description (submit empty line to finish):")
            lines = []
            while True:
                line = input("> ")
                if not line:
                    break
                lines.append(line)
            body = "\n".join(lines) if lines else None

        assignees = args.get("assignees")
        if assignees:
            assignees = assignees.split(",")

        labels = args.get("labels")
        if labels:
            labels = labels.split(",")

        milestone = args.get("milestone")
        if milestone:
            try:
                milestone = int(milestone)
            except ValueError:
                ui.display_error("Milestone must be a valid integer")
                return

        try:
            ui.display_info(f"Creating issue in {repo}...")

            issue = await issues_api.create_issue(
                repo=repo,
                title=title,
                body=body,
                assignees=assignees,
                labels=labels,
                milestone=milestone
            )

            ui.display_success(
                f"Issue #{issue.number} created: {issue.html_url}")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "close" or action == "reopen":
        repo = args.get("repo")
        number = args.get("number")

        if not repo or not number:
            ui.display_error("Repository name and issue number required")
            return

        try:
            number = int(number)
        except ValueError:
            ui.display_error("Issue number must be a valid integer")
            return

        state = "closed" if action == "close" else "open"

        try:
            ui.display_info(f"{action.capitalize()}ing issue #{number}...")

            issue = await issues_api.update_issue(repo, number, state=state)
            ui.display_success(
                f"Issue #{issue.number} {action}ed: {issue.html_url}")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "comment":
        repo = args.get("repo")
        number = args.get("number")

        if not repo or not number:
            ui.display_error("Repository name and issue number required")
            return

        try:
            number = int(number)
        except ValueError:
            ui.display_error("Issue number must be a valid integer")
            return

        body = args.get("body")
        if not body:
            ui.display_info("Enter comment (submit empty line to finish):")
            lines = []
            while True:
                line = input("> ")
                if not line:
                    break
                lines.append(line)
            body = "\n".join(lines)

        if not body:
            ui.display_error("Comment body cannot be empty")
            return

        try:
            ui.display_info(f"Adding comment to issue #{number}...")

            comment = await issues_api.add_comment(repo, number, body)
            ui.display_success(f"Comment added: {comment.get('html_url')}")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    else:
        ui.display_error(f"Unknown issue action: {action}")
        ui.display_info(
            "Available actions: list, view, create, close, reopen, comment")


def _display_issue_details(issue: Issue, ui: TerminalUI) -> None:
    """Display detailed information about an issue"""
    ui.display_heading(f"Issue #{issue.number}: {issue.title}")

    # Create a table for issue details
    table = Table(box=box.SIMPLE)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    # Format state with appropriate color
    state_style = "green" if issue.state == "open" else "red"

    table.add_row("State", f"[{state_style}]{issue.state}[/{state_style}]")
    table.add_row("Author", issue.creator_name)
    table.add_row("Created", issue.created_date.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Updated", issue.updated_date.strftime("%Y-%m-%d %H:%M:%S"))

    if issue.assignee:
        table.add_row("Assignee", issue.assignee.get("login", "Unknown"))

    if issue.labels:
        label_names = [label.get("name", "") for label in issue.labels]
        table.add_row("Labels", ", ".join(label_names))

    if issue.milestone:
        table.add_row("Milestone", issue.milestone.get("title", "Unknown"))

    table.add_row("Comments", str(issue.comments))
    table.add_row("URL", issue.html_url)

    ui.console.print(table)

    # Display issue body as markdown if available
    if issue.body:
        ui.display_heading("Description")
        md = Markdown(issue.body)
        ui.console.print(Panel(md, border_style="blue"))


def _display_issue_comments(comments: List[Dict[str, Any]], ui: TerminalUI) -> None:
    """Display comments for an issue"""
    for i, comment in enumerate(comments):
        user = comment.get("user", {}).get("login", "Unknown")
        created_at = datetime.fromisoformat(
            comment.get("created_at", "").replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M:%S")

        # Display comment with header showing author and timestamp
        header = f"{user} commented on {created_at}"

        # Format body as markdown
        body = comment.get("body", "")
        if body:
            md = Markdown(body)
            ui.console.print(Panel(md, title=header, border_style="blue"))
        else:
            ui.console.print(
                Panel("No content", title=header, border_style="blue"))

        # Add spacing between comments
        if i < len(comments) - 1:
            ui.console.print("")
