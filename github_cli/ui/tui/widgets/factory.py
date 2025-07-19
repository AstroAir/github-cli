"""
Widget factory and interaction patterns for GitHub CLI TUI.

This module provides factory functions and standardized patterns for creating
consistent, responsive, and accessible TUI widgets.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, Generic, Callable
from abc import ABC, abstractmethod

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator,
    Static, Switch, Select, ProgressBar, TabbedContent, TabPane
)
from textual.app import ComposeResult
from textual.binding import Binding
from textual.geometry import Size

from github_cli.api.client import GitHubClient
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager, AdaptiveWidget
from github_cli.ui.tui.screens.error import TUIErrorHandler
from github_cli.ui.tui.utils.data_loader import DataLoader, StateManager

T = TypeVar('T')


class WidgetConfig(Protocol):
    """Configuration protocol for widget creation."""

    def get_bindings(self) -> list[Binding]:
        """Get keyboard bindings for the widget."""
        ...

    def get_classes(self) -> list[str]:
        """Get CSS classes to apply to the widget."""
        ...


class InteractiveWidget(ABC, Generic[T]):
    """Base class for interactive widgets with standardized patterns."""

    def __init__(
        self,
        client: GitHubClient | None = None,
        layout_manager: ResponsiveLayoutManager | None = None,
        error_handler: TUIErrorHandler | None = None,
        data_loader: DataLoader | None = None,
        state_manager: StateManager | None = None
    ) -> None:
        self.client = client
        self.layout_manager = layout_manager
        self.error_handler = error_handler
        self.data_loader = data_loader
        self.state_manager = state_manager

        # Common state
        self.loading = False
        self.data: T | None = None
        self.selected_item: Any = None

    @abstractmethod
    def compose(self) -> ComposeResult:
        """Compose the widget's UI elements."""
        ...

    @abstractmethod
    async def load_data(self, **kwargs) -> None:
        """Load data for the widget."""
        ...

    def get_help_text(self) -> str:
        """Get help text for the widget."""
        return "No help available for this widget."

    def get_status_info(self) -> dict[str, Any]:
        """Get current status information."""
        return {
            'loading': self.loading,
            'has_data': self.data is not None,
            'selected_item': self.selected_item is not None
        }


class ResponsiveTable(DataTable, AdaptiveWidget):
    """Responsive data table with adaptive column management."""

    def __init__(
        self,
        layout_manager: ResponsiveLayoutManager,
        column_configs: list[dict[str, Any]],
        **kwargs
    ) -> None:
        DataTable.__init__(self, **kwargs)
        AdaptiveWidget.__init__(self, layout_manager)

        self.column_configs = column_configs
        self._setup_columns()

    def _setup_columns(self) -> None:
        """Setup columns based on configuration."""
        for config in self.column_configs:
            self.add_column(
                config['label'],
                width=config.get('width'),
                key=config.get('key', config['label'].lower())
            )

    def _on_layout_change(self, old_breakpoint, new_breakpoint) -> None:
        """Adapt table columns based on layout changes."""
        if not new_breakpoint:
            return

        # Hide/show columns based on priority and screen size
        for i, config in enumerate(self.column_configs):
            priority = config.get('priority', 'medium')
            hidden_in_compact = config.get('hidden_in_compact', False)

            should_hide = (
                (new_breakpoint.name in ['xs', 'sm'] and hidden_in_compact) or
                (new_breakpoint.name == 'xs' and priority == 'low') or
                (new_breakpoint.compact_mode and priority == 'very_low')
            )

            # Apply visibility (implementation depends on Textual capabilities)
            if should_hide:
                self.add_class(f"hide-col-{i}")
            else:
                self.remove_class(f"hide-col-{i}")


