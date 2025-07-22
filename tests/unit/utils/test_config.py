"""
Unit tests for configuration management - Fixed version.

Tests the Config class with the actual interface implementation.
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
class TestConfigFixed:
    """Test cases for Config class with correct interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.temp_dir / "github-cli"
        self.config_file = self.config_dir / "config.json"
        
        self.sample_config_data = {
            "oauth": {
                "client_id": "test_client_id"
            },
            "api": {
                "timeout": 30,
                "max_retries": 3
            },
            "ui": {
                "theme": "dark",
                "show_progress": True
            }
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_initialization_default(self):
        """Test Config initialization with default settings."""
        config = Config(config_dir=self.config_dir)
        
        assert config.config_dir == self.config_dir
        assert config.config_file == self.config_file
        assert isinstance(config.config, dict)
        # Should have default config
        assert "oauth" in config.config
        assert "api" in config.config
        assert "ui" in config.config

    def test_config_initialization_existing_file(self):
        """Test Config initialization with existing config file."""
        # Create config directory and file
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.sample_config_data, f)
        
        config = Config(config_dir=self.config_dir)
        
        assert config.config == self.sample_config_data

    def test_config_initialization_invalid_json(self):
        """Test Config initialization with invalid JSON."""
        # Create config directory and invalid JSON file
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(ConfigError, match="Config file is not valid JSON"):
            Config(config_dir=self.config_dir)

    def test_get_value_exists(self):
        """Test getting existing config value."""
        # Create config with sample data
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.sample_config_data, f)
        
        config = Config(config_dir=self.config_dir)
        
        # Test nested key access
        assert config.get("oauth.client_id") == "test_client_id"
        assert config.get("api.timeout") == 30
        assert config.get("ui.theme") == "dark"

    def test_get_value_not_exists(self):
        """Test getting non-existent config value."""
        config = Config(config_dir=self.config_dir)
        
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_set_value_simple(self):
        """Test setting simple config value."""
        config = Config(config_dir=self.config_dir)
        
        config.set("simple_key", "simple_value")
        
        assert config.config["simple_key"] == "simple_value"
        # Should auto-save
        assert self.config_file.exists()

    def test_set_value_nested(self):
        """Test setting nested config value."""
        config = Config(config_dir=self.config_dir)
        
        config.set("api.base_url", "https://custom.api.com")
        config.set("new.nested.key", "nested_value")
        
        assert config.config["api"]["base_url"] == "https://custom.api.com"
        assert config.config["new"]["nested"]["key"] == "nested_value"

    def test_delete_value_exists(self):
        """Test deleting existing config value."""
        config = Config(config_dir=self.config_dir)
        config.set("test.key", "value")
        
        result = config.delete("test.key")
        
        assert result is True
        assert config.get("test.key") is None

    def test_delete_value_not_exists(self):
        """Test deleting non-existent config value."""
        config = Config(config_dir=self.config_dir)
        
        result = config.delete("nonexistent.key")
        
        assert result is False

    def test_save_config(self):
        """Test saving config to file."""
        config = Config(config_dir=self.config_dir)
        config.set("test", "value")
        
        # Config should auto-save, but let's call save explicitly
        config.save()
        
        # Verify file was written
        assert self.config_file.exists()
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["test"] == "value"

    def test_reset_config(self):
        """Test resetting config to defaults."""
        config = Config(config_dir=self.config_dir)
        config.set("custom", "value")
        
        config.reset()
        
        # Should have default config again
        assert "oauth" in config.config
        assert "api" in config.config
        assert "ui" in config.config
        assert "custom" not in config.config

    def test_config_creates_directory(self):
        """Test that config creates directory if it doesn't exist."""
        non_existent_dir = self.temp_dir / "new_dir" / "github-cli"
        
        config = Config(config_dir=non_existent_dir)
        
        assert non_existent_dir.exists()
        assert config.config_file.parent.exists()

    def test_config_default_values(self):
        """Test that config has expected default values."""
        config = Config(config_dir=self.config_dir)
        
        # Check default values
        assert config.get("oauth.client_id") == "Iv1.c42d2e9c91e3a928"
        assert config.get("api.timeout") == 30
        assert config.get("api.max_retries") == 3
        assert config.get("ui.theme") == "auto"
        assert config.get("ui.show_progress") is True
