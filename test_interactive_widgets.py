#!/usr/bin/env python3
"""
Interactive test for GitHub CLI TUI modern widgets.
Tests keyboard navigation, clicks, and form interactions.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Checkbox, OptionList
from textual import on

from github_cli.ui.tui.widgets.factory import (
    create_digits_display, create_link_widget, create_option_list,
    create_checkbox, create_radio_button, create_text_area,
    create_collapsible_section
)


class InteractiveTestApp(App):
    """Interactive test application for modern Textual widgets."""
    
    TITLE = "GitHub CLI TUI - Interactive Widget Test"
    CSS_PATH = "github_cli/ui/tui/github_tui.tcss"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_checkbox", "Toggle Checkbox"),
        ("r", "select_radio", "Select Radio"),
        ("o", "select_option", "Select Option"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the interactive test interface."""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="test-panels"):
                # Status display
                yield Static("Interactive Widget Test - Use keyboard shortcuts!", 
                           id="status", classes="test-status")
                
                # Test interactive widgets
                yield Static("Interactive Widgets:", classes="test-label")
                
                # Checkbox test
                with Horizontal():
                    yield create_checkbox("Enable feature", False, "test-checkbox")
                    yield Static("← Press 't' to toggle", classes="hint")
                
                # OptionList test
                yield create_option_list(
                    ["GitHub", "GitLab", "Bitbucket"], 
                    "test-options"
                )
                yield Static("↑ Use arrow keys to navigate, Enter to select", classes="hint")
                
                # TextArea test
                yield Static("Code Editor (with syntax highlighting):", classes="test-label")
                code_sample = '''# GitHub CLI TUI Test
def test_function():
    """Test function with syntax highlighting."""
    widgets = ["Digits", "Link", "Checkbox"]
    return len(widgets) > 0'''
                yield create_text_area(code_sample, "python", "test-textarea")
                
                # Collapsible test
                yield create_collapsible_section(
                    "📊 Statistics (Click to expand)", 
                    None, True, "test-collapsible"
                )
                
                # Results display
                yield Static("Test Results:", classes="test-label")
                yield Static("Ready for testing...", id="results", classes="results")
        
        yield Footer()
    
    @on(Checkbox.Changed, "#test-checkbox")
    def on_checkbox_changed(self, event):
        """Handle checkbox changes."""
        status = "checked" if event.value else "unchecked"
        self.query_one("#results").update(f"Checkbox {status}")
    
    @on(OptionList.OptionSelected, "#test-options")
    def on_option_selected(self, event):
        """Handle option selection."""
        self.query_one("#results").update(f"Selected: {event.option.prompt}")
    
    def action_toggle_checkbox(self):
        """Toggle checkbox via keyboard shortcut."""
        checkbox = self.query_one("#test-checkbox")
        checkbox.value = not checkbox.value
    
    def action_select_option(self):
        """Select first option via keyboard shortcut."""
        option_list = self.query_one("#test-options")
        if option_list.option_count > 0:
            option_list.highlighted = 0


if __name__ == "__main__":
    app = InteractiveTestApp()
    app.run()
