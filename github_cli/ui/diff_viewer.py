"""
GitHub diff viewer UI - Refactored for better organization.

This module provides backward compatibility while using the new modular components.
"""

from typing import Optional
from rich.console import Console

# Import the new modular components
from .components.diff import DiffViewer as ModularDiffViewer


class DiffViewer:
    """
    Backward-compatible wrapper for the modular diff viewer.
    
    This class maintains the same API as the original DiffViewer while
    delegating to the new modular implementation.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        # Use the new modular diff viewer
        self._viewer = ModularDiffViewer(self.console)

    def display_diff(self, diff_content: str) -> None:
        """Display a git diff with syntax highlighting."""
        self._viewer.display_diff(diff_content)

    def display_diff_side_by_side(self, diff_content: str, width: int = 160) -> None:
        """Display a side-by-side diff view (for wider terminals)."""
        self._viewer.display_diff_side_by_side(diff_content, width)

    # Legacy methods for backward compatibility
    def _split_diff_hunks(self, diff_content: str) -> dict:
        """Split diff content into file hunks (legacy method)."""
        return self._viewer.parser.split_diff_hunks(diff_content)

    def _display_file_diff(self, file_path: str, diff_content: str) -> None:
        """Display diff for a single file (legacy method)."""
        panel = self._viewer.renderer.render_file_diff(file_path, diff_content)
        self._viewer.renderer.print_diff(panel)

    def _display_file_side_by_side(self, file_path: str, diff_content: str, width: int) -> None:
        """Display side-by-side diff for a single file (legacy method)."""
        before_lines, after_lines = self._viewer.parser.parse_diff_for_side_by_side(diff_content)
        columns = self._viewer.renderer.render_file_side_by_side(
            file_path, before_lines, after_lines, width
        )
        self._viewer.renderer.print_diff(columns)

    def _parse_diff_for_side_by_side(self, diff_content: str) -> tuple:
        """Parse diff content into before and after columns (legacy method)."""
        return self._viewer.parser.parse_diff_for_side_by_side(diff_content)

    # New enhanced methods
    def get_diff_summary(self, diff_content: str) -> dict:
        """Get a summary of the diff without displaying it."""
        return self._viewer.get_diff_summary(diff_content)

    def get_diff_stats(self, diff_content: str) -> dict:
        """Get statistics about the diff."""
        return self._viewer.parser.get_diff_stats(diff_content)
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
