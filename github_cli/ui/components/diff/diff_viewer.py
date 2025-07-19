"""
Main diff viewer component combining parsing and rendering.
"""

from typing import Optional
from rich.console import Console

from .diff_parser import DiffParser
from .diff_renderer import DiffRenderer


class DiffViewer:
    """Main component for viewing GitHub diff content."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.parser = DiffParser()
        self.renderer = DiffRenderer(self.console)
    
    def display_diff(self, diff_content: str) -> None:
        """Display a git diff with syntax highlighting."""
        if not diff_content or not diff_content.strip():
            self.renderer.print_diff(self.renderer.render_empty_diff())
            return
        
        # Split diff into hunks
        hunks = self.parser.split_diff_hunks(diff_content)
        
        # Show diff statistics first
        stats = self.parser.get_diff_stats(diff_content)
        self.renderer.print_diff(self.renderer.render_diff_stats(stats))
        
        # Display each file diff
        for file_path, file_diff in hunks.items():
            file_info = self.parser.extract_file_info(file_diff.split('\n')[0])
            
            # Show file header
            header = self.renderer.render_diff_header(file_path, file_info["operation"])
            self.console.print(header)
            
            # Show file diff
            panel = self.renderer.render_file_diff(file_path, file_diff)
            self.renderer.print_diff(panel)
    
    def display_diff_side_by_side(self, diff_content: str, width: int = 160) -> None:
        """Display a side-by-side diff view for wider terminals."""
        if not diff_content or not diff_content.strip():
            self.renderer.print_diff(self.renderer.render_empty_diff())
            return
        
        hunks = self.parser.split_diff_hunks(diff_content)
        
        # Show diff statistics first
        stats = self.parser.get_diff_stats(diff_content)
        self.renderer.print_diff(self.renderer.render_diff_stats(stats))
        
        for file_path, file_diff in hunks.items():
            # Parse the diff into before/after
            before_lines, after_lines = self.parser.parse_diff_for_side_by_side(file_diff)
            
            # Show file header
            file_info = self.parser.extract_file_info(file_diff.split('\n')[0])
            header = self.renderer.render_diff_header(file_path, file_info["operation"])
            self.console.print(header)
            
            # Show side-by-side diff
            columns = self.renderer.render_file_side_by_side(
                file_path, before_lines, after_lines, width
            )
            self.renderer.print_diff(columns)
    
    def get_diff_summary(self, diff_content: str) -> dict:
        """Get a summary of the diff without displaying it."""
        if not diff_content or not diff_content.strip():
            return {"files": [], "stats": {"files_changed": 0, "additions": 0, "deletions": 0}}
        
        hunks = self.parser.split_diff_hunks(diff_content)
        stats = self.parser.get_diff_stats(diff_content)
        
        files = []
        for file_path, file_diff in hunks.items():
            file_info = self.parser.extract_file_info(file_diff.split('\n')[0])
            files.append({
                "path": file_path,
                "operation": file_info["operation"],
                "old_file": file_info["old_file"],
                "new_file": file_info["new_file"]
            })
        
        return {
            "files": files,
            "stats": stats
        }
