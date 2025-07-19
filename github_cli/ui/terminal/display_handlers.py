"""
Display handlers for terminal UI components.
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box

from github_cli.models.repository import Repository
from github_cli.models.issue import Issue
from github_cli.models.pull_request import PullRequest


class DisplayHandlers:
    """Handles all display operations for the terminal UI."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def display_repositories(self, repos: List[Repository]) -> None:
        """Display a list of repositories."""
        if not repos:
            self.console.print("[blue]ℹ[/blue] No repositories found")
            return

        table = Table(title="Repositories", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Language", style="magenta")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Forks", justify="right")
        table.add_column("Updated", style="blue")

        for repo in repos:
            # Format the updated date
            updated = repo.updated_date.strftime("%Y-%m-%d") if repo.updated_date else "Unknown"

            table.add_row(
                repo.full_name,
                repo.description or "",
                repo.language or "None",
                str(repo.stargazers_count),
                str(repo.forks_count),
                updated
            )

        self.console.print(table)
    
    def display_issues(self, issues: List[Issue]) -> None:
        """Display a list of issues."""
        if not issues:
            self.console.print("[blue]ℹ[/blue] No issues found")
            return

        table = Table(title="Issues", box=box.ROUNDED)
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Title", style="green")
        table.add_column("State", style="magenta")
        table.add_column("Comments", justify="right")
        table.add_column("Created by", style="blue")
        table.add_column("Created", style="blue")

        for issue in issues:
            # Format the state with color
            state_style = "green" if issue.state == "open" else "red"
            state = f"[{state_style}]{issue.state}[/{state_style}]"

            # Format the date
            created = issue.created_date.strftime("%Y-%m-%d") if issue.created_date else "Unknown"

            table.add_row(
                str(issue.number),
                issue.title,
                state,
                str(issue.comments),
                issue.creator_name,
                created
            )

        self.console.print(table)
    
    def display_pull_requests(self, prs: List[PullRequest]) -> None:
        """Display a list of pull requests."""
        if not prs:
            self.console.print("[blue]ℹ[/blue] No pull requests found")
            return

        table = Table(title="Pull Requests", box=box.ROUNDED)
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Title", style="green")
        table.add_column("State", style="magenta")
        table.add_column("Branch", style="yellow")
        table.add_column("Author", style="blue")
        table.add_column("Updated", style="blue")

        for pr in prs:
            # Format the state with color
            state_color = "green"
            if pr.state == "closed":
                state_color = "red" if not pr.merged else "purple"
            state = f"[{state_color}]{pr.state}[/{state_color}]"

            # Format the date
            updated = pr.updated_date.strftime("%Y-%m-%d") if pr.updated_date else "Unknown"

            table.add_row(
                str(pr.number),
                pr.title,
                state,
                f"{pr.head_ref} → {pr.base_ref}",
                pr.creator_name,
                updated
            )

        self.console.print(table)
    
    def display_markdown(self, markdown_text: str, title: Optional[str] = None) -> None:
        """Display markdown content."""
        md = Markdown(markdown_text)
        if title:
            self.console.print(Panel(md, title=title, border_style="blue"))
        else:
            self.console.print(md)
    
    def display_code(self, code: str, language: str = "python") -> None:
        """Display code with syntax highlighting."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def display_git_branches(self, branches: List[str]) -> None:
        """Display git branches."""
        if not branches:
            self.console.print("[blue]ℹ[/blue] No branches found")
            return

        table = Table(title="Git Branches", box=box.ROUNDED)
        table.add_column("Branch", style="cyan")

        for branch in branches:
            table.add_row(branch)

        self.console.print(table)
    
    def display_git_status(self, status: Dict[str, Any]) -> None:
        """Display git repository status."""
        repo = status.get("repository", "Unknown")
        branch = status.get("branch", "Unknown")

        header = f"Repository: {repo} (Branch: {branch})"

        if status.get("clean", True):
            content = "Working tree clean"
            style = "green"
        else:
            content_lines = []

            if status.get("modified"):
                content_lines.append(f"Modified: {len(status['modified'])} files")
            if status.get("added"):
                content_lines.append(f"Added: {len(status['added'])} files")
            if status.get("deleted"):
                content_lines.append(f"Deleted: {len(status['deleted'])} files")
            if status.get("untracked"):
                content_lines.append(f"Untracked: {len(status['untracked'])} files")

            content = "\n".join(content_lines)
            style = "yellow"

        self.console.print(Panel(content, title=header, box=box.ROUNDED, style=style))
    
    def display_git_stashes(self, stashes: List[Dict[str, Any]]) -> None:
        """Display git stashes."""
        if not stashes:
            self.console.print("[blue]ℹ[/blue] No stashes found")
            return

        table = Table(title="Git Stashes", box=box.ROUNDED)
        table.add_column("Index", style="cyan")
        table.add_column("Message", style="white")
        table.add_column("Date", style="blue")

        for stash in stashes:
            table.add_row(
                stash.get("index", ""),
                stash.get("message", ""),
                stash.get("date", "")
            )

        self.console.print(table)
    
    def display_help(self) -> None:
        """Display help information."""
        help_text = """
        General:
          help            Show this help message
          exit            Exit interactive mode
          
        Repositories:
          repos list      List your repositories
          repos view      View repository details
          repos create    Create a new repository
          
        Issues:
          issues list     List issues
          issues create   Create a new issue
          issues view     View issue details
          
        Pull Requests:
          pr list         List pull requests
          pr view         View pull request details
          pr create       Create a new pull request
          
        Actions:
          actions list    List workflow runs
          actions view    View workflow details
        """

        self.console.print(Panel(help_text, title="Help", border_style="blue"))
