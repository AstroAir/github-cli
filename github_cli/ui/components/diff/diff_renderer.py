"""
Diff rendering utilities for GitHub CLI UI.
"""

from typing import Optional, Any
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text


class DiffRenderer:
    """Renderer for git diff content."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render_file_diff(self, file_path: str, diff_content: str) -> Panel:
        """Render diff for a single file."""
        # Create a panel with the file name
        title = Text(file_path, style="bold cyan")

        # Apply syntax highlighting
        syntax = Syntax(
            diff_content,
            "diff",
            theme="monokai",
            line_numbers=True
        )

        return Panel(syntax, title=title, border_style="cyan")

    def render_file_side_by_side(self, file_path: str, before_lines: list[str],
                                 after_lines: list[str], width: int = 160) -> Columns:
        """Render side-by-side diff for a single file."""
        # Determine column width
        col_width = max(30, (width // 2) - 5)

        # Create columns
        before_panel = Panel(
            "\n".join(before_lines),
            title="Before",
            width=col_width,
            border_style="red"
        )

        after_panel = Panel(
            "\n".join(after_lines),
            title="After",
            width=col_width,
            border_style="green"
        )

        return Columns([before_panel, after_panel])

    def render_diff_header(self, file_path: str, operation: str = "modified") -> Text:
        """Render a header for a diff section."""
        header = Text()

        # Add operation indicator
        if operation == "added":
            header.append("+ ", style="green")
        elif operation == "deleted":
            header.append("- ", style="red")
        elif operation == "renamed":
            header.append("→ ", style="yellow")
        else:
            header.append("~ ", style="blue")

        header.append(file_path, style="bold cyan")

        return header

    def render_diff_stats(self, stats: dict) -> Panel:
        """Render diff statistics."""
        content = Text()

        files_changed = stats.get("files_changed", 0)
        additions = stats.get("additions", 0)
        deletions = stats.get("deletions", 0)

        content.append(f"Files changed: ", style="bold")
        content.append(f"{files_changed}\n", style="white")

        content.append(f"Additions: ", style="bold")
        content.append(f"{additions}\n", style="green")

        content.append(f"Deletions: ", style="bold")
        content.append(f"{deletions}\n", style="red")

        total_changes = additions + deletions
        content.append(f"Total changes: ", style="bold")
        content.append(f"{total_changes}", style="yellow")

        return Panel(content, title="Diff Statistics", border_style="blue")

    def render_empty_diff(self) -> Panel:
        """Render a message for empty or no diff."""
        content = Text("No changes to display", style="dim")
        return Panel(content, title="Diff", border_style="dim")

    def print_diff(self, panel_or_content: Any) -> None:
        """Print diff content to console."""
        self.console.print(panel_or_content)
        self.console.print("")  # Add spacing
