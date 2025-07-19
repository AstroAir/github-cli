"""
Reusable footer components for GitHub CLI UI.
"""

from datetime import datetime
from typing import Optional
from rich.panel import Panel
from rich.text import Text


class FooterFactory:
    """Factory for creating footer components."""
    
    @staticmethod
    def create_main_footer(last_updated: Optional[datetime] = None) -> Panel:
        """Create the main application footer."""
        footer_text = Text()
        footer_text.append("Press Ctrl+C to exit", style="cyan")
        
        if last_updated:
            footer_text.append(" | ")
            update_str = last_updated.strftime("%Y-%m-%d %H:%M:%S")
            footer_text.append(f"Last updated: {update_str}", style="green")
        
        return Panel(footer_text, style="white on blue")
    
    @staticmethod
    def create_dashboard_footer() -> Panel:
        """Create a dashboard-specific footer."""
        current_time = datetime.now()
        return FooterFactory.create_main_footer(current_time)
    
    @staticmethod
    def create_help_footer(help_text: str) -> Panel:
        """Create a footer with help information."""
        footer_text = Text(help_text, style="dim cyan")
        return Panel(footer_text, style="dim")
