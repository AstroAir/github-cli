"""
Configuration management for GitHub CLI
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from github_cli.utils.exceptions import ConfigError


class Config:
    """Configuration manager for GitHub CLI"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the config manager"""
        if config_dir is None:
            # Default to ~/.config/github-cli on Unix, %APPDATA%\github-cli on Windows
            if os.name == 'nt':  # Windows
                base_dir = Path(os.environ.get(
                    'APPDATA', os.path.expanduser('~')))
            else:  # Unix/Mac
                base_dir = Path(os.environ.get(
                    'XDG_CONFIG_HOME', os.path.expanduser('~/.config')))

            self.config_dir = base_dir / 'github-cli'
        else:
            self.config_dir = config_dir

        self.config_file = self.config_dir / 'config.json'
        self.config: Dict[str, Any] = {}

        # Create config directory if it doesn't exist
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load config if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                raise ConfigError("Config file is not valid JSON")
        else:
            # Create default config
            self.config = {
                "oauth": {
                    "client_id": "Iv1.c42d2e9c91e3a928",  # Default client ID
                },
                "api": {
                    "timeout": 30,
                    "max_retries": 3
                },
                "ui": {
                    "theme": "auto",
                    "show_progress": True
                }
            }
            self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by key (supports dot notation)"""
        keys = key.split('.')
        config = self.config

        # Navigate to the innermost dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

        # Save the changes
        self.save()

    def save(self) -> None:
        """Save the configuration to disk"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def delete(self, key: str) -> bool:
        """Delete a configuration value by key"""
        keys = key.split('.')
        config = self.config

        # Navigate to the innermost dict
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                return False
            config = config[k]

        # Delete the value
        if keys[-1] in config:
            del config[keys[-1]]
            self.save()
            return True

        return False

    def reset(self) -> None:
        """Reset the configuration to defaults"""
        if self.config_file.exists():
            self.config_file.unlink()
        # Reinitialize the instance
        self.__init__(self.config_dir)  # type: ignore[misc]

    def get_auth_dir(self) -> Path:
        """Get the authentication directory path"""
        return self.config_dir / "auth"

    def get_cache_dir(self) -> Path:
        """Get the cache directory path"""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get(
                'LOCALAPPDATA', os.path.expanduser('~')))
            return base_dir / 'github-cli' / 'cache'
        else:  # Unix/Mac
            base_dir = Path(os.environ.get('XDG_CACHE_HOME',
                            os.path.expanduser('~/.cache')))
            return base_dir / 'github-cli'
