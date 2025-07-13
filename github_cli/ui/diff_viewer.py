"""
GitHub diff viewer UI
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text


class DiffViewer:
    """Viewer for GitHub diff content"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def display_diff(self, diff_content: str) -> None:
        """Display a git diff with syntax highlighting"""
        # Split diff into hunks
        hunks = self._split_diff_hunks(diff_content)

        for file_path, file_diff in hunks.items():
            self._display_file_diff(file_path, file_diff)

    def _split_diff_hunks(self, diff_content: str) -> Dict[str, str]:
        """Split diff content into file hunks"""
        result = {}
        current_file = None
        current_content = []

        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                # New file diff starts
                if current_file:
                    result[current_file] = '\n'.join(current_content)

                # Get the new file name
                parts = line.split(' b/')
                if len(parts) > 1:
                    current_file = parts[1]
                else:
                    current_file = f"File {len(result) + 1}"

                current_content = [line]
            elif current_file:
                current_content.append(line)

        # Add the last file
        if current_file:
            result[current_file] = '\n'.join(current_content)

        return result

    def _display_file_diff(self, file_path: str, diff_content: str) -> None:
        """Display diff for a single file"""
        # Create a panel with the file name
        title = Text(file_path, style="bold cyan")

        # Apply syntax highlighting
        syntax = Syntax(diff_content, "diff",
                        theme="monokai", line_numbers=True)

        panel = Panel(syntax, title=title, border_style="cyan")
        self.console.print(panel)
        self.console.print("")

    def display_diff_side_by_side(self, diff_content: str, width: int = 160) -> None:
        """Display a side-by-side diff view (for wider terminals)"""
        hunks = self._split_diff_hunks(diff_content)

        for file_path, file_diff in hunks.items():
            self._display_file_side_by_side(file_path, file_diff, width)

    def _display_file_side_by_side(self, file_path: str, diff_content: str, width: int) -> None:
        """Display side-by-side diff for a single file"""
        title = Text(file_path, style="bold cyan")
        self.console.print(title)

        # Parse the diff into before/after
        before_lines, after_lines = self._parse_diff_for_side_by_side(
            diff_content)

        # Determine column width
        col_width = max(30, (width // 2) - 5)

        # Create columns
        columns = Columns([
            Panel("\n".join(before_lines), title="Before",
                  width=col_width, border_style="red"),
            Panel("\n".join(after_lines), title="After",
                  width=col_width, border_style="green")
        ])

        self.console.print(columns)
        self.console.print("")

    def _parse_diff_for_side_by_side(self, diff_content: str) -> tuple[List[str], List[str]]:
        """Parse diff content into before and after columns"""
        before_lines = []
        after_lines = []

        # Skip header lines
        content_lines = diff_content.split('\n')
        start_index = 0
        for i, line in enumerate(content_lines):
            if line.startswith('@@'):
                start_index = i + 1
                break

        for line in content_lines[start_index:]:
            if not line:
                before_lines.append("")
                after_lines.append("")
            elif line.startswith('+'):
                before_lines.append("")
                after_lines.append(line[1:])
            elif line.startswith('-'):
                before_lines.append(line[1:])
                after_lines.append("")
            elif line.startswith(' '):
                before_lines.append(line[1:])
                after_lines.append(line[1:])

        return before_lines, after_lines
