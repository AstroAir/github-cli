# Terminal User Interface (TUI)

The GitHub CLI TUI provides a modern, responsive terminal-based interface built with Textual. It offers an intuitive way to interact with GitHub repositories, pull requests, actions, and more directly from your terminal.

## 🏗️ Architecture Overview

The TUI system is built with a modular, responsive architecture:

```text
github_cli/tui/
├── app.py                    # Main TUI application
├── responsive.py             # Responsive layout management
├── adaptive_widgets.py       # Adaptive widget components
├── widget_factory.py         # Widget creation patterns
├── repositories.py           # Repository management interface
├── pull_requests.py          # Pull request interface
├── actions.py               # GitHub Actions interface
├── notifications.py         # Notifications interface
├── search.py                # Search interface
├── settings.py              # Settings and preferences
├── error_handler.py         # Error handling and recovery
├── data_loader.py           # Data loading and state management
├── shortcuts.py             # Keyboard shortcuts
└── github_tui.tcss          # CSS styling
```

## 🚀 Main Application

### GitHubTUIApp Class

The central TUI application that orchestrates all components:

```python
class GitHubTUIApp(App[None]):
    """Modern GitHub CLI TUI application with comprehensive functionality and responsive design."""
    
    TITLE = "GitHub CLI - Terminal User Interface"
    SUB_TITLE = "Advanced GitHub management in your terminal"
    
    CSS_PATH = "github_tui.tcss"
```

**Key Features:**

- Responsive layout that adapts to terminal size
- Real-time authentication status
- Background data loading
- Comprehensive error handling
- Keyboard shortcuts and accessibility

### Application Lifecycle

```python
async def on_mount(self) -> None:
    """Called when the app is mounted."""
    # Initialize responsive layout
    self.layout_manager.update_layout(self.size)
    
    # Initialize GitHub client
    self.client = GitHubClient(self.authenticator)
    
    # Check authentication status
    await self._check_authentication()
    
    # Start background tasks
    self._start_background_tasks()
```

## 📱 Responsive Design

### Layout Breakpoints

The TUI adapts to different terminal sizes using breakpoints:

```python
class LayoutBreakpoint(NamedTuple):
    name: str
    min_width: int
    min_height: int
    sidebar_width: int
    sidebar_visible: bool
    tabs_horizontal: bool
    compact_mode: bool
```

**Predefined Breakpoints:**

- **Mobile** (< 60 cols): Vertical layout, no sidebar, compact mode
- **Tablet** (60-100 cols): Horizontal layout, collapsible sidebar
- **Desktop** (> 100 cols): Full layout with sidebar and all features

### ResponsiveLayoutManager

Manages layout adaptation and provides configuration for widgets:

```python
class ResponsiveLayoutManager:
    """Manages responsive layout configurations for different terminal sizes."""
    
    def __init__(self, app: App):
        self.app = app
        self.current_breakpoint = None
        self.resize_callbacks = []
    
    def update_layout(self, size: Size) -> None:
        """Update layout based on terminal size."""
        new_breakpoint = self._determine_breakpoint(size)
        
        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            self._notify_layout_change()
```

### Adaptive Layout Strategies

#### Horizontal Layout (Large Screens)

```python
def _compose_horizontal_layout(self) -> ComposeResult:
    """Compose horizontal layout for larger screens."""
    with Horizontal(id="content-area"):
        # Sidebar navigation
        if sidebar_config["visible"]:
            with Vertical(id="sidebar", classes="sidebar adaptive-sidebar"):
                yield Tree("GitHub CLI", id="nav-tree")
                yield Button("🔐 Login", id="login-btn")
                yield Button("🚪 Logout", id="logout-btn")
        
        # Main content area
        yield from self._compose_main_content()
```

#### Vertical Layout (Small Screens)

```python
def _compose_vertical_layout(self) -> ComposeResult:
    """Compose vertical layout for smaller screens."""
    with Vertical(id="content-area-vertical"):
        # Compact navigation bar
        with Horizontal(id="nav-bar", classes="compact-nav"):
            yield Button("🔐", id="login-btn-compact")
            yield Button("🔄", id="refresh-btn-compact")
        
        # Main content (full width)
        yield from self._compose_main_content()
```

## 🧩 Adaptive Widgets

### AdaptiveWidget Protocol

Base interface for responsive widgets:

```python
@runtime_checkable
class AdaptiveWidget(Protocol):
    """Protocol for widgets that can adapt to layout changes."""
    
    def adapt_to_layout(self, layout_config: dict[str, Any]) -> None:
        """Adapt widget to current layout configuration."""
        ...
    
    def get_minimum_size(self) -> Size:
        """Get minimum size required for this widget."""
        ...
```

### AdaptiveDataTable

Data table that automatically adjusts columns based on available space:

