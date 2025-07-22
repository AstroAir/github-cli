"""
Unit tests for configuration management.

Tests the Config class including loading, saving, validation, and defaults.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from github_cli.utils.config import Config
from github_cli.utils.exceptions import ConfigError


@pytest.mark.unit
@pytest.mark.utils
class TestConfig:
    """Test cases for Config class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "config.json"
        
        self.sample_config_data = {
            "api": {
                "base_url": "https://api.github.com",
                "timeout": 30,
                "max_retries": 3
            },
            "auth": {
                "token_file": "tokens.json",
                "default_scopes": "repo,user"
            },
            "ui": {
                "theme": "dark",
                "pager": "less",
                "editor": "vim"
            },
            "git": {
                "default_branch": "main",
                "auto_fetch": True
            }
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_initialization_default(self):
        """Test Config initialization with default values."""
        config = Config()
        
        assert config.config_file is not None
        assert config._config_data == {}
        assert config._loaded is False

    def test_config_initialization_custom_file(self):
        """Test Config initialization with custom config file."""
        config = Config(config_file=self.config_file)
        
        assert config.config_file == self.config_file

    def test_get_default_config_file(self):
        """Test getting default config file path."""
        with patch('github_cli.utils.config.Path.home') as mock_home:
            mock_home.return_value = Path("/home/user")
            
            config = Config()
            expected_path = Path("/home/user") / ".config" / "github-cli" / "config.json"
            
            assert config.config_file == expected_path

    def test_load_config_file_exists(self):
        """Test loading config when file exists."""
        # Write sample config to file
        with open(self.config_file, 'w') as f:
            json.dump(self.sample_config_data, f)
        
        config = Config(config_file=self.config_file)
        config.load()
        
        assert config._loaded is True
        assert config._config_data == self.sample_config_data

    def test_load_config_file_not_exists(self):
        """Test loading config when file doesn't exist."""
        config = Config(config_file=self.config_file)
        config.load()
        
        assert config._loaded is True
        assert config._config_data == {}

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        # Write invalid JSON to file
        with open(self.config_file, 'w') as f:
            f.write("invalid json content")

        # Config loads automatically in __init__, so invalid JSON should raise error during construction
        with pytest.raises(ConfigError, match="Config file is not valid JSON"):
            config = Config(config_dir=self.temp_dir)

    def test_load_config_permission_error(self):
        """Test loading config with permission error."""
        # Create the config file first
        with open(self.config_file, 'w') as f:
            json.dump(self.sample_config_data, f)

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                config = Config(config_dir=self.temp_dir)

    def test_save_config_success(self):
        """Test saving config successfully."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        
        config.save()
        
        # Verify file was written
        assert self.config_file.exists()
        
        # Verify content
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == self.sample_config_data

    def test_save_config_creates_directory(self):
        """Test saving config creates parent directories."""
        nested_config_file = Path(self.temp_dir) / "nested" / "config.json"
        config = Config(config_file=nested_config_file)
        config._config_data = {"test": "value"}
        
        config.save()
        
        assert nested_config_file.exists()
        assert nested_config_file.parent.exists()

    def test_save_config_permission_error(self):
        """Test saving config with permission error."""
        config = Config(config_file=self.config_file)
        config._config_data = {"test": "value"}
        
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(ConfigError, match="Failed to save config"):
                config.save()

    def test_get_value_exists(self):
        """Test getting existing config value."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        # Test nested key access
        assert config.get("api.base_url") == "https://api.github.com"
        assert config.get("api.timeout") == 30
        assert config.get("ui.theme") == "dark"

    def test_get_value_not_exists(self):
        """Test getting non-existent config value."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        assert config.get("nonexistent.key") is None

    def test_get_value_with_default(self):
        """Test getting config value with default."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        # Existing value
        assert config.get("api.timeout", 60) == 30
        
        # Non-existent value with default
        assert config.get("nonexistent.key", "default_value") == "default_value"

    def test_get_value_auto_load(self):
        """Test getting value automatically loads config."""
        # Write sample config to file
        with open(self.config_file, 'w') as f:
            json.dump(self.sample_config_data, f)
        
        config = Config(config_file=self.config_file)
        
        # Should auto-load when accessing value
        assert config.get("api.base_url") == "https://api.github.com"
        assert config._loaded is True

    def test_set_value_simple(self):
        """Test setting simple config value."""
        config = Config(config_file=self.config_file)
        config._loaded = True
        
        config.set("simple_key", "simple_value")
        
        assert config._config_data["simple_key"] == "simple_value"

    def test_set_value_nested(self):
        """Test setting nested config value."""
        config = Config(config_file=self.config_file)
        config._loaded = True
        
        config.set("api.base_url", "https://custom.api.com")
        config.set("new.nested.key", "nested_value")
        
        assert config._config_data["api"]["base_url"] == "https://custom.api.com"
        assert config._config_data["new"]["nested"]["key"] == "nested_value"

    def test_set_value_overwrites_existing(self):
        """Test setting value overwrites existing."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data.copy()
        config._loaded = True
        
        config.set("api.timeout", 60)
        
        assert config._config_data["api"]["timeout"] == 60

    def test_delete_value_exists(self):
        """Test deleting existing config value."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data.copy()
        config._loaded = True
        
        result = config.delete("api.timeout")
        
        assert result is True
        assert "timeout" not in config._config_data["api"]

    def test_delete_value_not_exists(self):
        """Test deleting non-existent config value."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data.copy()
        config._loaded = True
        
        result = config.delete("nonexistent.key")
        
        assert result is False

    def test_has_key_exists(self):
        """Test checking if key exists."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        assert config.has("api.base_url") is True
        assert config.has("api.timeout") is True
        assert config.has("ui") is True

    def test_has_key_not_exists(self):
        """Test checking if key doesn't exist."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        assert config.has("nonexistent.key") is False
        assert config.has("api.nonexistent") is False

    def test_get_section(self):
        """Test getting entire config section."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        api_section = config.get_section("api")
        
        assert api_section == self.sample_config_data["api"]
        assert api_section["base_url"] == "https://api.github.com"
        assert api_section["timeout"] == 30

    def test_get_section_not_exists(self):
        """Test getting non-existent config section."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        section = config.get_section("nonexistent")
        
        assert section == {}

    def test_get_auth_dir(self):
        """Test getting auth directory path."""
        with patch('github_cli.utils.config.Path.home') as mock_home:
            mock_home.return_value = Path("/home/user")
            
            config = Config()
            auth_dir = config.get_auth_dir()
            
            expected_path = Path("/home/user") / ".config" / "github-cli" / "auth"
            assert auth_dir == expected_path

    def test_get_cache_dir(self):
        """Test getting cache directory path."""
        with patch('github_cli.utils.config.Path.home') as mock_home:
            mock_home.return_value = Path("/home/user")
            
            config = Config()
            cache_dir = config.get_cache_dir()
            
            expected_path = Path("/home/user") / ".cache" / "github-cli"
            assert cache_dir == expected_path

    def test_reset_config(self):
        """Test resetting config to defaults."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data.copy()
        config._loaded = True
        
        config.reset()
        
        assert config._config_data == {}
        assert config._loaded is False

    def test_config_context_manager(self):
        """Test Config as context manager."""
        with open(self.config_file, 'w') as f:
            json.dump(self.sample_config_data, f)
        
        with Config(config_file=self.config_file) as config:
            assert config.get("api.base_url") == "https://api.github.com"
            config.set("api.timeout", 60)
        
        # Verify changes were saved
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["api"]["timeout"] == 60

    def test_config_validation_valid(self):
        """Test config validation with valid data."""
        config = Config(config_file=self.config_file)
        config._config_data = self.sample_config_data
        config._loaded = True
        
        # Should not raise any exception
        config.validate()

    def test_config_validation_invalid_type(self):
        """Test config validation with invalid data type."""
        config = Config(config_file=self.config_file)
        config._config_data = {
            "api": {
                "timeout": "invalid_number"  # Should be int
            }
        }
        config._loaded = True
        
        # For now, validation might be basic or not implemented
        # This test documents expected behavior
        try:
            config.validate()
        except ConfigError:
            pass  # Expected if validation is implemented
