"""
Reusable panel components for GitHub CLI UI.
"""

from typing import Optional, Any
from rich.panel import Panel
from rich.text import Text
from rich.console import Console


class BasePanelFactory:
    """Base factory for creating UI panels."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def create_panel(self, content: Any, title: str, border_style: str = "white") -> Panel:
        """Create a basic panel with content."""
        return Panel(content, title=title, border_style=border_style)


class InfoPanel(BasePanelFactory):
    """Factory for informational panels."""
    
    def create_info_panel(self, message: str, title: str = "Info") -> Panel:
        """Create an informational panel."""
        content = Text(message, style="blue")
        return self.create_panel(content, title, "blue")
    
    def create_empty_state_panel(self, message: str, title: str) -> Panel:
        """Create a panel for empty states."""
        content = Text(message, style="dim")
        return self.create_panel(content, title, "dim")


class ErrorPanel(BasePanelFactory):
    """Factory for error panels."""
    
    def create_error_panel(self, message: str, title: str = "Error") -> Panel:
        """Create an error panel."""
        content = Text(message, style="red")
        return self.create_panel(content, title, "red")
    
    def create_warning_panel(self, message: str, title: str = "Warning") -> Panel:
        """Create a warning panel."""
        content = Text(message, style="yellow")
        return self.create_panel(content, title, "yellow")
