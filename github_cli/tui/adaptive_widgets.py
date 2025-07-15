"""
Adaptive widget utilities for responsive GitHub CLI TUI components.

This module provides base classes and utilities for creating widgets that
automatically adapt to different terminal sizes and layout configurations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Static, Label
from textual.geometry import Size

from github_cli.tui.responsive import ResponsiveLayoutManager, AdaptiveWidget


@runtime_checkable
class ResponsiveWidget(Protocol):
    """Protocol for widgets that support responsive layout."""

    def update_layout(self, layout_manager: ResponsiveLayoutManager) -> None:
        """Update the widget layout based on the layout manager."""
        ...

    def get_minimum_size(self) -> Size:
        """Get the minimum size this widget requires."""
        ...


class AdaptiveContainer(Container, AdaptiveWidget):
    """Container that automatically adapts its layout based on available space."""

    def __init__(self, layout_manager: ResponsiveLayoutManager, **kwargs) -> None:
        Container.__init__(self, **kwargs)
        AdaptiveWidget.__init__(self, layout_manager)

        self._content_widgets = []
        self._layout_strategy = "auto"  # auto, horizontal, vertical, grid

    def set_layout_strategy(self, strategy: str) -> None:
        """Set the layout strategy for this container."""
        self._layout_strategy = strategy
        self._update_container_layout()

    def add_adaptive_content(self, widget, priority: int = 0, min_width: int = 0, min_height: int = 0) -> None:
        """Add content with responsive priority and minimum size requirements."""
        self._content_widgets.append({
            'widget': widget,
            'priority': priority,
            'min_width': min_width,
            'min_height': min_height,
            'visible': True
        })
        self._update_container_layout()

    def _on_layout_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle layout changes by reorganizing content."""
        self._update_container_layout()

    def _update_container_layout(self) -> None:
        """Update the container layout based on current configuration."""
        if not self.layout_manager.current_breakpoint:
            return

        breakpoint = self.layout_manager.current_breakpoint
        available_width = self.layout_manager.app.size.width
        available_height = self.layout_manager.app.size.height

        # Determine optimal layout based on content and space
        if self._layout_strategy == "auto":
            if breakpoint.compact_mode or available_width < 80:
                layout_type = "vertical"
            else:
                layout_type = "horizontal"
        else:
            layout_type = self._layout_strategy

        # Hide/show widgets based on priority and space constraints
        visible_widgets = []
        total_required_width = 0

        for content in sorted(self._content_widgets, key=lambda x: x['priority'], reverse=True):
            if layout_type == "horizontal":
                if total_required_width + content['min_width'] <= available_width:
                    content['visible'] = True
                    visible_widgets.append(content)
                    total_required_width += content['min_width']
                else:
                    content['visible'] = False
            else:
                # For vertical layout, show all widgets but consider height
                content['visible'] = True
                visible_widgets.append(content)

        # Apply visibility changes
        for content in self._content_widgets:
            if hasattr(content['widget'], 'display'):
                content['widget'].display = content['visible']