class ActionPanel(Container):
    """Standardized action panel with responsive button layout."""

    def __init__(
        self,
        actions: list[dict[str, Any]],
        layout_manager: ResponsiveLayoutManager | None = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.actions = actions
        self.layout_manager = layout_manager

        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose action buttons with adaptive layout."""
        with Horizontal(classes="action-panel adaptive-horizontal"):
            for action in self.actions:
                button = Button(
                    action['label'],
                    id=action['id'],
                    variant=action.get('variant', 'default'),
                    classes=f"adaptive-button priority-{action.get('priority', 'medium')}"
                )
                yield button

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if not new_breakpoint:
            return

        # Hide low-priority actions on small screens
        for action in self.actions:
            priority = action.get('priority', 'medium')
            button_id = action['id']

            try:
                button = self.query_one(f"#{button_id}")

                should_hide = (
                    (new_breakpoint.name == 'xs' and priority in ['low', 'very_low']) or
                    (new_breakpoint.name == 'sm' and priority == 'very_low')
                )

                button.display = not should_hide
            except Exception:
                pass  # Button might not exist yet


class LoadingStateWidget(Container):
    """Widget for displaying loading states with progress indication."""

    def __init__(self, message: str = "Loading...", **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = message
        self.progress = 0
        self.total = 100

    def compose(self) -> ComposeResult:
        yield Static(self.message, id="loading-message", classes="loading-message")
        yield LoadingIndicator(id="loading-spinner")
        yield ProgressBar(
            total=self.total,
            show_eta=True,
            id="loading-progress",
            classes="loading-progress"
        )

    def update_progress(self, progress: int, message: str | None = None) -> None:
        """Update loading progress."""
        self.progress = progress

        try:
            progress_bar = self.query_one("#loading-progress", ProgressBar)
            progress_bar.progress = progress

            if message:
                self.message = message
                message_widget = self.query_one("#loading-message", Static)
                message_widget.update(message)
        except Exception:
            pass  # Widgets might not be mounted yet

    def show_error(self, error_message: str) -> None:
        """Show error state."""
        try:
            message_widget = self.query_one("#loading-message", Static)
            message_widget.update(f"❌ {error_message}")

            spinner = self.query_one("#loading-spinner", LoadingIndicator)
            spinner.display = False
        except Exception:
            pass


class SearchableWidget(Container):
    """Widget with integrated search functionality."""

    def __init__(
        self,
        placeholder: str = "Search...",
        search_callback: Callable[[str], None] | None = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.placeholder = placeholder
        self.search_callback = search_callback
        self.search_term = ""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="search-container adaptive-horizontal"):
            yield Input(
                placeholder=self.placeholder,
                id="search-input",
                classes="adaptive-input search-input"
            )
            yield Button("🔍", id="search-button", classes="search-button")
            yield Button("❌", id="clear-search", classes="clear-search-button")

    def on_input_changed(self, event) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_term = event.value
            if self.search_callback:
                self.search_callback(self.search_term)

    def on_button_pressed(self, event) -> None:
        """Handle search button presses."""
        if event.button.id == "clear-search":
            search_input = self.query_one("#search-input", Input)
            search_input.value = ""
            self.search_term = ""
            if self.search_callback:
                self.search_callback("")


class InfoPanel(Container):
    """Panel for displaying key-value information with adaptive layout."""

    def __init__(
        self,
        info_items: list[dict[str, Any]],
        layout_manager: ResponsiveLayoutManager | None = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.info_items = info_items
        self.layout_manager = layout_manager

    def compose(self) -> ComposeResult:
        with Vertical(classes="info-panel adaptive-panel"):
            for item in self.info_items:
                priority = item.get('priority', 'medium')
                classes = f"info-item priority-{priority}"

                if item.get('compact_label'):
                    # Support for compact labels on small screens
                    classes += " has-compact-label"

                yield Label(
                    f"{item['label']}: {item['value']}",
                    classes=classes
                )

    def update_item(self, label: str, new_value: str) -> None:
        """Update an info item value."""
        for item in self.info_items:
            if item['label'] == label:
                item['value'] = new_value
                # Refresh the entire widget instead of trying to update individual labels
                try:
                    self.refresh()
                except Exception:
                    pass
                break


# Factory functions for creating standardized widgets

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


def create_action_panel(
    actions: list[dict[str, Any]],
    layout_manager: ResponsiveLayoutManager | None = None,
    panel_id: str = "action-panel"
) -> ActionPanel:
    """Create a standardized action panel."""
    return ActionPanel(
        actions=actions,
        layout_manager=layout_manager,
        id=panel_id,
        classes="action-panel"
    )


def create_loading_widget(
    message: str = "Loading...",
    widget_id: str = "loading-widget"
) -> LoadingStateWidget:
    """Create a standardized loading widget."""
    return LoadingStateWidget(
        message=message,
        id=widget_id,
        classes="loading-widget"
    )


def create_searchable_container(
    placeholder: str = "Search...",
    search_callback: Callable[[str], None] | None = None,
    container_id: str = "searchable-container"
) -> SearchableWidget:
    """Create a container with integrated search functionality."""
    return SearchableWidget(
        placeholder=placeholder,
        search_callback=search_callback,
        id=container_id,
        classes="searchable-container"
    )


def create_info_panel(
    info_items: list[dict[str, Any]],
    layout_manager: ResponsiveLayoutManager | None = None,
    panel_id: str = "info-panel"
) -> InfoPanel:
    """Create a standardized information panel."""
    return InfoPanel(
        info_items=info_items,
        layout_manager=layout_manager,
        id=panel_id,
        classes="info-panel"
    )


def create_tabbed_interface(
    tabs: list[dict[str, Any]],
    container_id: str = "tabbed-interface"
) -> TabbedContent:
    """Create a standardized tabbed interface."""
    tabbed_content = TabbedContent(
        id=container_id,
        classes="adaptive-tabs responsive-tabs"
    )

    for tab in tabs:
        tab_pane = TabPane(
            tab['title'],
            id=tab.get('id', tab['title'].lower().replace(' ', '-'))
        )
        # Tab content would be added by the calling code
        tabbed_content.add_pane(tab_pane)

    return tabbed_content


# Interaction patterns

class KeyboardShortcutMixin:
    """Mixin for standardized keyboard shortcuts."""

    COMMON_BINDINGS = [
        Binding("ctrl+r", "refresh", "Refresh", priority=True),
        Binding("f5", "refresh", "Refresh"),
        Binding("ctrl+f", "search", "Search"),
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
        Binding("space", "toggle", "Toggle"),
        Binding("ctrl+c", "copy", "Copy"),
        Binding("delete", "delete", "Delete"),
        Binding("f1", "help", "Help"),
    ]

    @classmethod
    def get_standard_bindings(cls, additional_bindings: list[Binding] | None = None) -> list[Binding]:
        """Get standard keyboard bindings with optional additions."""
        bindings = cls.COMMON_BINDINGS.copy()
        if additional_bindings:
            bindings.extend(additional_bindings)
        return bindings


class AccessibilityMixin:
    """Mixin for accessibility features."""

    def add_accessibility_attributes(self, widget: Any, **attrs) -> None:
        """Add accessibility attributes to a widget."""
        # This would depend on Textual's accessibility support
        # For now, we can add classes and IDs for screen readers
        if 'aria_label' in attrs:
            widget.add_class(
                f"aria-label-{attrs['aria_label'].replace(' ', '-')}")

        if 'role' in attrs:
            widget.add_class(f"role-{attrs['role']}")


# Theme and styling utilities

class ThemeFactory:
    """Factory for creating themed widgets."""

    THEMES = {
        'github': {
            'primary_color': '#0366d6',
            'success_color': '#28a745',
            'error_color': '#d73a49',
            'warning_color': '#f66a0a'
        },
        'dark': {
            'primary_color': '#58a6ff',
            'success_color': '#3fb950',
            'error_color': '#f85149',
            'warning_color': '#d29922'
        }
    }

    @classmethod
    def apply_theme(cls, widget: Any, theme: str = 'github') -> None:
        """Apply theme styling to a widget."""
        if theme in cls.THEMES:
            widget.add_class(f"theme-{theme}")
        else:
            widget.add_class("theme-default")


# Widget composition helpers

def compose_standard_screen(
    title: str,
    content_widgets: list[Any],
    actions: list[dict[str, Any]] | None = None,
    layout_manager: ResponsiveLayoutManager | None = None
) -> ComposeResult:
    """Compose a standard screen layout with title, content, and actions."""

    with Container(classes="screen-container adaptive-container"):
        # Title
        yield Static(title, classes="screen-title adaptive-title")

        # Main content area
        with Container(classes="content-area adaptive-layout"):
            for widget in content_widgets:
                yield widget

        # Action panel (if provided)
        if actions:
            yield create_action_panel(actions, layout_manager, "screen-actions")


def compose_dashboard_layout(
    widgets: list[tuple[str, Any]],  # (title, widget) pairs
    columns: int = 2,
    layout_manager: ResponsiveLayoutManager | None = None
) -> ComposeResult:
    """Compose a dashboard-style layout with multiple widgets."""

    with Container(classes="dashboard-container adaptive-container"):
        current_row = None

        for i, (title, widget) in enumerate(widgets):
            # Create new row every 'columns' widgets
            if i % columns == 0:
                current_row = Horizontal(classes="dashboard-row")
                yield current_row

            # Add widget to current row
            with Vertical(classes="dashboard-item adaptive-panel"):
                yield Static(title, classes="dashboard-item-title")
                yield widget
