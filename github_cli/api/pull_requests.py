"""
GitHub Pull Requests API module
"""

import os
import asyncio
import subprocess
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError
from github_cli.models.pull_request import PullRequest
from github_cli.ui.diff_viewer import DiffViewer
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich import box


class PullRequestAPI:
    """API for working with GitHub pull requests"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui
        self.diff_viewer = DiffViewer(ui.console if ui else None)

    async def list_pull_requests(self, repo: str,
                                 state: str = "open",
                                 sort: str = "created",
                                 direction: str = "desc") -> List[PullRequest]:
        """List pull requests for a repository"""
        endpoint = f"repos/{repo}/pulls"
        params = {
            "state": state,
            "sort": sort,
            "direction": direction
        }

        response = await self.client.get(endpoint, params=params)
        return [PullRequest.from_json(pr_data) for pr_data in response.data]

    async def get_pull_request(self, repo: str, number: int) -> PullRequest:
        """Get a pull request by number"""
        endpoint = f"repos/{repo}/pulls/{number}"

        try:
            response = await self.client.get(endpoint)
            return PullRequest.from_json(response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Pull request #{number} not found in {repo}")

    async def create_pull_request(self, repo: str,
                                  title: str,
                                  head: str,
                                  base: str,
                                  body: Optional[str] = None,
                                  draft: bool = False) -> PullRequest:
        """Create a new pull request"""
        endpoint = f"repos/{repo}/pulls"

        data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft
        }

        if body:
            data["body"] = body

        try:
            response = await self.client.post(endpoint, data=data)
            return PullRequest.from_json(response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create pull request: {str(e)}")

    async def update_pull_request(self, repo: str, number: int, **kwargs: Any) -> PullRequest:
        """Update a pull request"""
        endpoint = f"repos/{repo}/pulls/{number}"

        try:
            response = await self.client.patch(endpoint, data=kwargs)
            return PullRequest.from_json(response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to update pull request: {str(e)}")

    async def get_pull_request_files(self, repo: str, number: int) -> List[Dict[str, Any]]:
        """Get files changed in a pull request"""
        endpoint = f"repos/{repo}/pulls/{number}/files"

        try:
            response = await self.client.get(endpoint)
            return response.data  # type: ignore[no-any-return]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get pull request files: {str(e)}")

    async def get_pull_request_commits(self, repo: str, number: int) -> List[Dict[str, Any]]:
        """Get commits in a pull request"""
        endpoint = f"repos/{repo}/pulls/{number}/commits"

        try:
            response = await self.client.get(endpoint)
            return response.data  # type: ignore[no-any-return]
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to get pull request commits: {str(e)}")

    async def get_pull_request_reviews(self, repo: str, number: int) -> List[Dict[str, Any]]:
        """Get reviews for a pull request"""
        endpoint = f"repos/{repo}/pulls/{number}/reviews"

        try:
            response = await self.client.get(endpoint)
            return response.data  # type: ignore[no-any-return]
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to get pull request reviews: {str(e)}")

    async def create_review(self, repo: str, number: int,
                            event: str = "COMMENT",
                            body: Optional[str] = None,
                            comments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a review on a pull request"""
        endpoint = f"repos/{repo}/pulls/{number}/reviews"

        valid_events = ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
        if event not in valid_events:
            raise GitHubCLIError(
                f"Invalid review event: {event}. Must be one of {valid_events}")

        data: Dict[str, Any] = {"event": event}

        if body:
            data["body"] = body

        if comments:
            data["comments"] = comments

        try:
            response = await self.client.post(endpoint, data=data)
            return response.data  # type: ignore[no-any-return]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create review: {str(e)}")

    async def merge_pull_request(self, repo: str, number: int,
                                 commit_title: Optional[str] = None,
                                 commit_message: Optional[str] = None,
                                 merge_method: str = "merge") -> Dict[str, Any]:
        """Merge a pull request"""
        endpoint = f"repos/{repo}/pulls/{number}/merge"

        valid_methods = ["merge", "squash", "rebase"]
        if merge_method not in valid_methods:
            raise GitHubCLIError(
                f"Invalid merge method: {merge_method}. Must be one of {valid_methods}")

        data = {"merge_method": merge_method}

        if commit_title:
            data["commit_title"] = commit_title

        if commit_message:
            data["commit_message"] = commit_message

        try:
            response = await self.client.put(endpoint, data=data)
            return response.data  # type: ignore[no-any-return]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to merge pull request: {str(e)}")


