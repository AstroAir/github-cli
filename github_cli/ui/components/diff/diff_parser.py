"""
Diff parsing utilities for GitHub CLI UI.
"""

from typing import Dict, List, Tuple


class DiffParser:
    """Parser for git diff content."""
    
    @staticmethod
    def split_diff_hunks(diff_content: str) -> Dict[str, str]:
        """Split diff content into file hunks."""
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
    
    @staticmethod
    def parse_diff_for_side_by_side(diff_content: str) -> Tuple[List[str], List[str]]:
        """Parse diff content into before and after columns for side-by-side view."""
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
    
    @staticmethod
    def extract_file_info(diff_line: str) -> Dict[str, str]:
        """Extract file information from a diff header line."""
        info = {
            "old_file": "",
            "new_file": "",
            "operation": "modified"
        }
        
        if diff_line.startswith('diff --git'):
            parts = diff_line.split(' ')
            if len(parts) >= 4:
                # Extract file paths
                old_path = parts[2][2:]  # Remove 'a/' prefix
                new_path = parts[3][2:]  # Remove 'b/' prefix
                
                info["old_file"] = old_path
                info["new_file"] = new_path
                
                # Determine operation type
                if old_path == new_path:
                    info["operation"] = "modified"
                elif old_path == "/dev/null":
                    info["operation"] = "added"
                elif new_path == "/dev/null":
                    info["operation"] = "deleted"
                else:
                    info["operation"] = "renamed"
        
        return info
    
    @staticmethod
    def get_diff_stats(diff_content: str) -> Dict[str, int]:
        """Get statistics about the diff (additions, deletions, etc.)."""
        stats = {
            "additions": 0,
            "deletions": 0,
            "files_changed": 0
        }
        
        files = DiffParser.split_diff_hunks(diff_content)
        stats["files_changed"] = len(files)
        
        for file_diff in files.values():
            for line in file_diff.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    stats["additions"] += 1
                elif line.startswith('-') and not line.startswith('---'):
                    stats["deletions"] += 1
        
        return stats
