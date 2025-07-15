"""
Terminal UI for GitHub CLI
"""

from typing import List, Optional

import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box

from github_cli.api.client import GitHubClient
from github_cli.models.repository import Repository
from github_cli.models.issue import Issue
from github_cli.models.pull_request import PullRequest
from github_cli.utils.exceptions import GitHubCLIError


class TerminalUI:
    """Terminal UI for the GitHub CLI"""

    def __init__(self, client: GitHubClient):
        self.client = client
        self.console = Console()
        self.theme = "auto"

        # Define colors
        self.colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "heading": "cyan"
        }

    def display_repositories(self, repos: List[Repository]) -> None:
        """Display a list of repositories"""
        if not repos:
            self.display_info("No repositories found")
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
            updated = repo.updated_date.strftime("%Y-%m-%d")

            table.add_row(
                repo.full_name,
                repo.description or "",
                repo.language or "None",
                str(repo.stargazers_count),
                str(repo.forks_count),
                updated
            )

        self.console.print(table)

    def display_info(self, message: str) -> None:
        """Display an informational message"""
        self.console.print(
            f"[{self.colors['info']}]ℹ[/{self.colors['info']}] {message}")

    def display_success(self, message: str) -> None:
        """Display a success message"""
        self.console.print(
            f"[{self.colors['success']}]✓[/{self.colors['success']}] {message}")

    def display_warning(self, message: str) -> None:
        """Display a warning message"""
        self.console.print(
            f"[{self.colors['warning']}]![/{self.colors['warning']}] {message}")

    def display_error(self, message: str) -> None:
        """Display an error message"""
        self.console.print(
            f"[{self.colors['error']}]✗[/{self.colors['error']}] {message}")

    def display_heading(self, heading: str) -> None:
        """Display a heading"""
        self.console.print(
            f"\n[{self.colors['heading']}]{heading}[/{self.colors['heading']}]")

    def prompt(self, message: str, choices: Optional[List[str]] = None, default: Optional[str] = None) -> str:
        """Prompt the user for input"""
        # Ensure default is a string, not None, for questionary.text
        default_val = default if default is not None else ""
        if choices:
            return questionary.select(message, choices=choices, default=default_val).ask() or ""
        return questionary.text(message, default=default_val).ask() or ""

    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation"""
        return questionary.confirm(message, default=default).ask()

    def interactive_mode(self) -> None:
        """Start an interactive session"""
        self.display_heading("GitHub CLI Interactive Mode")
        self.display_info(
            "Type 'help' for available commands or 'exit' to quit")

        while True:
            command = self.prompt("> ")

            if not command:
                continue

            if command.lower() == 'exit':
                self.display_info("Exiting interactive mode")
                break

            try:
                self._process_interactive_command(command)
            except GitHubCLIError as e:
                self.display_error(f"Error: {str(e)}")
            except Exception as e:
                self.display_warning(f"Unexpected error: {str(e)}")
                self.display_error("This might be a bug. Please report it.")

    def _process_interactive_command(self, command: str) -> None:
        """Process a command in interactive mode"""
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Command handlers go here
        if cmd == "help":
            self._display_help()
        elif cmd == "repos" or cmd == "repositories":
            self._handle_repos_command(args)
        # Add more command handlers
        else:
            self.display_error(f"Unknown command: {cmd}")
            self.display_info("Type 'help' for available commands")

    def _display_help(self) -> None:
        """Display help information"""
        self.display_heading("Available Commands")

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

    def _handle_repos_command(self, args: List[str]) -> None:
        """Handle repository commands"""
        if not args or args[0] == "list":
            self.display_info("Fetching your repositories...")
            # This would be implemented to call the API client
            # Example: repos = await self.client.get_user_repositories()
            # self.display_repositories(repos)
            self.display_info("Repository listing not implemented yet")
        elif args[0] == "view" and len(args) > 1:
            self.display_info(f"Fetching repository: {args[1]}")
            # Example: repo = await self.client.get_repository(args[1])
            # self._display_repository_details(repo)
            self.display_info("Repository view not implemented yet")
        else:
            self.display_error("Invalid repository command")
            self.display_info("Usage: repos [list|view|create] [name]")

    def display_issues(self, issues: List[Issue]) -> None:
        """Display a list of issues"""
        if not issues:
            self.display_info("No issues found")
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
            created = issue.created_date.strftime("%Y-%m-%d")

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
        """Display a list of pull requests"""
        if not prs:
            self.display_info("No pull requests found")
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
            updated = pr.updated_date.strftime("%Y-%m-%d")

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
        """Display markdown content"""
        md = Markdown(markdown_text)
        if title:
            self.console.print(Panel(md, title=title, border_style="blue"))
        else:
            self.console.print(md)

    def display_code(self, code: str, language: str = "python") -> None:
        """Display code with syntax highlighting"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    async def start_interactive_mode(self, shortcuts_manager=None) -> None:
        """Start the interactive terminal mode"""
        self.console.print(
            "[bold green]Welcome to GitHub CLI Interactive Mode[/bold green]")
        self.console.print(
            "Type 'help' to see available commands or 'exit' to quit.")

        while True:
            try:
                # Display prompt
                self.console.print(
                    "[bold blue]github-cli>[/bold blue] ", end="")
                command = input().strip()

                if not command:
                    continue

                if command.lower() in ['exit', 'quit', 'q']:
                    break

                if command.lower() == 'help':
                    self._display_help()
                    continue

                # Check if command is a shortcut
                if shortcuts_manager and shortcuts_manager.has_shortcut(command):
                    command = shortcuts_manager.get_shortcut(command)

                # Process command
                await self._process_command(command)

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
            except Exception as e:
                self.display_error(f"Command error: {str(e)}")

    async def _process_command(self, command: str) -> None:
        """Process a command in interactive mode"""
        # This is a placeholder - real implementation would parse and execute commands
        parts = command.split()
        if not parts:
            return

        # Simplified command handling
        self.console.print(
            f"[yellow]Command '{command}' is not yet implemented[/yellow]")