# Handler function for CLI commands
async def handle_pr_command(args: Dict[str, Any], client: GitHubClient, ui: TerminalUI) -> None:
    """Handle pull request commands from the CLI"""
    pr_api = PullRequestAPI(client, ui)

    action = args.get("action")

    if action == "list":
        repo = args.get("repo")
        if not repo:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        state = args.get("state", "open")
        sort = args.get("sort", "created")
        direction = args.get("direction", "desc")

        ui.display_info(f"Fetching {state} pull requests for {repo}...")
        try:
            prs = await pr_api.list_pull_requests(repo, state, sort, direction)
            ui.display_pull_requests(prs)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "view":
        repo = args.get("repo")
        number = args.get("number")

        if not repo or not number:
            ui.display_error("Repository name and PR number required")
            return

        try:
            number = int(number)
        except ValueError:
            ui.display_error("PR number must be a valid integer")
            return

        ui.display_info(f"Fetching PR #{number} from {repo}...")

        try:
            pr = await pr_api.get_pull_request(repo, number)
            _display_pr_details(pr, ui)

            # Fetch additional data
            files = await pr_api.get_pull_request_files(repo, number)
            commits = await pr_api.get_pull_request_commits(repo, number)
            reviews = await pr_api.get_pull_request_reviews(repo, number)

            # Show summaries
            ui.display_heading("Changed Files")
            _display_changed_files(files, ui)

            ui.display_heading("Commits")
            _display_commits(commits, ui)

            ui.display_heading("Reviews")
            _display_reviews(reviews, ui)

            # Ask if user wants to see diff
            if ui.confirm("View diff", default=False):
                await _show_pr_diff(repo, number, pr_api, ui)

        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "create":
        repo = args.get("repo")
        if not repo:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        title = args.get("title")
        if not title:
            title = ui.prompt("Enter pull request title:")

        head = args.get("head")
        if not head:
            head = ui.prompt("Enter head branch:")

        base = args.get("base")
        if not base:
            base = ui.prompt("Enter base branch:", default="main")

        body = args.get("body")
        if not body:
            ui.display_info(
                "Enter PR description (submit empty line to finish):")
            lines = []
            while True:
                line = input("> ")
                if not line:
                    break
                lines.append(line)
            body = "\n".join(lines) if lines else None

        draft = args.get("draft", False)

        try:
            ui.display_info(f"Creating pull request: {title}")
            pr = await pr_api.create_pull_request(repo, title, head, base, body, draft)
            ui.display_success(
                f"Pull request #{pr.number} created: {pr.html_url}")
        except GitHubCLIError as e:
            ui.display_error(f"Failed to create pull request: {str(e)}")

    elif action == "merge":
        repo = args.get("repo")
        number = args.get("number")

        if not repo or not number:
            ui.display_error("Repository name and PR number required")
            return

        try:
            number = int(number)
        except ValueError:
            ui.display_error("PR number must be a valid integer")
            return

        method = args.get("method", "merge")

        # Confirm merge
        confirmed = ui.confirm(
            f"Are you sure you want to {method} PR #{number}", default=False)
        if not confirmed:
            ui.display_info("Merge cancelled")
            return

        try:
            ui.display_info(f"Merging pull request #{number}...")
            result = await pr_api.merge_pull_request(repo, number, merge_method=method)
            ui.display_success(
                f"Pull request merged: {result.get('message', 'Success')}")
            ui.display_info(f"Commit SHA: {result.get('sha')}")
        except GitHubCLIError as e:
            ui.display_error(f"Failed to merge pull request: {str(e)}")

    else:
        ui.display_error(f"Unknown pull request action: {action}")
        ui.display_info("Available actions: list, view, create, merge")