```python
class AdaptiveDataTable(DataTable, AdaptiveWidget):
    """DataTable that automatically adjusts columns based on available space."""
    
    def adapt_to_layout(self, layout_config: dict[str, Any]) -> None:
        """Adapt table columns to available space."""
        available_width = layout_config.get('width', 80)
        
        # Hide less important columns in compact mode
        if layout_config.get('compact_mode', False):
            self._hide_optional_columns()
        
        # Adjust column widths
        self._resize_columns(available_width)
```

### AdaptiveContainer

Container that adjusts its layout based on available space:

```python
class AdaptiveContainer(Container, AdaptiveWidget):
    """Container that adapts its layout based on available space."""
    
    def adapt_to_layout(self, layout_config: dict[str, Any]) -> None:
        """Switch between horizontal and vertical layouts."""
        if layout_config.get('compact_mode', False):
            self._switch_to_vertical_layout()
        else:
            self._switch_to_horizontal_layout()
```

## 🎨 Styling and Themes

### CSS Styling

The TUI uses external CSS files for comprehensive styling:

```css
/* Responsive container */
.adaptive-container {
    height: 100%;
    overflow: hidden;
}

/* Responsive sidebar */
.adaptive-sidebar {
    width: auto;
    min-width: 20;
    max-width: 30;
    background: $surface;
    border-right: solid $accent;
}

/* Compact mode utilities */
.compact-hidden {
    display: none;
}

.compact-text {
    text-overflow: ellipsis;
    overflow: hidden;
}
```

### Theme Support

```python
# Color schemes
THEMES = {
    "dark": {
        "background": "#1e1e1e",
        "surface": "#2d2d2d",
        "primary": "#0366d6",
        "accent": "#f85149",
        "text": "#f0f6fc"
    },
    "light": {
        "background": "#ffffff",
        "surface": "#f6f8fa",
        "primary": "#0969da",
        "accent": "#cf222e",
        "text": "#24292f"
    }
}
```

## 🔧 Widget Factory

### Standardized Widget Creation

The widget factory provides consistent patterns for creating widgets:

```python
def create_responsive_table(
    layout_manager: ResponsiveLayoutManager,
    columns: list[dict[str, Any]],
    table_id: str = "data-table",
    **kwargs
) -> ResponsiveTable:
    """Create a responsive data table with standard configuration."""
    return ResponsiveTable(
        layout_manager=layout_manager,
        column_configs=columns,
        id=table_id,
        classes="adaptive-table responsive-table",
        **kwargs
    )
```

### Widget Configuration

```python
class WidgetConfig(Protocol):
    """Configuration protocol for widget creation."""
    
    def get_bindings(self) -> list[Binding]:
        """Get keyboard bindings for the widget."""
        ...
    
    def get_classes(self) -> list[str]:
        """Get CSS classes to apply to the widget."""
        ...
```

## 📊 Feature Interfaces

### Repository Management

```python
def create_repository_widget(
    client: GitHubClient, 
    layout_manager: ResponsiveLayoutManager
) -> Widget:
    """Create repository management interface."""
    
    # Adaptive table for repository list
    table = create_responsive_table(
        layout_manager,
        columns=[
            {"key": "name", "label": "Name", "width": 30},
            {"key": "description", "label": "Description", "width": 50},
            {"key": "stars", "label": "Stars", "width": 10, "optional": True},
            {"key": "language", "label": "Language", "width": 15, "optional": True}
        ]
    )
    
    return RepositoryWidget(client, table, layout_manager)
```

### Pull Request Interface

```python
def create_pull_request_widget(
    client: GitHubClient,
    layout_manager: ResponsiveLayoutManager
) -> Widget:
    """Create pull request management interface."""
    
    # Responsive layout with details panel
    return PullRequestWidget(client, layout_manager)
```

### GitHub Actions Interface

```python
def create_actions_widget(
    client: GitHubClient,
    layout_manager: ResponsiveLayoutManager
) -> Widget:
    """Create GitHub Actions management interface."""
    
    return ActionsWidget(client, layout_manager)
```

## ⌨️ Keyboard Shortcuts

### Global Shortcuts

```python
BINDINGS = [
    Binding("ctrl+c", "quit", "Quit"),
    Binding("ctrl+r", "refresh", "Refresh"),
    Binding("ctrl+l", "toggle_login", "Login/Logout"),
    Binding("ctrl+s", "toggle_sidebar", "Toggle Sidebar"),
    Binding("ctrl+t", "next_tab", "Next Tab"),
    Binding("ctrl+shift+t", "prev_tab", "Previous Tab"),
    Binding("f1", "help", "Help"),
    Binding("f5", "refresh_data", "Refresh Data"),
]
```

### Context-Specific Shortcuts

```python
# Repository shortcuts
REPO_BINDINGS = [
    Binding("enter", "view_repo", "View Repository"),
    Binding("c", "create_repo", "Create Repository"),
    Binding("d", "delete_repo", "Delete Repository"),
    Binding("f", "fork_repo", "Fork Repository"),
    Binding("s", "star_repo", "Star Repository"),
]

# Pull request shortcuts
PR_BINDINGS = [
    Binding("enter", "view_pr", "View Pull Request"),
    Binding("c", "create_pr", "Create Pull Request"),
    Binding("m", "merge_pr", "Merge Pull Request"),
    Binding("r", "review_pr", "Review Pull Request"),
]
```

