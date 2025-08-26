"""
Terminal UI for GitHub CLI - Refactored for better organization.

This module provides backward compatibility while using the new modular components.
"""

from typing import List, Optional, Dict, Any

from github_cli.api.client import GitHubClient

# Import the new modular terminal components
from .terminal import TerminalUI as ModularTerminalUI


class TerminalUI:
    """
    Backward-compatible wrapper for the modular terminal UI.

    This class maintains the same API as the original TerminalUI while
    delegating to the new modular implementation.
    """

    def __init__(self, client: GitHubClient):
        self.client = client

        # Use the new modular terminal UI
        self._terminal = ModularTerminalUI(client)

        # Maintain backward compatibility properties
        self.console = self._terminal.console
        self.theme = self._terminal.theme
        self.colors = self._terminal.formatter.COLORS

    # Delegate all methods to the modular implementation
    def display_repositories(self, repos: List) -> None:
        """Display a list of repositories."""
        self._terminal.display_repositories(repos)

    def display_info(self, message: str) -> None:
        """Display an informational message."""
        self._terminal.display_info(message)

    def display_success(self, message: str) -> None:
        """Display a success message."""
        self._terminal.display_success(message)

    def display_warning(self, message: str) -> None:
        """Display a warning message."""
        self._terminal.display_warning(message)

    def display_error(self, message: str) -> None:
        """Display an error message."""
        self._terminal.display_error(message)

    def display_heading(self, heading: str) -> None:
        """Display a heading."""
        self._terminal.display_heading(heading)

    def prompt(self, message: str, choices: Optional[List[str]] = None,
               default: Optional[str] = None) -> str:
        """Prompt the user for input."""
        return self._terminal.prompt(message, choices, default)

    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation."""
        return self._terminal.confirm(message, default)

    def interactive_mode(self) -> None:
        """Start an interactive session."""
        self._terminal.interactive_mode()

    def display_issues(self, issues: List) -> None:
        """Display a list of issues."""
        self._terminal.display_issues(issues)

    def display_pull_requests(self, prs: List) -> None:
        """Display a list of pull requests."""
        self._terminal.display_pull_requests(prs)

    def display_markdown(self, markdown_text: str, title: Optional[str] = None) -> None:
        """Display markdown content."""
        self._terminal.display_markdown(markdown_text, title)

    def display_code(self, code: str, language: str = "python") -> None:
        """Display code with syntax highlighting."""
        self._terminal.display_code(code, language)

    async def start_interactive_mode(self, shortcuts_manager=None) -> None:
        """Start the interactive terminal mode."""
        await self._terminal.start_interactive_mode(shortcuts_manager)

    def display_git_branches(self, branches: List[str]) -> None:
        """Display git branches."""
        self._terminal.display_git_branches(branches)

    def display_git_status(self, status: Dict[str, Any]) -> None:
        """Display git repository status."""
        self._terminal.display_git_status(status)

    def display_git_stashes(self, stashes: List[Dict[str, Any]]) -> None:
        """Display git stashes."""
        self._terminal.display_git_stashes(stashes)

    # New enhanced methods
    def set_theme(self, theme: str) -> None:
        """Set the UI theme."""
        self._terminal.set_theme(theme)
        self.theme = theme

    def get_console_width(self) -> int:
        """Get the current console width."""
        return self._terminal.get_console_width()

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        self._terminal.clear_screen()

    # Provide access to the underlying components for advanced usage
    @property
    def display_handlers(self):
        """Get the display handlers component."""
        return self._terminal.display

    @property
    def formatters(self):
        """Get the formatters component."""
        return self._terminal.formatter
