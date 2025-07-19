"""
Help screen for GitHub CLI TUI.

This module contains the help screen that displays keyboard shortcuts
and usage information for the GitHub CLI TUI application.
"""

from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Static


class HelpScreen(Screen[None]):
    """Help screen showing keybindings and usage."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", "Close Help"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Container(id="help-container"):
            yield Static("GitHub CLI - Help", id="help-title")

            help_text = """
GitHub CLI TUI - Keyboard Shortcuts

Navigation:
  Ctrl+C / Q      Quit application
  Ctrl+N          New tab
  Ctrl+W          Close tab
  Ctrl+T          Toggle sidebar
  Ctrl+R          Refresh current view
  Ctrl+S          Search
  F1              Show this help
  F5              Refresh all

Authentication:
  Ctrl+L          Login
  Ctrl+O          Logout

General:
  Tab             Navigate between widgets
  Enter           Activate/Select
  Escape          Cancel/Go back
  Arrow Keys      Navigate lists
  Page Up/Down    Scroll long lists
  Home/End        Go to first/last item

Repository View:
  Enter           View repository details
  D               Clone repository
  I               View issues
  P               View pull requests
  A               View actions

Pull Requests:
  Enter           View PR details
  M               Merge PR
  C               Close PR
  R               Review PR

Notifications:
  Enter           View notification
  M               Mark as read
  Del             Delete notification
  Ctrl+A          Mark all as read

Search:
  /               Focus search input
  Enter           Execute search
  Tab             Switch search type

For more information, visit: https://github.com/github/gh
            """

            yield Static(help_text.strip(), id="help-content")
            yield Button("Close", id="close-help", variant="primary")

    @on(Button.Pressed, "#close-help")
    def close_help(self) -> None:
        """Close help screen."""
        self.dismiss()