## 🚨 Error Handling

### TUIErrorHandler

Comprehensive error handling with user-friendly messages:

```python
class TUIErrorHandler:
    """Handles errors in the TUI with user-friendly messages."""
    
    async def handle_error(self, error: Exception) -> None:
        """Handle an error with appropriate user feedback."""
        
        if isinstance(error, AuthenticationError):
            await self._show_auth_error(error)
        elif isinstance(error, NetworkError):
            await self._show_network_error(error)
        elif isinstance(error, GitHubCLIError):
            await self._show_api_error(error)
        else:
            await self._show_generic_error(error)
```

### Error Recovery

```python
async def _show_auth_error(self, error: AuthenticationError) -> None:
    """Show authentication error with recovery options."""
    
    dialog = ErrorDialog(
        title="Authentication Error",
        message=str(error),
        actions=[
            ("Login", self._trigger_login),
            ("Retry", self._retry_operation),
            ("Cancel", self._cancel_operation)
        ]
    )
    
    await self.app.push_screen(dialog)
```

## 📱 Mobile-First Design

### Compact Mode Features

- **Simplified Navigation**: Essential buttons only
- **Condensed Tables**: Hide optional columns
- **Vertical Layouts**: Stack components vertically
- **Touch-Friendly**: Larger touch targets
- **Minimal Text**: Abbreviated labels and descriptions

### Progressive Enhancement

```python
def enhance_for_larger_screens(self, layout_config: dict) -> None:
    """Add features for larger screens."""
    
    if not layout_config.get('compact_mode', False):
        # Add detailed information panels
        self._show_detailed_panels()
        
        # Enable advanced features
        self._enable_advanced_features()
        
        # Show additional columns
        self._show_optional_columns()
```

## 🔧 Configuration

### TUI Settings

```python
@dataclass
class TUIConfig:
    theme: str = "dark"
    auto_refresh: bool = True
    refresh_interval: int = 30
    show_sidebar: bool = True
    compact_threshold: int = 60
    animation_enabled: bool = True
    keyboard_shortcuts: bool = True
```

### User Preferences

```python
class TUIPreferences:
    """Manages user preferences for TUI behavior."""
    
    def save_layout_preference(self, layout_name: str) -> None:
        """Save user's preferred layout."""
        
    def get_preferred_theme(self) -> str:
        """Get user's preferred color theme."""
        
    def set_keyboard_shortcuts(self, enabled: bool) -> None:
        """Enable/disable keyboard shortcuts."""
```

## 📝 Usage Examples

### Launching the TUI

```bash
# Launch TUI
github-cli tui

# Launch with specific theme
github-cli tui --theme light

# Launch in compact mode
github-cli tui --compact
```

### Programmatic Usage

```python
from github_cli.ui.tui.app import GitHubTUIApp

# Create and run TUI application
app = GitHubTUIApp()
await app.run_async()
```

### Custom Widget Creation

```python
from github_cli.ui.tui.widget_factory import create_responsive_table
from github_cli.ui.tui.adaptive_widgets import AdaptiveContainer

# Create custom responsive widget
class CustomWidget(AdaptiveContainer):
    def __init__(self, layout_manager: ResponsiveLayoutManager):
        super().__init__(layout_manager=layout_manager)
        
        # Create responsive table
        self.table = create_responsive_table(
            layout_manager,
            columns=[
                {"key": "name", "label": "Name", "width": 30},
                {"key": "value", "label": "Value", "width": 20}
            ]
        )
    
    def compose(self) -> ComposeResult:
        yield self.table
```

## 🧪 Testing

### TUI Testing

```python
import pytest
from textual.testing import TUITestCase

class TestGitHubTUI(TUITestCase):
    """Test cases for GitHub TUI."""
    
    async def test_app_startup(self):
        """Test TUI application startup."""
        app = GitHubTUIApp()
        async with app.run_test() as pilot:
            # Test initial state
            assert app.authenticated is False
            
            # Test navigation
            await pilot.press("tab")
            await pilot.press("enter")
```

### Responsive Testing

```python
async def test_responsive_layout(self):
    """Test responsive layout adaptation."""
    app = GitHubTUIApp()
    
    # Test small screen
    app.layout_manager.update_layout(Size(50, 20))
    assert app.layout_manager.should_use_vertical_layout()
    
    # Test large screen
    app.layout_manager.update_layout(Size(120, 40))
    assert not app.layout_manager.should_use_vertical_layout()
```

## 🔗 Related Documentation

- [Responsive Design](responsive.md) - Detailed responsive design system
- [Widget System](widgets.md) - Custom widget components
- [Styling Guide](styling.md) - CSS styling and themes
- [Keyboard Shortcuts](shortcuts.md) - Complete shortcut reference
- [API Integration](../api/README.md) - API client integration
