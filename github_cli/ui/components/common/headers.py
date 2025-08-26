"""
Reusable header components for GitHub CLI UI.
"""

from typing import Optional, Dict, Any
from rich.panel import Panel
from rich.text import Text


class HeaderFactory:
    """Factory for creating header components."""

    @staticmethod
    def create_main_header(title: str, user_info: Optional[Dict[str, Any]] = None) -> Panel:
        """Create the main application header."""
        header_text = Text()
        header_text.append(title, style="bold cyan")

        if user_info:
            username = user_info.get("login", "Unknown")
            header_text.append(" | ")
            header_text.append(f"User: {username}", style="green")

        return Panel(header_text, style="white on blue")

    @staticmethod
    def create_dashboard_header(user_info: Optional[Dict[str, Any]] = None,
                                rate_limit_info: Optional[Dict[str, int]] = None) -> Panel:
        """Create a dashboard-specific header."""
        header_text = Text()
        header_text.append("GitHub CLI", style="bold cyan")

        if user_info:
            username = user_info.get("login", "Unknown")
            header_text.append(" | ")
            header_text.append(f"User: {username}", style="green")

        if rate_limit_info:
            remaining = rate_limit_info.get("remaining")
            if remaining is not None:
                header_text.append(" | ")
                color = "yellow" if remaining < 100 else "green"
                header_text.append(f"API Rate Limit: {remaining}", style=color)

        return Panel(header_text, style="white on blue")

    @staticmethod
    def create_section_header(title: str, style: str = "bold white") -> Text:
        """Create a section header."""
        return Text(title, style=style)
