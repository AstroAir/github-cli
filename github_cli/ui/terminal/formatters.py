"""
UI formatting utilities for terminal components.
"""

from typing import Dict, Any


class UIFormatters:
    """Formatting utilities for UI components."""
    
    # Color configuration
    COLORS = {
        "info": "blue",
        "success": "green", 
        "warning": "yellow",
        "error": "red",
        "heading": "cyan"
    }
    
    @classmethod
    def format_info_message(cls, message: str) -> str:
        """Format an informational message."""
        return f"[{cls.COLORS['info']}]ℹ[/{cls.COLORS['info']}] {message}"
    
    @classmethod
    def format_success_message(cls, message: str) -> str:
        """Format a success message."""
        return f"[{cls.COLORS['success']}]✓[/{cls.COLORS['success']}] {message}"
    
    @classmethod
    def format_warning_message(cls, message: str) -> str:
        """Format a warning message."""
        return f"[{cls.COLORS['warning']}]![/{cls.COLORS['warning']}] {message}"
    
    @classmethod
    def format_error_message(cls, message: str) -> str:
        """Format an error message."""
        return f"[{cls.COLORS['error']}]✗[/{cls.COLORS['error']}] {message}"
    
    @classmethod
    def format_heading(cls, heading: str) -> str:
        """Format a heading."""
        return f"\n[{cls.COLORS['heading']}]{heading}[/{cls.COLORS['heading']}]"
    
    @classmethod
    def format_prompt(cls, message: str) -> str:
        """Format a prompt message."""
        return f"[bold blue]{message}[/bold blue] "
    
    @classmethod
    def format_interactive_prompt(cls) -> str:
        """Format the interactive mode prompt."""
        return "[bold blue]github-cli>[/bold blue] "
    
    @staticmethod
    def format_state_with_color(state: str, state_type: str = "generic") -> str:
        """Format a state string with appropriate color."""
        color_map = {
            "open": "green",
            "closed": "red", 
            "merged": "purple",
            "draft": "yellow",
            "pending": "yellow",
            "success": "green",
            "failure": "red",
            "error": "red"
        }
        
        state_lower = state.lower()
        color = color_map.get(state_lower, "white")
        return f"[{color}]{state}[/{color}]"
    
    @staticmethod
    def format_date_string(date_str: str, format_type: str = "short") -> str:
        """Format a date string for display."""
        # This could include more sophisticated date formatting
        # For now, just return the input
        return date_str
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text to a maximum length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def format_count(count: int, label: str) -> str:
        """Format a count with its label."""
        plural = "s" if count != 1 else ""
        return f"{count} {label}{plural}"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @staticmethod
    def format_percentage(value: int, total: int) -> str:
        """Format a percentage value."""
        if total == 0:
            return "0%"
        percentage = (value / total) * 100
        return f"{percentage:.1f}%"
