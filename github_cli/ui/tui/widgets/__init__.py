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
    create_enhanced_button,
    create_enhanced_input,
    create_masked_input,
    create_enhanced_static,
    create_enhanced_label,
    create_visual_separator,
    create_enhanced_datatable,
    create_responsive_enhanced_table,
    # New widget factory functions
    create_digits_display,
    create_link_widget,
    create_list_view,
    create_option_list,
    create_pretty_display,
    create_checkbox,
    create_radio_button,
    create_radio_set,
    create_text_area,
    create_collapsible_section,
    create_content_switcher,
    create_directory_tree,
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
    'create_enhanced_button',
    'create_enhanced_input',
    'create_masked_input',
    'create_enhanced_static',
    'create_enhanced_label',
    'create_visual_separator',
    'create_enhanced_datatable',
    'create_responsive_enhanced_table',
    # New widget factory functions
    'create_digits_display',
    'create_link_widget',
    'create_list_view',
    'create_option_list',
    'create_pretty_display',
    'create_checkbox',
    'create_radio_button',
    'create_radio_set',
    'create_text_area',
    'create_collapsible_section',
    'create_content_switcher',
    'create_directory_tree',
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
