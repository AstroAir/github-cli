"""
TUI widgets package.

This package contains reusable widget components for the GitHub CLI TUI,
including factories, adaptive widgets, and responsive components.
"""

from .factory import (
    WidgetConfig,
    InteractiveWidget,
    ResponsiveTable,
    ActionPanel,
    LoadingStateWidget,
    SearchableWidget,
    InfoPanel,
    create_responsive_table,
    create_action_panel,
    create_loading_widget,
    create_searchable_container,
    create_info_panel,
    create_tabbed_interface,
    KeyboardShortcutMixin,
    AccessibilityMixin,
    ThemeFactory,
    compose_standard_screen,
    compose_dashboard_layout
)

from .adaptive import (
    ResponsiveWidget,
    AdaptiveContainer,
    AdaptiveDataTable,
    AdaptiveInfoPanel,
    create_adaptive_widget,
    apply_responsive_styles,
    get_optimal_widget_size
)

__all__ = [
    # Factory components
    'WidgetConfig',
    'InteractiveWidget', 
    'ResponsiveTable',
    'ActionPanel',
    'LoadingStateWidget',
    'SearchableWidget',
    'InfoPanel',
    'create_responsive_table',
    'create_action_panel',
    'create_loading_widget',
    'create_searchable_container',
    'create_info_panel',
    'create_tabbed_interface',
    'KeyboardShortcutMixin',
    'AccessibilityMixin',
    'ThemeFactory',
    'compose_standard_screen',
    'compose_dashboard_layout',
    
    # Adaptive components
    'ResponsiveWidget',
    'AdaptiveContainer',
    'AdaptiveDataTable',
    'AdaptiveInfoPanel',
    'create_adaptive_widget',
    'apply_responsive_styles',
    'get_optimal_widget_size'
]
