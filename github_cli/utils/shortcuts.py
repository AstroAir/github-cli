"""
Shortcuts manager for GitHub CLI
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging

from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError


class ShortcutsManager:
    """Manages keyboard shortcuts and command aliases for GitHub CLI"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Default shortcuts
        self.default_shortcuts = {
            "ctrl+r": "repo list",
            "ctrl+i": "issue list",
            "ctrl+p": "pr list",
            "ctrl+n": "notify list",
            "ctrl+s": "search repos",
            "ctrl+d": "dashboard",
            "ctrl+q": "quit",
            "ctrl+h": "help",
            "ctrl+/": "help shortcuts",
            "f1": "help",
            "f2": "config",
            "f3": "search",
            "f4": "notifications",
            "f5": "refresh"
        }

        # Command aliases
        self.default_aliases = {
            "r": "repo",
            "i": "issue",
            "pr": "pr",
            "n": "notify",
            "s": "search",
            "c": "config",
            "a": "auth",
            "g": "git",
            "st": "stats",
            "ls": "list",
            "new": "create",
            "rm": "delete",
            "mv": "move",
            "cp": "copy"
        }

        # Load custom shortcuts and aliases
        self.shortcuts = self._load_shortcuts()
        self.aliases = self._load_aliases()

    def _load_shortcuts(self) -> Dict[str, str]:
        """Load shortcuts from config"""
        custom_shortcuts = self.config.get("shortcuts.keyboard", {})
        shortcuts = self.default_shortcuts.copy()
        shortcuts.update(custom_shortcuts)
        return shortcuts

    def _load_aliases(self) -> Dict[str, str]:
        """Load command aliases from config"""
        custom_aliases = self.config.get("shortcuts.aliases", {})
        aliases = self.default_aliases.copy()
        aliases.update(custom_aliases)
        return aliases

    def get_shortcut(self, key: str) -> Optional[str]:
        """Get command for a keyboard shortcut"""
        return self.shortcuts.get(key.lower())

    def get_alias(self, alias: str) -> Optional[str]:
        """Get command for an alias"""
        return self.aliases.get(alias.lower())

    def set_shortcut(self, key: str, command: str) -> None:
        """Set a keyboard shortcut"""
        self.shortcuts[key.lower()] = command
        self._save_shortcuts()

    def set_alias(self, alias: str, command: str) -> None:
        """Set a command alias"""
        self.aliases[alias.lower()] = command
        self._save_aliases()

    def remove_shortcut(self, key: str) -> bool:
        """Remove a keyboard shortcut"""
        key = key.lower()
        if key in self.shortcuts:
            del self.shortcuts[key]
            self._save_shortcuts()
            return True
        return False

    def remove_alias(self, alias: str) -> bool:
        """Remove a command alias"""
        alias = alias.lower()
        if alias in self.aliases:
            del self.aliases[alias]
            self._save_aliases()
            return True
        return False

    def _save_shortcuts(self) -> None:
        """Save shortcuts to config"""
        # Only save non-default shortcuts
        custom_shortcuts = {k: v for k, v in self.shortcuts.items()
                            if k not in self.default_shortcuts or self.default_shortcuts[k] != v}
        self.config.set("shortcuts.keyboard", custom_shortcuts)

    def _save_aliases(self) -> None:
        """Save aliases to config"""
        # Only save non-default aliases
        custom_aliases = {k: v for k, v in self.aliases.items()
                          if k not in self.default_aliases or self.default_aliases[k] != v}
        self.config.set("shortcuts.aliases", custom_aliases)

    def expand_command(self, command: str) -> str:
        """Expand command using aliases"""
        parts = command.split()
        if parts:
            first_part = parts[0].lower()
            if first_part in self.aliases:
                parts[0] = self.aliases[first_part]
                return " ".join(parts)
        return command

    def list_shortcuts(self) -> Dict[str, str]:
        """Get all shortcuts"""
        return self.shortcuts.copy()

    def list_aliases(self) -> Dict[str, str]:
        """Get all aliases"""
        return self.aliases.copy()

    def reset_shortcuts(self) -> None:
        """Reset shortcuts to defaults"""
        self.shortcuts = self.default_shortcuts.copy()
        self.config.delete("shortcuts.keyboard")

    def reset_aliases(self) -> None:
        """Reset aliases to defaults"""
        self.aliases = self.default_aliases.copy()
        self.config.delete("shortcuts.aliases")

    def import_shortcuts(self, shortcuts_file: Path) -> None:
        """Import shortcuts from a file"""
        try:
            with open(shortcuts_file, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            if 'shortcuts' in imported:
                self.shortcuts.update(imported['shortcuts'])
                self._save_shortcuts()

            if 'aliases' in imported:
                self.aliases.update(imported['aliases'])
                self._save_aliases()

            self.logger.info(f"Imported shortcuts from {shortcuts_file}")

        except (json.JSONDecodeError, OSError) as e:
            raise GitHubCLIError(f"Failed to import shortcuts: {e}")

    def export_shortcuts(self, shortcuts_file: Path) -> None:
        """Export shortcuts to a file"""
        try:
            export_data = {
                'shortcuts': self.shortcuts,
                'aliases': self.aliases,
                'exported_at': str(Path(__file__).stat().st_mtime)
            }

            with open(shortcuts_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Exported shortcuts to {shortcuts_file}")

        except OSError as e:
            raise GitHubCLIError(f"Failed to export shortcuts: {e}")

    def get_help_text(self) -> List[str]:
        """Get help text for shortcuts and aliases"""
        help_lines = [
            "Keyboard Shortcuts:",
            "==================",
        ]

        for key, command in sorted(self.shortcuts.items()):
            help_lines.append(f"  {key:<12} -> {command}")

        help_lines.extend([
            "",
            "Command Aliases:",
            "================",
        ])

        for alias, command in sorted(self.aliases.items()):
            help_lines.append(f"  {alias:<12} -> {command}")

        return help_lines
