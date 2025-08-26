"""
Refactored Terminal UI with improved organization.
"""

from typing import List, Optional, Dict, Any
import questionary
from rich.console import Console

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
from .display_handlers import DisplayHandlers
from .formatters import UIFormatters


class TerminalUI:
    """Terminal UI for the GitHub CLI with modular components."""

    def __init__(self, client: GitHubClient):
        self.client = client
        self.console = Console()
        self.theme = "auto"

        # Initialize components
        self.display = DisplayHandlers(self.console)
        self.formatter = UIFormatters()

    # Message display methods using formatters
    def display_info(self, message: str) -> None:
        """Display an informational message."""
        formatted = self.formatter.format_info_message(message)
        self.console.print(formatted)

    def display_success(self, message: str) -> None:
        """Display a success message."""
        formatted = self.formatter.format_success_message(message)
        self.console.print(formatted)

    def display_warning(self, message: str) -> None:
        """Display a warning message."""
        formatted = self.formatter.format_warning_message(message)
        self.console.print(formatted)

    def display_error(self, message: str) -> None:
        """Display an error message."""
        formatted = self.formatter.format_error_message(message)
        self.console.print(formatted)

    def display_heading(self, heading: str) -> None:
        """Display a heading."""
        formatted = self.formatter.format_heading(heading)
        self.console.print(formatted)

    # Input and interaction methods
    def prompt(self, message: str, choices: Optional[List[str]] = None,
               default: Optional[str] = None) -> str:
        """Prompt the user for input."""
        default_val = default if default is not None else ""
        if choices:
            return questionary.select(message, choices=choices, default=default_val).ask() or ""
        return questionary.text(message, default=default_val).ask() or ""

    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation."""
        result = questionary.confirm(message, default=default).ask()
        return bool(result) if result is not None else default

    # Delegate display methods to display handlers
    def display_repositories(self, repos: List) -> None:
        """Display a list of repositories."""
        self.display.display_repositories(repos)

    def display_issues(self, issues: List) -> None:
        """Display a list of issues."""
        self.display.display_issues(issues)

    def display_pull_requests(self, prs: List) -> None:
        """Display a list of pull requests."""
        self.display.display_pull_requests(prs)

    def display_markdown(self, markdown_text: str, title: Optional[str] = None) -> None:
        """Display markdown content."""
        self.display.display_markdown(markdown_text, title)

    def display_code(self, code: str, language: str = "python") -> None:
        """Display code with syntax highlighting."""
        self.display.display_code(code, language)

    def display_git_branches(self, branches: List[str]) -> None:
        """Display git branches."""
        self.display.display_git_branches(branches)

    def display_git_status(self, status: Dict[str, Any]) -> None:
        """Display git repository status."""
        self.display.display_git_status(status)

    def display_git_stashes(self, stashes: List[Dict[str, Any]]) -> None:
        """Display git stashes."""
        self.display.display_git_stashes(stashes)

    # Interactive mode methods
    def interactive_mode(self) -> None:
        """Start an interactive session."""
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

    async def start_interactive_mode(self, shortcuts_manager: Any = None) -> None:
        """Start the interactive terminal mode."""
        self.console.print(
            "[bold green]Welcome to GitHub CLI Interactive Mode[/bold green]")
        self.console.print(
            "Type 'help' to see available commands or 'exit' to quit.")

        while True:
            try:
                # Display prompt
                prompt = self.formatter.format_interactive_prompt()
                self.console.print(prompt, end="")
                command = input().strip()

                if not command:
                    continue

                if command.lower() in ['exit', 'quit', 'q']:
                    break

                if command.lower() == 'help':
                    self.display.display_help()
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

    def _process_interactive_command(self, command: str) -> None:
        """Process a command in interactive mode."""
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Command handlers
        if cmd == "help":
            self.display.display_help()
        elif cmd == "repos" or cmd == "repositories":
            self._handle_repos_command(args)
        else:
            self.display_error(f"Unknown command: {cmd}")
            self.display_info("Type 'help' for available commands")

    def _handle_repos_command(self, args: List[str]) -> None:
        """Handle repository commands."""
        if not args or args[0] == "list":
            self.display_info("Fetching your repositories...")
            self.display_info("Repository listing not implemented yet")
        elif args[0] == "view" and len(args) > 1:
            self.display_info(f"Fetching repository: {args[1]}")
            self.display_info("Repository view not implemented yet")
        else:
            self.display_error("Invalid repository command")
            self.display_info("Usage: repos [list|view|create] [name]")

    async def _process_command(self, command: str) -> None:
        """Process a command in interactive mode."""
        # This is a placeholder - real implementation would parse and execute commands
        parts = command.split()
        if not parts:
            return

        # Simplified command handling
        self.console.print(
            f"[yellow]Command '{command}' is not yet implemented[/yellow]")

    # Utility methods
    def set_theme(self, theme: str) -> None:
        """Set the UI theme."""
        self.theme = theme

    def get_console_width(self) -> int:
        """Get the current console width."""
        return self.console.size.width

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        self.console.clear()
