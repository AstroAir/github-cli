#!/usr/bin/env python3
"""
Test application for GitHub CLI TUI modern widgets.
This script tests the visual appearance and basic functionality of new widgets.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static

from github_cli.ui.tui.widgets.factory import (
    create_digits_display, create_link_widget, create_list_view,
    create_option_list, create_pretty_display, create_checkbox,
    create_radio_button, create_radio_set, create_text_area,
    create_collapsible_section, create_content_switcher, create_directory_tree
)


class WidgetTestApp(App):
    """Test application for modern Textual widgets."""
    
    TITLE = "GitHub CLI TUI - Widget Test"
    CSS_PATH = "github_cli/ui/tui/github_tui.tcss"
    
    def compose(self) -> ComposeResult:
        """Compose the test interface."""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="test-panels"):
                # Test Digits widget
                yield Static("Digits Widget Test:", classes="test-label")
                with Horizontal():
                    yield create_digits_display(12345, "test-digits-1")
                    yield create_digits_display("99.9%", "test-digits-2")
                
                # Test Link widget
                yield Static("Link Widget Test:", classes="test-label")
                yield create_link_widget("Visit GitHub", "https://github.com", "test-link")
                
                # Test Checkbox widget
                yield Static("Checkbox Widget Test:", classes="test-label")
                with Horizontal():
                    yield create_checkbox("Enable notifications", True, "test-checkbox-1")
                    yield create_checkbox("Dark mode", False, "test-checkbox-2")
                
                # Test OptionList widget
                yield Static("OptionList Widget Test:", classes="test-label")
                yield create_option_list(["Option A", "Option B", "Option C"], "test-options")
                
                # Test TextArea widget
                yield Static("TextArea Widget Test:", classes="test-label")
                code_sample = '''def hello_world():
    """A simple Python function."""
    print("Hello, World!")
    return True'''
                yield create_text_area(code_sample, "python", "test-textarea")
                
                # Test Pretty widget
                yield Static("Pretty Widget Test:", classes="test-label")
                test_data = {
                    "repository": "github-cli",
                    "stars": 1234,
                    "language": "Python",
                    "features": ["TUI", "API", "Responsive"]
                }
                yield create_pretty_display(test_data, "test-pretty")
        
        yield Footer()


if __name__ == "__main__":
    app = WidgetTestApp()
    app.run()
