"""
Plugin manager for GitHub CLI
"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging

from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError


class PluginManager:
    """Manages GitHub CLI plugins"""

    def __init__(self, config: Config):
        self.config = config
        self.plugins: Dict[str, Any] = {}
        self.plugin_commands: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)

        # Plugin directories
        self.plugin_dirs = [
            Path.home() / ".github-cli" / "plugins",
            Path(__file__).parent.parent / "plugins",
            Path.cwd() / ".github-cli-plugins"
        ]

    def load_plugins(self) -> None:
        """Load all available plugins"""
        self.logger.info("Loading plugins...")

        for plugin_dir in self.plugin_dirs:
            if plugin_dir.exists() and plugin_dir.is_dir():
                self._load_plugins_from_directory(plugin_dir)

        self.logger.info(f"Loaded {len(self.plugins)} plugins")

    def _load_plugins_from_directory(self, plugin_dir: Path) -> None:
        """Load plugins from a specific directory"""
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                plugin_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(
                    plugin_name, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Check if plugin has required attributes
                    if hasattr(module, 'PLUGIN_INFO') and hasattr(module, 'register_commands'):
                        self.plugins[plugin_name] = module

                        # Register plugin commands
                        commands = module.register_commands()
                        for cmd_name, cmd_func in commands.items():
                            self.plugin_commands[cmd_name] = cmd_func

                        self.logger.info(f"Loaded plugin: {plugin_name}")
                    else:
                        self.logger.warning(
                            f"Plugin {plugin_name} missing required attributes")

            except Exception as e:
                self.logger.error(f"Failed to load plugin {plugin_file}: {e}")

    def get_plugin_commands(self) -> Dict[str, Callable]:
        """Get all registered plugin commands"""
        return self.plugin_commands.copy()

    def execute_plugin_command(self, command: str, *args, **kwargs) -> Any:
        """Execute a plugin command"""
        if command not in self.plugin_commands:
            raise GitHubCLIError(f"Plugin command '{command}' not found")

        try:
            return self.plugin_commands[command](*args, **kwargs)
        except Exception as e:
            raise GitHubCLIError(f"Plugin command '{command}' failed: {e}")

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with their info"""
        plugin_list = []

        for name, module in self.plugins.items():
            plugin_info = {
                'name': name,
                'version': getattr(module, 'PLUGIN_INFO', {}).get('version', 'unknown'),
                'description': getattr(module, 'PLUGIN_INFO', {}).get('description', 'No description'),
                'author': getattr(module, 'PLUGIN_INFO', {}).get('author', 'Unknown'),
                'commands': list(getattr(module, 'register_commands', lambda: {})().keys())
            }
            plugin_list.append(plugin_info)

        return plugin_list

    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a specific plugin"""
        enabled_plugins = self.config.get("plugins.enabled_list", [])
        if plugin_name not in enabled_plugins:
            enabled_plugins.append(plugin_name)
            self.config.set("plugins.enabled_list", enabled_plugins)

    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a specific plugin"""
        enabled_plugins = self.config.get("plugins.enabled_list", [])
        if plugin_name in enabled_plugins:
            enabled_plugins.remove(plugin_name)
            self.config.set("plugins.enabled_list", enabled_plugins)