class AdaptiveDataTable(DataTable, AdaptiveWidget):
    """DataTable that automatically adjusts columns based on available space."""

    def __init__(self, layout_manager: ResponsiveLayoutManager, **kwargs) -> None:
        DataTable.__init__(self, **kwargs)
        AdaptiveWidget.__init__(self, layout_manager)

        self._column_configs = []
        self._original_columns = []

    def add_adaptive_column(self,
                            label: str,
                            key: str,
                            width: int | None = None,
                            min_width: int = 10,
                            priority: int = 0,
                            hidden_in_compact: bool = False,
                            **kwargs) -> None:
        """Add a column with adaptive configuration."""
        self._column_configs.append({
            'label': label,
            'key': key,
            'width': width,
            'min_width': min_width,
            'priority': priority,
            'hidden_in_compact': hidden_in_compact,
            'kwargs': kwargs
        })
        self._update_table_columns()

    def _on_layout_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle layout changes by reconfiguring columns."""
        self._update_table_columns()
        self.refresh()

    def _update_table_columns(self) -> None:
        """Update table columns based on current layout."""
        if not self.layout_manager.current_breakpoint:
            return

        breakpoint = self.layout_manager.current_breakpoint
        table_config = self.layout_manager.get_table_config()
        available_width = self.layout_manager.get_content_config()['width']

        # Clear existing columns
        self.clear(columns=True)

        # Sort columns by priority for space allocation
        sorted_columns = sorted(self._column_configs,
                                key=lambda x: x['priority'], reverse=True)

        # Calculate which columns to show
        visible_columns = []
        allocated_width = 0

        for col_config in sorted_columns:
            # Skip if hidden in compact mode
            if breakpoint.compact_mode and col_config['hidden_in_compact']:
                continue

            # Check if we have space for this column
            required_width = col_config['width'] or col_config['min_width']
            if allocated_width + required_width <= available_width or len(visible_columns) == 0:
                visible_columns.append(col_config)
                allocated_width += required_width
            elif not breakpoint.compact_mode:
                # In non-compact mode, try to fit with minimum width
                if allocated_width + col_config['min_width'] <= available_width:
                    col_config['actual_width'] = col_config['min_width']
                    visible_columns.append(col_config)
                    allocated_width += col_config['min_width']

        # Add visible columns to table
        for col_config in visible_columns:
            actual_width = col_config.get('actual_width', col_config['width'])
            self.add_column(
                col_config['label'],
                width=actual_width,
                key=col_config['key'],
                **col_config['kwargs']
            )


class AdaptiveInfoPanel(Container, AdaptiveWidget):
    """Information panel that adapts its content based on available space."""

    def __init__(self, layout_manager: ResponsiveLayoutManager, **kwargs) -> None:
        Container.__init__(self, **kwargs)
        AdaptiveWidget.__init__(self, layout_manager)

        self._info_items = []
        self._compact_items = []

    def add_info_item(self,
                      label: str,
                      value: str,
                      compact_label: str | None = None,
                      priority: int = 0,
                      show_in_compact: bool = True) -> None:
        """Add an information item with adaptive display options."""
        self._info_items.append({
            'label': label,
            'value': value,
            'compact_label': compact_label or label[:3],
            'priority': priority,
            'show_in_compact': show_in_compact
        })
        self._update_info_display()

    def update_info_item(self, label: str, value: str) -> None:
        """Update the value of an existing info item."""
        for item in self._info_items:
            if item['label'] == label:
                item['value'] = value
                break
        self._update_info_display()

    def _on_layout_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle layout changes by updating info display."""
        self._update_info_display()

    def _update_info_display(self) -> None:
        """Update the information display based on current layout."""
        if not self.layout_manager.current_breakpoint:
            return

        breakpoint = self.layout_manager.current_breakpoint

        # Clear existing content
        for widget in self.children:
            widget.remove()

        # Sort items by priority
        sorted_items = sorted(
            self._info_items, key=lambda x: x['priority'], reverse=True)

        if breakpoint.compact_mode:
            # Compact display - horizontal layout with abbreviated labels
            with Horizontal():
                for item in sorted_items:
                    if item['show_in_compact']:
                        self.mount(
                            Label(f"{item['compact_label']}: {item['value']}"))
        else:
            # Full display - vertical layout with full labels
            with Vertical():
                for item in sorted_items:
                    self.mount(Label(f"{item['label']}: {item['value']}"))


def create_adaptive_widget(widget_type: str, layout_manager: ResponsiveLayoutManager, **kwargs):
    """Factory function to create adaptive widgets."""
    widget_map = {
        'container': AdaptiveContainer,
        'datatable': AdaptiveDataTable,
        'infopanel': AdaptiveInfoPanel,
    }

    widget_class = widget_map.get(widget_type)
    if widget_class:
        return widget_class(layout_manager, **kwargs)
    else:
        raise ValueError(f"Unknown adaptive widget type: {widget_type}")


def apply_responsive_styles(widget, layout_manager: ResponsiveLayoutManager) -> None:
    """Apply responsive styles to a widget based on current layout."""
    if not layout_manager.current_breakpoint:
        return

    breakpoint = layout_manager.current_breakpoint

    # Apply compact mode styles
    if breakpoint.compact_mode:
        if hasattr(widget, 'add_class'):
            widget.add_class('compact-mode')
    else:
        if hasattr(widget, 'remove_class'):
            widget.remove_class('compact-mode')

    # Apply size-specific styles
    if hasattr(widget, 'add_class'):
        widget.add_class(f'breakpoint-{breakpoint.name}')


def get_optimal_widget_size(widget_type: str, layout_manager: ResponsiveLayoutManager) -> Size:
    """Get optimal size for a widget type based on current layout."""
    breakpoint = layout_manager.current_breakpoint
    if not breakpoint:
        return Size(80, 24)  # Default size

    content_config = layout_manager.get_content_config()

    size_map = {
        'table': Size(
            content_config['width'] - 2,  # Account for borders
            max(10, layout_manager.app.size.height - 10)
        ),
        'panel': Size(
            content_config['width'] // 3,
            max(5, layout_manager.app.size.height // 4)
        ),
        'dialog': Size(
            min(60, content_config['width'] - 10),
            min(20, layout_manager.app.size.height - 5)
        )
    }

    return size_map.get(widget_type, Size(40, 10))