def _display_pr_details(pr: PullRequest, ui: TerminalUI) -> None:
    """Display detailed information about a pull request"""
    ui.display_heading(f"Pull Request #{pr.number}: {pr.title}")

    # Create a table for PR details
    table = Table(box=box.SIMPLE)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    # Add PR state with appropriate styling
    state_style = "green"
    if pr.state == "closed":
        state_style = "red" if not pr.merged else "purple"
    state_value = f"[{state_style}]{pr.state}[/{state_style}]"
    if pr.merged:
        state_value += " (merged)"
    if pr.draft:
        state_value += " (draft)"

    table.add_row("State", state_value)
    table.add_row("Author", pr.creator_name)
    table.add_row("Created", pr.created_date.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Updated", pr.updated_date.strftime("%Y-%m-%d %H:%M:%S"))

    if pr.merged and pr.merged_date:
        table.add_row("Merged", pr.merged_date.strftime("%Y-%m-%d %H:%M:%S"))
        if pr.merged_by:
            table.add_row("Merged by", pr.merged_by.get("login", "Unknown"))

    table.add_row("Branch", f"{pr.head_ref} �{pr.base_ref}")

    if pr.assignee:
        table.add_row("Assignee", pr.assignee.get("login", "Unknown"))

    if pr.labels:
        label_names = [label.get("name", "") for label in pr.labels]
        table.add_row("Labels", ", ".join(label_names))

    table.add_row("URL", pr.html_url)

    ui.console.print(table)

    # Display PR body as markdown if available
    if pr.body:
        ui.display_heading("Description")
        md = Markdown(pr.body)
        ui.console.print(Panel(md, border_style="blue"))


def _display_changed_files(files: List[Dict[str, Any]], ui: TerminalUI) -> None:
    """Display files changed in a pull request"""
    if not files:
        ui.display_info("No files changed")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Changes", style="yellow", justify="right")

    for file in files:
        filename = file.get("filename", "Unknown")
        status = file.get("status", "modified")

        # Style status appropriately
        status_style = "green"
        if status == "removed":
            status_style = "red"
        elif status == "added":
            status_style = "blue"

        # Calculate changes
        additions = file.get("additions", 0)
        deletions = file.get("deletions", 0)
        changes = f"+{additions} −{deletions}"

        table.add_row(
            filename, f"[{status_style}]{status}[/{status_style}]", changes)

    ui.console.print(table)


def _display_commits(commits: List[Dict[str, Any]], ui: TerminalUI) -> None:
    """Display commits in a pull request"""
    if not commits:
        ui.display_info("No commits found")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("SHA", style="yellow")
    table.add_column("Author", style="cyan")
    table.add_column("Message")
    table.add_column("Date", style="green")

    for commit in commits:
        sha = commit.get("sha", "")[:7]  # Short SHA

        # Get author info
        author = "Unknown"
        author_info = commit.get("author") or {}
        if author_info:
            author = author_info.get("login", "Unknown")

        # Get commit info
        commit_info = commit.get("commit", {})
        message = commit_info.get("message", "").split("\n")[
            0]  # First line only

        # Get date
        date = "Unknown"
        if "committer" in commit_info:
            date_str = commit_info["committer"].get("date")
            if date_str:
                date = datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")

        table.add_row(sha, author, message, date)

    ui.console.print(table)


def _display_reviews(reviews: List[Dict[str, Any]], ui: TerminalUI) -> None:
    """Display reviews for a pull request"""
    if not reviews:
        ui.display_info("No reviews yet")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Reviewer", style="cyan")
    table.add_column("State", style="yellow")
    table.add_column("Submitted", style="green")

    for review in reviews:
        reviewer = review.get("user", {}).get("login", "Unknown")

        # Style review state appropriately
        state = review.get("state", "PENDING")
        state_style = "yellow"
        if state == "APPROVED":
            state_style = "green"
        elif state == "CHANGES_REQUESTED":
            state_style = "red"

        # Format date
        date = "Unknown"
        if "submitted_at" in review:
            date_str = review["submitted_at"]
            date = datetime.fromisoformat(
                date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")

        table.add_row(
            reviewer, f"[{state_style}]{state}[/{state_style}]", date)

    ui.console.print(table)


async def _show_pr_diff(repo: str, number: int, pr_api: PullRequestAPI, ui: TerminalUI) -> None:
    """Show diff for a pull request"""
    ui.display_info("Fetching diff...")

    # Use the diff viewer to display the diff
    endpoint = f"repos/{repo}/pulls/{number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}

    try:
        response = await pr_api.client._request("GET", endpoint, headers=headers)
        diff = response.data

        if ui.console.width > 120:
            # Wide terminal - show side by side
            pr_api.diff_viewer.display_diff_side_by_side(
                diff, ui.console.width)
        else:
            # Narrow terminal - show normal diff
            pr_api.diff_viewer.display_diff(diff)

    except GitHubCLIError as e:
        ui.display_error(f"Failed to fetch diff: {str(e)}")
