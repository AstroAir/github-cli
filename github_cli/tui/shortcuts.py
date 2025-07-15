"""
Enhanced keyboard shortcuts and navigation system for GitHub CLI TUI.

This module provides comprehensive keyboard navigation, shortcuts management,
and accessibility features for efficient terminal interaction.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol
from dataclasses import dataclass, field
from enum import Enum

from textual.binding import Binding, BindingType
from textual.app import App
from textual.screen import Screen
from textual.widget import Widget
from loguru import logger


class NavigationMode(Enum):
    """Navigation modes for different contexts."""
    NORMAL = "normal"
    SEARCH = "search"
    EDIT = "edit"
    COMMAND = "command"
    HELP = "help"


class ShortcutScope(Enum):
    """Scope levels for keyboard shortcuts."""
    GLOBAL = "global"          # Available everywhere
    SCREEN = "screen"          # Available in specific screen
    WIDGET = "widget"          # Available in specific widget
    MODE = "mode"              # Available in specific mode


@dataclass
class KeyboardShortcut:
    """Enhanced keyboard shortcut definition."""
    key: str
    action: str
    description: str
    scope: ShortcutScope = ShortcutScope.GLOBAL
    priority: int = 0
    enabled: bool = True
    context: dict[str, Any] = field(default_factory=dict)
    condition: Callable[[], bool] | None = None  # Dynamic enabling condition


@dataclass
class NavigationContext:
    """Current navigation context and state."""
    mode: NavigationMode = NavigationMode.NORMAL
    focus_stack: list[str] = field(default_factory=list)
    breadcrumbs: list[str] = field(default_factory=list)
    current_screen: str | None = None
    current_widget: str | None = None
    search_active: bool = False
    command_mode: bool = False


class ShortcutManager:
    """Manages keyboard shortcuts and navigation patterns."""

    def __init__(self, app: App) -> None:
        self.app = app
        self.shortcuts: dict[str, KeyboardShortcut] = {}
        self.context = NavigationContext()
        self.custom_shortcuts: dict[str, KeyboardShortcut] = {}
        self.disabled_shortcuts: set[str] = set()

        # Setup default shortcuts
        self._setup_default_shortcuts()

    def _setup_default_shortcuts(self) -> None:
        """Setup default keyboard shortcuts."""

        # Global navigation shortcuts
        global_shortcuts = [
            KeyboardShortcut("ctrl+q", "quit", "Quit application",
                             ShortcutScope.GLOBAL, priority=100),
            KeyboardShortcut("escape", "cancel", "Cancel/Go back",
                             ShortcutScope.GLOBAL, priority=90),
            KeyboardShortcut("f1", "help", "Show help",
                             ShortcutScope.GLOBAL, priority=80),
            KeyboardShortcut("ctrl+h", "help", "Show help",
                             ShortcutScope.GLOBAL, priority=80),
            KeyboardShortcut(
                "ctrl+r", "refresh", "Refresh current view", ShortcutScope.GLOBAL, priority=70),
            KeyboardShortcut("f5", "refresh", "Refresh current view",
                             ShortcutScope.GLOBAL, priority=70),
            KeyboardShortcut("ctrl+f", "search", "Search",
                             ShortcutScope.GLOBAL, priority=60),
            KeyboardShortcut("ctrl+g", "goto", "Go to",
                             ShortcutScope.GLOBAL, priority=60),
            KeyboardShortcut("ctrl+n", "new", "New item",
                             ShortcutScope.GLOBAL, priority=50),
            KeyboardShortcut("ctrl+s", "save", "Save",
                             ShortcutScope.GLOBAL, priority=50),
            KeyboardShortcut("ctrl+z", "undo", "Undo",
                             ShortcutScope.GLOBAL, priority=40),
            KeyboardShortcut("ctrl+y", "redo", "Redo",
                             ShortcutScope.GLOBAL, priority=40),
        ]

        # Tab navigation
        tab_shortcuts = [
            KeyboardShortcut("ctrl+tab", "next_tab", "Next tab",
                             ShortcutScope.GLOBAL, priority=30),
            KeyboardShortcut("ctrl+shift+tab", "prev_tab",
                             "Previous tab", ShortcutScope.GLOBAL, priority=30),
            KeyboardShortcut("ctrl+1", "tab_1", "Go to tab 1",
                             ShortcutScope.GLOBAL, priority=20),
            KeyboardShortcut("ctrl+2", "tab_2", "Go to tab 2",
                             ShortcutScope.GLOBAL, priority=20),
            KeyboardShortcut("ctrl+3", "tab_3", "Go to tab 3",
                             ShortcutScope.GLOBAL, priority=20),
            KeyboardShortcut("ctrl+4", "tab_4", "Go to tab 4",
                             ShortcutScope.GLOBAL, priority=20),
            KeyboardShortcut("ctrl+5", "tab_5", "Go to tab 5",
                             ShortcutScope.GLOBAL, priority=20),
        ]

        # GitHub-specific shortcuts
        github_shortcuts = [
            KeyboardShortcut("ctrl+shift+p", "command_palette",
                             "Command palette", ShortcutScope.GLOBAL, priority=85),
            KeyboardShortcut("g r", "goto_repos", "Go to repositories",
                             ShortcutScope.GLOBAL, priority=45),
            KeyboardShortcut("g p", "goto_prs", "Go to pull requests",
                             ShortcutScope.GLOBAL, priority=45),
            KeyboardShortcut("g i", "goto_issues", "Go to issues",
                             ShortcutScope.GLOBAL, priority=45),
            KeyboardShortcut("g a", "goto_actions", "Go to actions",
                             ShortcutScope.GLOBAL, priority=45),
            KeyboardShortcut("g n", "goto_notifications",
                             "Go to notifications", ShortcutScope.GLOBAL, priority=45),
            KeyboardShortcut("g s", "goto_settings", "Go to settings",
                             ShortcutScope.GLOBAL, priority=45),
        ]

        # List/table navigation
        list_shortcuts = [
            KeyboardShortcut("j", "move_down", "Move down",
                             ShortcutScope.WIDGET, priority=35),
            KeyboardShortcut("k", "move_up", "Move up",
                             ShortcutScope.WIDGET, priority=35),
            KeyboardShortcut("h", "move_left", "Move left",
                             ShortcutScope.WIDGET, priority=35),
            KeyboardShortcut("l", "move_right", "Move right",
                             ShortcutScope.WIDGET, priority=35),
            KeyboardShortcut("g g", "goto_top", "Go to top",
                             ShortcutScope.WIDGET, priority=30),
            KeyboardShortcut("shift+g", "goto_bottom",
                             "Go to bottom", ShortcutScope.WIDGET, priority=30),
            KeyboardShortcut("enter", "select", "Select item",
                             ShortcutScope.WIDGET, priority=40),
            KeyboardShortcut("space", "toggle", "Toggle selection",
                             ShortcutScope.WIDGET, priority=40),
            KeyboardShortcut("o", "open", "Open item",
                             ShortcutScope.WIDGET, priority=40),
        ]

        # Authentication shortcuts\n        auth_shortcuts = [\n            KeyboardShortcut(\"ctrl+alt+l\", \"login\", \"Login to GitHub\", ShortcutScope.GLOBAL, priority=55),\n            KeyboardShortcut(\"ctrl+alt+o\", \"logout\", \"Logout from GitHub\", ShortcutScope.GLOBAL, priority=55),\n        ]\n        \n        # Combine all shortcuts\n        all_shortcuts = global_shortcuts + tab_shortcuts + github_shortcuts + list_shortcuts + auth_shortcuts\n        \n        for shortcut in all_shortcuts:\n            self.register_shortcut(shortcut)\n    \n    def register_shortcut(self, shortcut: KeyboardShortcut) -> None:\n        \"\"\"Register a new keyboard shortcut.\"\"\"\n        key = f\"{shortcut.scope.value}:{shortcut.key}\"\n        self.shortcuts[key] = shortcut\n        logger.debug(f\"Registered shortcut: {shortcut.key} -> {shortcut.action}\")\n    \n    def unregister_shortcut(self, key: str, scope: ShortcutScope = ShortcutScope.GLOBAL) -> None:\n        \"\"\"Unregister a keyboard shortcut.\"\"\"\n        full_key = f\"{scope.value}:{key}\"\n        if full_key in self.shortcuts:\n            del self.shortcuts[full_key]\n            logger.debug(f\"Unregistered shortcut: {key}\")\n    \n    def get_active_shortcuts(self, scope: ShortcutScope | None = None) -> list[KeyboardShortcut]:\n        \"\"\"Get currently active shortcuts for a scope.\"\"\"\n        active_shortcuts = []\n        \n        for shortcut in self.shortcuts.values():\n            # Check scope filter\n            if scope and shortcut.scope != scope:\n                continue\n            \n            # Check if shortcut is enabled\n            if not shortcut.enabled or shortcut.key in self.disabled_shortcuts:\n                continue\n            \n            # Check dynamic condition\n            if shortcut.condition and not shortcut.condition():\n                continue\n            \n            active_shortcuts.append(shortcut)\n        \n        # Sort by priority (higher priority first)\n        return sorted(active_shortcuts, key=lambda x: x.priority, reverse=True)\n    \n    def get_bindings_for_scope(self, scope: ShortcutScope) -> list[Binding]:\n        \"\"\"Get Textual bindings for a specific scope.\"\"\"\n        shortcuts = self.get_active_shortcuts(scope)\n        bindings = []\n        \n        for shortcut in shortcuts:\n            binding = Binding(\n                key=shortcut.key,\n                action=shortcut.action,\n                description=shortcut.description,\n                priority=shortcut.priority > 50  # High priority shortcuts\n            )\n            bindings.append(binding)\n        \n        return bindings\n    \n    def disable_shortcut(self, key: str) -> None:\n        \"\"\"Temporarily disable a shortcut.\"\"\"\n        self.disabled_shortcuts.add(key)\n    \n    def enable_shortcut(self, key: str) -> None:\n        \"\"\"Re-enable a disabled shortcut.\"\"\"\n        self.disabled_shortcuts.discard(key)\n    \n    def set_navigation_mode(self, mode: NavigationMode) -> None:\n        \"\"\"Set current navigation mode.\"\"\"\n        old_mode = self.context.mode\n        self.context.mode = mode\n        logger.debug(f\"Navigation mode changed: {old_mode.value} -> {mode.value}\")\n    \n    def push_focus(self, widget_id: str) -> None:\n        \"\"\"Push widget to focus stack.\"\"\"\n        self.context.focus_stack.append(widget_id)\n        self.context.current_widget = widget_id\n    \n    def pop_focus(self) -> str | None:\n        \"\"\"Pop widget from focus stack.\"\"\"\n        if self.context.focus_stack:\n            widget_id = self.context.focus_stack.pop()\n            self.context.current_widget = self.context.focus_stack[-1] if self.context.focus_stack else None\n            return widget_id\n        return None\n    \n    def add_breadcrumb(self, label: str) -> None:\n        \"\"\"Add breadcrumb to navigation trail.\"\"\"\n        self.context.breadcrumbs.append(label)\n    \n    def get_breadcrumbs(self) -> str:\n        \"\"\"Get formatted breadcrumb trail.\"\"\"\n        return \" > \".join(self.context.breadcrumbs)\n    \n    def clear_breadcrumbs(self) -> None:\n        \"\"\"Clear breadcrumb trail.\"\"\"\n        self.context.breadcrumbs.clear()\n\n\nclass NavigationHelper:\n    \"\"\"Helper class for navigation patterns and accessibility.\"\"\"\n    \n    def __init__(self, app: App, shortcut_manager: ShortcutManager) -> None:\n        self.app = app\n        self.shortcut_manager = shortcut_manager\n        self.quick_access_items: dict[str, Callable] = {}\n        \n    def register_quick_access(self, key: str, action: Callable, description: str) -> None:\n        \"\"\"Register a quick access action.\"\"\"\n        self.quick_access_items[key] = action\n        \n        # Register as shortcut too\n        shortcut = KeyboardShortcut(\n            key=key,\n            action=f\"quick_access_{key.replace(' ', '_')}\",\n            description=description,\n            scope=ShortcutScope.GLOBAL\n        )\n        self.shortcut_manager.register_shortcut(shortcut)\n    \n    def handle_vim_navigation(self, key: str, widget: Widget) -> bool:\n        \"\"\"Handle vim-style navigation keys.\"\"\"\n        navigation_map = {\n            'j': 'down',\n            'k': 'up', \n            'h': 'left',\n            'l': 'right',\n            'g g': 'home',\n            'shift+g': 'end',\n            'ctrl+d': 'page_down',\n            'ctrl+u': 'page_up'\n        }\n        \n        if key in navigation_map:\n            action = navigation_map[key]\n            # Send the appropriate action to the widget\n            widget.action(action)\n            return True\n        \n        return False\n    \n    def create_help_text(self, scope: ShortcutScope | None = None) -> str:\n        \"\"\"Create formatted help text for shortcuts.\"\"\"\n        shortcuts = self.shortcut_manager.get_active_shortcuts(scope)\n        \n        if not shortcuts:\n            return \"No shortcuts available.\"\n        \n        # Group shortcuts by category\n        categories = {\n            'Navigation': [],\n            'GitHub': [],\n            'Editing': [],\n            'General': []\n        }\n        \n        for shortcut in shortcuts:\n            # Categorize shortcuts based on action patterns\n            if any(action in shortcut.action for action in ['move', 'goto', 'tab', 'focus']):\n                categories['Navigation'].append(shortcut)\n            elif any(action in shortcut.action for action in ['repo', 'pr', 'issue', 'action', 'notification']):\n                categories['GitHub'].append(shortcut)\n            elif any(action in shortcut.action for action in ['edit', 'save', 'undo', 'redo', 'new']):\n                categories['Editing'].append(shortcut)\n            else:\n                categories['General'].append(shortcut)\n        \n        help_lines = []\n        for category, shortcuts_list in categories.items():\n            if shortcuts_list:\n                help_lines.append(f\"\\n{category}:\")\n                for shortcut in sorted(shortcuts_list, key=lambda x: x.key):\n                    help_lines.append(f\"  {shortcut.key:<20} {shortcut.description}\")\n        \n        return \"\\n\".join(help_lines)\n    \n    def get_context_help(self) -> str:\n        \"\"\"Get contextual help based on current navigation state.\"\"\"\n        context = self.shortcut_manager.context\n        \n        help_text = f\"Navigation Context:\\n\"\n        help_text += f\"Mode: {context.mode.value}\\n\"\n        \n        if context.breadcrumbs:\n            help_text += f\"Location: {self.shortcut_manager.get_breadcrumbs()}\\n\"\n        \n        if context.current_widget:\n            help_text += f\"Active Widget: {context.current_widget}\\n\"\n        \n        help_text += \"\\n\" + self.create_help_text()\n        \n        return help_text\n\n\nclass AccessibilityManager:\n    \"\"\"Manages accessibility features and screen reader support.\"\"\"\n    \n    def __init__(self, app: App) -> None:\n        self.app = app\n        self.screen_reader_mode = False\n        self.high_contrast_mode = False\n        self.reduced_motion = False\n        \n    def enable_screen_reader_mode(self) -> None:\n        \"\"\"Enable screen reader optimizations.\"\"\"\n        self.screen_reader_mode = True\n        # Add screen reader specific classes to the app\n        self.app.add_class(\"screen-reader-mode\")\n        logger.info(\"Screen reader mode enabled\")\n    \n    def set_high_contrast(self, enabled: bool) -> None:\n        \"\"\"Toggle high contrast mode.\"\"\"\n        self.high_contrast_mode = enabled\n        if enabled:\n            self.app.add_class(\"high-contrast\")\n        else:\n            self.app.remove_class(\"high-contrast\")\n        logger.info(f\"High contrast mode: {enabled}\")\n    \n    def set_reduced_motion(self, enabled: bool) -> None:\n        \"\"\"Toggle reduced motion for accessibility.\"\"\"\n        self.reduced_motion = enabled\n        if enabled:\n            self.app.add_class(\"reduced-motion\")\n        else:\n            self.app.remove_class(\"reduced-motion\")\n        logger.info(f\"Reduced motion: {enabled}\")\n    \n    def announce_to_screen_reader(self, message: str) -> None:\n        \"\"\"Announce message to screen reader.\"\"\"\n        if self.screen_reader_mode:\n            # In a real implementation, this would use platform-specific\n            # screen reader APIs or ARIA live regions\n            logger.info(f\"Screen reader announcement: {message}\")\n            # For now, just use the app's notification system\n            self.app.notify(message, timeout=1)\n\n\n# Factory functions and utilities\n\ndef create_shortcut_manager(app: App) -> ShortcutManager:\n    \"\"\"Create and configure a shortcut manager.\"\"\"\n    return ShortcutManager(app)\n\n\ndef create_navigation_helper(app: App, shortcut_manager: ShortcutManager) -> NavigationHelper:\n    \"\"\"Create a navigation helper.\"\"\"\n    return NavigationHelper(app, shortcut_manager)\n\n\ndef create_accessibility_manager(app: App) -> AccessibilityManager:\n    \"\"\"Create an accessibility manager.\"\"\"\n    return AccessibilityManager(app)\n\n\n# Mixin classes for easy integration\n\nclass ShortcutMixin:\n    \"\"\"Mixin for widgets that need shortcut support.\"\"\"\n    \n    def __init__(self, shortcut_manager: ShortcutManager, *args, **kwargs) -> None:\n        super().__init__(*args, **kwargs)\n        self.shortcut_manager = shortcut_manager\n    \n    def get_widget_bindings(self) -> list[Binding]:\n        \"\"\"Get bindings specific to this widget.\"\"\"\n        return self.shortcut_manager.get_bindings_for_scope(ShortcutScope.WIDGET)\n    \n    def register_widget_shortcut(self, key: str, action: str, description: str) -> None:\n        \"\"\"Register a widget-specific shortcut.\"\"\"\n        shortcut = KeyboardShortcut(\n            key=key,\n            action=action,\n            description=description,\n            scope=ShortcutScope.WIDGET\n        )\n        self.shortcut_manager.register_shortcut(shortcut)\n\n\nclass NavigationMixin:\n    \"\"\"Mixin for screens that need navigation support.\"\"\"\n    \n    def __init__(self, navigation_helper: NavigationHelper, *args, **kwargs) -> None:\n        super().__init__(*args, **kwargs)\n        self.navigation_helper = navigation_helper\n    \n    def on_mount(self) -> None:\n        \"\"\"Called when screen is mounted.\"\"\"\n        super().on_mount() if hasattr(super(), 'on_mount') else None\n        # Add breadcrumb for this screen\n        screen_name = self.__class__.__name__.replace('Screen', '')\n        self.navigation_helper.shortcut_manager.add_breadcrumb(screen_name)\n    \n    def on_unmount(self) -> None:\n        \"\"\"Called when screen is unmounted.\"\"\"\n        super().on_unmount() if hasattr(super(), 'on_unmount') else None\n        # Remove breadcrumb\n        self.navigation_helper.shortcut_manager.context.breadcrumbs.pop()\n\n\n# Command palette functionality\n\nclass CommandPalette:\n    \"\"\"Command palette for quick access to actions.\"\"\"\n    \n    def __init__(self, app: App, shortcut_manager: ShortcutManager) -> None:\n        self.app = app\n        self.shortcut_manager = shortcut_manager\n        self.commands: dict[str, dict[str, Any]] = {}\n        \n        # Register built-in commands\n        self._register_builtin_commands()\n    \n    def _register_builtin_commands(self) -> None:\n        \"\"\"Register built-in command palette commands.\"\"\"\n        commands = [\n            {'name': 'Go to Repositories', 'action': 'goto_repos', 'keywords': ['repo', 'repository']},\n            {'name': 'Go to Pull Requests', 'action': 'goto_prs', 'keywords': ['pr', 'pull']},\n            {'name': 'Go to Issues', 'action': 'goto_issues', 'keywords': ['issue', 'bug']},\n            {'name': 'Go to Actions', 'action': 'goto_actions', 'keywords': ['action', 'workflow', 'ci']},\n            {'name': 'Go to Notifications', 'action': 'goto_notifications', 'keywords': ['notification', 'alert']},\n            {'name': 'Go to Settings', 'action': 'goto_settings', 'keywords': ['setting', 'config', 'preference']},\n            {'name': 'Refresh', 'action': 'refresh', 'keywords': ['refresh', 'reload', 'update']},\n            {'name': 'Search', 'action': 'search', 'keywords': ['search', 'find', 'filter']},\n            {'name': 'Help', 'action': 'help', 'keywords': ['help', 'documentation', 'guide']},\n            {'name': 'Quit', 'action': 'quit', 'keywords': ['quit', 'exit', 'close']},\n        ]\n        \n        for cmd in commands:\n            self.register_command(cmd['name'], cmd['action'], cmd['keywords'])\n    \n    def register_command(self, name: str, action: str, keywords: list[str] | None = None) -> None:\n        \"\"\"Register a command in the palette.\"\"\"\n        self.commands[name] = {\n            'action': action,\n            'keywords': keywords or [],\n            'name': name\n        }\n    \n    def search_commands(self, query: str) -> list[dict[str, Any]]:\n        \"\"\"Search commands by name or keywords.\"\"\"\n        query_lower = query.lower()\n        matches = []\n        \n        for cmd_name, cmd_data in self.commands.items():\n            # Check name match\n            if query_lower in cmd_name.lower():\n                matches.append(cmd_data)\n                continue\n            \n            # Check keyword match\n            for keyword in cmd_data['keywords']:\n                if query_lower in keyword.lower():\n                    matches.append(cmd_data)\n                    break\n        \n        return matches\n    \n    def execute_command(self, action: str) -> None:\n        \"\"\"Execute a command action.\"\"\"\n        try:\n            # This would dispatch to the appropriate action handler\n            self.app.action(action)\n        except Exception as e:\n            logger.error(f\"Failed to execute command action '{action}': {e}\")
