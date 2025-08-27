"""
Widget factory and interaction patterns for GitHub CLI TUI.

This module provides factory functions and standardized patterns for creating
consistent, responsive, and accessible TUI widgets.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, Generic, Callable, Literal
from abc import ABC, abstractmethod

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, Checkbox, Collapsible, ContentSwitcher, DataTable, Digits, DirectoryTree,
    Input, Label, Link, ListView, LoadingIndicator, MaskedInput, OptionList, Pretty,
    ProgressBar, RadioButton, RadioSet, Rule, Select, Static, Switch, TabbedContent,
    TabPane, TextArea
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
    async def load_data(self, **kwargs: Any) -> None:
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
    """Responsive data table with adaptive column management and modern features."""

    def __init__(
        self,
        layout_manager: ResponsiveLayoutManager,
        column_configs: list[dict[str, Any]],
        **kwargs: Any
    ) -> None:
        # Enhanced DataTable initialization with modern features
        DataTable.__init__(
            self,
            show_header=kwargs.pop('show_header', True),
            show_row_labels=kwargs.pop('show_row_labels', False),
            zebra_stripes=kwargs.pop('zebra_stripes', True),
            header_height=kwargs.pop('header_height', 1),
            show_cursor=kwargs.pop('show_cursor', True),
            cursor_foreground_priority=kwargs.pop('cursor_foreground_priority', "css"),
            cursor_background_priority=kwargs.pop('cursor_background_priority', "css"),
            **kwargs
        )
        AdaptiveWidget.__init__(self, layout_manager)

        self.column_configs = column_configs
        self._sortable_columns: set[str] = set()
        self._filterable_columns: set[str] = set()
        self._setup_columns()

    def _setup_columns(self) -> None:
        """Setup columns based on configuration with enhanced features."""
        for config in self.column_configs:
            # Add column with enhanced configuration
            column_key = config.get('key', config['label'].lower())
            self.add_column(
                config['label'],
                width=config.get('width'),
                key=column_key
            )

            # Track sortable and filterable columns
            if config.get('sortable', False):
                self._sortable_columns.add(column_key)
            if config.get('filterable', False):
                self._filterable_columns.add(column_key)

    def add_enhanced_row(
        self,
        *cells: Any,
        height: int | None = None,
        key: str | None = None,
        label: str | None = None
    ) -> None:
        """Add a row with enhanced features."""
        self.add_row(*cells, height=height, key=key, label=label)

    def sort_by_column(self, column_key: str, reverse: bool = False) -> None:
        """Sort table by column if sortable."""
        if column_key in self._sortable_columns:
            # Get current data
            rows = []
            for row_key in self.rows:
                row = self.get_row(row_key)
                rows.append((str(row_key), row))

            # Find column index by matching the column key
            column_index = None
            for i, config in enumerate(self.column_configs):
                if config.get('key', config['label'].lower()) == column_key:
                    column_index = i
                    break

            if column_index is not None:
                # Sort rows by column value
                rows.sort(key=lambda x: str(x[1][column_index]) if len(x[1]) > column_index else "", reverse=reverse)

                # Clear and re-add sorted rows
                self.clear()
                for row_key, row_data in rows:
                    self.add_row(*row_data, key=row_key)

    def filter_rows(self, filter_func: Callable[[list[Any]], bool]) -> None:
        """Filter table rows based on a filter function."""
        # Get all current rows
        all_rows = []
        for row_key in self.rows:
            row = self.get_row(row_key)
            all_rows.append((str(row_key), row))

        # Clear table
        self.clear()

        # Re-add filtered rows
        for row_key, row_data in all_rows:
            if filter_func(row_data):
                self.add_row(*row_data, key=row_key)

    def highlight_row(self, row_key: str, highlight: bool = True) -> None:
        """Highlight or unhighlight a specific row."""
        try:
            if highlight:
                self.add_class(f"highlight-row-{row_key}")
            else:
                self.remove_class(f"highlight-row-{row_key}")
        except Exception:
            pass  # Row might not exist

    def get_selected_data(self) -> list[Any] | None:
        """Get data from the currently selected row."""
        if self.cursor_row is not None:
            try:
                return self.get_row_at(self.cursor_row)
            except Exception:
                return None
        return None

    def _on_layout_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
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
        **kwargs: Any
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

    def _on_responsive_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
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

    def __init__(self, message: str = "Loading...", **kwargs: Any) -> None:
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
        **kwargs: Any
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

    def on_input_changed(self, event: Any) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_term = event.value
            if self.search_callback:
                self.search_callback(self.search_term)

    def on_button_pressed(self, event: Any) -> None:
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
        **kwargs: Any
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
    **kwargs: Any
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

    def add_accessibility_attributes(self, widget: Any, **attrs: Any) -> None:
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


# Modern widget factory functions for enhanced basic widgets

def create_enhanced_button(
    label: str,
    button_id: str,
    variant: Literal["default", "primary", "success", "warning", "error"] = "default",
    tooltip: str | None = None,
    disabled: bool = False,
    **kwargs: Any
) -> Button:
    """Create an enhanced button with modern features."""
    button = Button(
        label,
        id=button_id,
        variant=variant,
        disabled=disabled,
        **kwargs
    )

    # Add tooltip if provided (using classes for CSS styling)
    if tooltip:
        button.tooltip = tooltip
        button.add_class("has-tooltip")

    return button


def create_enhanced_input(
    placeholder: str = "",
    input_id: str = "input",
    input_type: str = "text",
    max_length: int | None = None,
    password: bool = False,
    **kwargs: Any
) -> Input:
    """Create an enhanced input with modern features."""
    input_widget = Input(
        placeholder=placeholder,
        id=input_id,
        password=password,
        **kwargs
    )

    if max_length:
        input_widget.max_length = max_length

    # Add type-specific classes for styling
    input_widget.add_class(f"input-{input_type}")

    return input_widget


def create_masked_input(
    template: str,
    placeholder: str = "",
    input_id: str = "masked-input",
    **kwargs: Any
) -> MaskedInput:
    """Create a masked input for formatted data entry."""
    return MaskedInput(
        template=template,
        placeholder=placeholder,
        id=input_id,
        classes="masked-input enhanced-input",
        **kwargs
    )


def create_enhanced_static(
    content: str,
    static_id: str = "static",
    markup: bool = True,
    expand: bool = False,
    **kwargs: Any
) -> Static:
    """Create an enhanced static text widget."""
    static = Static(
        content,
        id=static_id,
        markup=markup,
        expand=expand,
        **kwargs
    )

    # Add enhanced styling classes
    static.add_class("enhanced-static")

    return static


def create_enhanced_label(
    text: str,
    label_id: str = "label",
    for_widget: str | None = None,
    **kwargs: Any
) -> Label:
    """Create an enhanced label with accessibility features."""
    label = Label(
        text,
        id=label_id,
        **kwargs
    )

    # Associate with widget if provided
    if for_widget:
        label.add_class(f"label-for-{for_widget}")

    # Add enhanced styling
    label.add_class("enhanced-label")

    return label


def create_visual_separator(
    line_style: Literal["ascii", "blank", "dashed", "double", "heavy", "hidden", "none", "solid", "thick"] = "solid",
    orientation: Literal["horizontal", "vertical"] = "horizontal",
    separator_id: str = "separator"
) -> Rule:
    """Create a visual separator using Rule widget."""
    return Rule(
        line_style=line_style,
        orientation=orientation,
        id=separator_id,
        classes=f"separator separator-{orientation}"
    )


def create_enhanced_datatable(
    columns: list[dict[str, Any]],
    table_id: str = "enhanced-table",
    sortable: bool = True,
    filterable: bool = True,
    zebra_stripes: bool = True,
    show_cursor: bool = True,
    **kwargs: Any
) -> DataTable:
    """Create an enhanced DataTable with modern features."""
    # Create table with enhanced configuration
    table: DataTable = DataTable(
        id=table_id,
        show_header=kwargs.pop('show_header', True),
        show_row_labels=kwargs.pop('show_row_labels', False),
        zebra_stripes=zebra_stripes,
        header_height=kwargs.pop('header_height', 1),
        show_cursor=show_cursor,
        cursor_foreground_priority=kwargs.pop('cursor_foreground_priority', "css"),
        cursor_background_priority=kwargs.pop('cursor_background_priority', "css"),
        classes="enhanced-datatable modern-table",
        **kwargs
    )

    # Add columns with enhanced configuration
    for column_config in columns:
        table.add_column(
            column_config['label'],
            width=column_config.get('width'),
            key=column_config.get('key', column_config['label'].lower())
        )

    # Add enhanced styling classes
    if sortable:
        table.add_class("sortable-table")
    if filterable:
        table.add_class("filterable-table")

    return table


def create_responsive_enhanced_table(
    layout_manager: ResponsiveLayoutManager,
    columns: list[dict[str, Any]],
    table_id: str = "responsive-enhanced-table",
    **kwargs: Any
) -> ResponsiveTable:
    """Create a responsive table with all modern enhancements."""
    # Mark columns as sortable and filterable by default
    enhanced_columns = []
    for column in columns:
        enhanced_column = column.copy()
        enhanced_column.setdefault('sortable', True)
        enhanced_column.setdefault('filterable', True)
        enhanced_columns.append(enhanced_column)

    return ResponsiveTable(
        layout_manager=layout_manager,
        column_configs=enhanced_columns,
        id=table_id,
        classes="responsive-enhanced-table modern-table adaptive-table",
        **kwargs
    )


# New widget factory functions for modern Textual widgets

def create_digits_display(
    value: str | int | float = "",
    digits_id: str = "digits",
    **kwargs: Any
) -> Digits:
    """Create a digits widget for displaying large numbers."""
    return Digits(
        value=str(value),
        id=digits_id,
        classes="digits-display enhanced-digits",
        **kwargs
    )


def create_link_widget(
    text: str,
    url: str,
    link_id: str = "link",
    **kwargs: Any
) -> Link:
    """Create a clickable link widget."""
    return Link(
        text=text,
        url=url,
        id=link_id,
        classes="link-widget enhanced-link",
        **kwargs
    )


def create_list_view(
    items: list[Any] | None = None,
    list_id: str = "list-view",
    **kwargs: Any
) -> ListView:
    """Create a list view widget for simple item display."""
    list_view = ListView(
        id=list_id,
        classes="list-view enhanced-list",
        **kwargs
    )

    # Note: Items should be added after mounting, not during creation
    # This factory creates the widget, items can be added later via append()

    return list_view


def create_option_list(
    options: list[str] | None = None,
    option_list_id: str = "option-list",
    **kwargs: Any
) -> OptionList:
    """Create an option list widget for selections."""
    option_list = OptionList(
        id=option_list_id,
        classes="option-list enhanced-options",
        **kwargs
    )

    if options:
        for text in options:
            option_list.add_option(text)

    return option_list


def create_pretty_display(
    content: Any,
    pretty_id: str = "pretty",
    **kwargs: Any
) -> Pretty:
    """Create a pretty widget for formatted object display."""
    return Pretty(
        content,
        id=pretty_id,
        classes="pretty-display enhanced-pretty",
        **kwargs
    )


def create_checkbox(
    label: str = "",
    value: bool = False,
    checkbox_id: str = "checkbox",
    **kwargs: Any
) -> Checkbox:
    """Create a checkbox widget."""
    return Checkbox(
        label=label,
        value=value,
        id=checkbox_id,
        classes="checkbox enhanced-checkbox",
        **kwargs
    )


def create_radio_button(
    label: str = "",
    value: bool = False,
    radio_id: str = "radio",
    **kwargs: Any
) -> RadioButton:
    """Create a radio button widget."""
    return RadioButton(
        label=label,
        value=value,
        id=radio_id,
        classes="radio-button enhanced-radio",
        **kwargs
    )


def create_radio_set(
    radio_set_id: str = "radio-set",
    **kwargs: Any
) -> RadioSet:
    """Create a radio set widget for exclusive selections.

    Note: RadioSet in Textual 4.0 is a container for RadioButton widgets.
    Individual RadioButton widgets should be added as children after creation.
    """
    radio_set = RadioSet(
        id=radio_set_id,
        classes="radio-set enhanced-radio-set",
        **kwargs
    )

    return radio_set


def create_text_area(
    text: str = "",
    language: str | None = None,
    text_area_id: str = "text-area",
    read_only: bool = False,
    **kwargs: Any
) -> TextArea:
    """Create a text area widget with optional syntax highlighting."""
    return TextArea(
        text=text,
        language=language,
        read_only=read_only,
        id=text_area_id,
        classes="text-area enhanced-text-area",
        **kwargs
    )


def create_collapsible_section(
    title: str,
    content: Any = None,
    collapsed: bool = False,
    collapsible_id: str = "collapsible",
    **kwargs: Any
) -> Collapsible:
    """Create a collapsible section widget."""
    collapsible = Collapsible(
        title=title,
        collapsed=collapsed,
        id=collapsible_id,
        classes="collapsible-section enhanced-collapsible",
        **kwargs
    )

    if content:
        collapsible.compose_add_child(content)

    return collapsible


def create_content_switcher(
    initial: str | None = None,
    switcher_id: str = "content-switcher",
    **kwargs: Any
) -> ContentSwitcher:
    """Create a content switcher widget."""
    return ContentSwitcher(
        initial=initial,
        id=switcher_id,
        classes="content-switcher enhanced-switcher",
        **kwargs
    )


def create_directory_tree(
    path: str,
    tree_id: str = "directory-tree",
    **kwargs: Any
) -> DirectoryTree:
    """Create a directory tree widget."""
    return DirectoryTree(
        path=path,
        id=tree_id,
        classes="directory-tree enhanced-tree",
        **kwargs
    )
