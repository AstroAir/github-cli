"""
Unit tests for cache utility.

Tests caching functionality including storage, retrieval,
expiration, and cache management.
"""

import pytest
import json
import tempfile
import time
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime, timezone, timedelta

from github_cli.utils.cache import Cache, CacheEntry
from github_cli.utils.config import Config
from github_cli.utils.exceptions import ConfigurationError


@pytest.mark.unit
@pytest.mark.utils
class TestCacheEntry:
    """Test cases for CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation."""
        data = {"key": "value", "number": 42}
        entry = CacheEntry(data)
        
        assert entry.data == data
        assert entry.created_at is not None
        assert entry.expires_at is None
        assert entry.is_expired() is False

    def test_cache_entry_with_ttl(self):
        """Test CacheEntry creation with TTL."""
        data = {"test": "data"}
        ttl = 3600  # 1 hour
        entry = CacheEntry(data, ttl=ttl)
        
        assert entry.data == data
        assert entry.expires_at is not None
        assert entry.is_expired() is False
        
        # Check that expires_at is approximately 1 hour from now
        expected_expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        time_diff = abs((entry.expires_at - expected_expiry).total_seconds())
        assert time_diff < 1  # Within 1 second

    def test_cache_entry_is_expired_false(self):
        """Test CacheEntry.is_expired when not expired."""
        data = {"test": "data"}
        ttl = 3600  # 1 hour in future
        entry = CacheEntry(data, ttl=ttl)
        
        assert entry.is_expired() is False

    def test_cache_entry_is_expired_true(self):
        """Test CacheEntry.is_expired when expired."""
        data = {"test": "data"}
        entry = CacheEntry(data)
        
        # Manually set expiry to past
        entry.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        assert entry.is_expired() is True

    def test_cache_entry_no_expiry(self):
        """Test CacheEntry with no expiry (never expires)."""
        data = {"test": "data"}
        entry = CacheEntry(data)
        
        assert entry.expires_at is None
        assert entry.is_expired() is False

    def test_cache_entry_to_dict(self):
        """Test CacheEntry serialization to dict."""
        data = {"test": "data"}
        ttl = 3600
        entry = CacheEntry(data, ttl=ttl)
        
        entry_dict = entry.to_dict()
        
        assert entry_dict["data"] == data
        assert "created_at" in entry_dict
        assert "expires_at" in entry_dict

    def test_cache_entry_from_dict(self):
        """Test CacheEntry deserialization from dict."""
        now = datetime.now(timezone.utc)
        entry_dict = {
            "data": {"test": "data"},
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat()
        }
        
        entry = CacheEntry.from_dict(entry_dict)
        
        assert entry.data == {"test": "data"}
        assert entry.created_at == now
        assert entry.expires_at == now + timedelta(hours=1)

    def test_cache_entry_from_dict_no_expiry(self):
        """Test CacheEntry deserialization with no expiry."""
        now = datetime.now(timezone.utc)
        entry_dict = {
            "data": {"test": "data"},
            "created_at": now.isoformat(),
            "expires_at": None
        }
        
        entry = CacheEntry.from_dict(entry_dict)
        
        assert entry.data == {"test": "data"}
        assert entry.expires_at is None


@pytest.mark.unit
@pytest.mark.utils
class TestCache:
    """Test cases for Cache class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = Path(self.temp_dir) / "cache.json"
        
        self.mock_config = Mock(spec=Config)
        self.mock_config.get_cache_dir.return_value = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """Test Cache initialization."""
        cache = Cache(self.mock_config)
        
        assert cache.config == self.mock_config
        assert cache._cache == {}
        assert cache._loaded is False

    def test_cache_file_path_property(self):
        """Test cache_file_path property."""
        cache = Cache(self.mock_config)
        
        expected_path = Path(self.temp_dir) / "cache.json"
        assert cache.cache_file_path == expected_path

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = Cache(self.mock_config)
        
        key = "test_key"
        value = {"data": "test_value", "number": 42}
        
        cache.set(key, value)
        result = cache.get(key)
        
        assert result == value

    def test_cache_set_with_ttl(self):
        """Test setting cache value with TTL."""
        cache = Cache(self.mock_config)
        
        key = "test_key"
        value = {"data": "test_value"}
        ttl = 3600
        
        cache.set(key, value, ttl=ttl)
        result = cache.get(key)
        
        assert result == value
        
        # Check that entry has expiry
        entry = cache._cache[key]
        assert entry.expires_at is not None

    def test_cache_get_nonexistent_key(self):
        """Test getting nonexistent cache key."""
        cache = Cache(self.mock_config)
        
        result = cache.get("nonexistent_key")
        
        assert result is None

    def test_cache_get_with_default(self):
        """Test getting cache value with default."""
        cache = Cache(self.mock_config)
        
        default_value = {"default": "value"}
        result = cache.get("nonexistent_key", default=default_value)
        
        assert result == default_value

    def test_cache_get_expired_entry(self):
        """Test getting expired cache entry."""
        cache = Cache(self.mock_config)
        
        key = "test_key"
        value = {"data": "test_value"}
        
        # Set entry and manually expire it
        cache.set(key, value)
        cache._cache[key].expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        result = cache.get(key)
        
        assert result is None
        assert key not in cache._cache  # Should be removed

    def test_cache_has_key_exists(self):
        """Test checking if cache key exists."""
        cache = Cache(self.mock_config)
        
        key = "test_key"
        value = {"data": "test_value"}
        
        cache.set(key, value)
        
        assert cache.has(key) is True

    def test_cache_has_key_not_exists(self):
        """Test checking if nonexistent cache key exists."""
        cache = Cache(self.mock_config)
        
        assert cache.has("nonexistent_key") is False

    def test_cache_has_expired_key(self):
        """Test checking if expired cache key exists."""
        cache = Cache(self.mock_config)
        
        key = "test_key"
        value = {"data": "test_value"}
        
        # Set entry and manually expire it
        cache.set(key, value)
        cache._cache[key].expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        assert cache.has(key) is False

    def test_cache_delete_existing_key(self):
        """Test deleting existing cache key."""
        cache = Cache(self.mock_config)
        
        key = "test_key"
        value = {"data": "test_value"}
        
        cache.set(key, value)
        result = cache.delete(key)
        
        assert result is True
        assert cache.has(key) is False

    def test_cache_delete_nonexistent_key(self):
        """Test deleting nonexistent cache key."""
        cache = Cache(self.mock_config)
        
        result = cache.delete("nonexistent_key")
        
        assert result is False

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = Cache(self.mock_config)
        
        # Add multiple entries
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        cache.set("key3", {"data": "value3"})
        
        assert len(cache._cache) == 3
        
        cache.clear()
        
        assert len(cache._cache) == 0

    def test_cache_cleanup_expired(self):
        """Test cleaning up expired cache entries."""
        cache = Cache(self.mock_config)
        
        # Add entries with different expiry times
        cache.set("valid_key", {"data": "valid"}, ttl=3600)  # 1 hour
        cache.set("expired_key1", {"data": "expired1"})
        cache.set("expired_key2", {"data": "expired2"})
        
        # Manually expire some entries
        cache._cache["expired_key1"].expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        cache._cache["expired_key2"].expires_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        assert len(cache._cache) == 3
        
        removed_count = cache.cleanup_expired()
        
        assert removed_count == 2
        assert len(cache._cache) == 1
        assert cache.has("valid_key") is True

    def test_cache_size(self):
        """Test getting cache size."""
        cache = Cache(self.mock_config)
        
        assert cache.size() == 0
        
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        
        assert cache.size() == 2

    def test_cache_keys(self):
        """Test getting cache keys."""
        cache = Cache(self.mock_config)
        
        keys = ["key1", "key2", "key3"]
        for key in keys:
            cache.set(key, {"data": f"value_{key}"})
        
        cache_keys = cache.keys()
        
        assert set(cache_keys) == set(keys)

    def test_cache_load_from_file_success(self):
        """Test loading cache from file."""
        cache = Cache(self.mock_config)
        
        # Create cache file with test data
        now = datetime.now(timezone.utc)
        cache_data = {
            "test_key": {
                "data": {"test": "value"},
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=1)).isoformat()
            }
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        cache._load_from_file()
        
        assert cache.has("test_key") is True
        assert cache.get("test_key") == {"test": "value"}

    def test_cache_load_from_file_not_exists(self):
        """Test loading cache when file doesn't exist."""
        cache = Cache(self.mock_config)
        
        cache._load_from_file()
        
        assert cache._cache == {}
        assert cache._loaded is True

    def test_cache_load_from_file_invalid_json(self):
        """Test loading cache with invalid JSON."""
        cache = Cache(self.mock_config)
        
        # Write invalid JSON to file
        with open(self.cache_file, 'w') as f:
            f.write("invalid json content")
        
        cache._load_from_file()
        
        assert cache._cache == {}
        assert cache._loaded is True

    def test_cache_save_to_file_success(self):
        """Test saving cache to file."""
        cache = Cache(self.mock_config)
        
        # Add test data
        cache.set("test_key", {"test": "value"}, ttl=3600)
        
        cache._save_to_file()
        
        # Verify file was created and contains data
        assert self.cache_file.exists()
        
        with open(self.cache_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "test_key" in saved_data
        assert saved_data["test_key"]["data"] == {"test": "value"}

    def test_cache_save_to_file_permission_error(self):
        """Test saving cache with permission error."""
        cache = Cache(self.mock_config)
        
        cache.set("test_key", {"test": "value"})
        
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(ConfigurationError, match="Failed to save cache"):
                cache._save_to_file()

    def test_cache_auto_load(self):
        """Test automatic cache loading on first access."""
        cache = Cache(self.mock_config)
        
        # Create cache file
        cache_data = {
            "auto_load_key": {
                "data": {"auto": "loaded"},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": None
            }
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        # First access should auto-load
        result = cache.get("auto_load_key")
        
        assert result == {"auto": "loaded"}
        assert cache._loaded is True

    def test_cache_context_manager(self):
        """Test Cache as context manager."""
        with Cache(self.mock_config) as cache:
            cache.set("context_key", {"context": "value"})
        
        # Verify data was saved
        assert self.cache_file.exists()
        
        with open(self.cache_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "context_key" in saved_data

    def test_cache_get_or_set(self):
        """Test get_or_set method."""
        cache = Cache(self.mock_config)
        
        key = "computed_key"
        
        def compute_value():
            return {"computed": "value", "timestamp": time.time()}
        
        # First call should compute and cache
        result1 = cache.get_or_set(key, compute_value)
        
        # Second call should return cached value
        result2 = cache.get_or_set(key, compute_value)
        
        assert result1 == result2
        assert result1["computed"] == "value"

    def test_cache_get_or_set_with_ttl(self):
        """Test get_or_set method with TTL."""
        cache = Cache(self.mock_config)
        
        key = "computed_key"
        ttl = 3600
        
        def compute_value():
            return {"computed": "value"}
        
        result = cache.get_or_set(key, compute_value, ttl=ttl)
        
        assert result == {"computed": "value"}
        assert cache.has(key) is True
        
        # Check that entry has expiry
        entry = cache._cache[key]
        assert entry.expires_at is not None

    def test_cache_statistics(self):
        """Test cache statistics."""
        cache = Cache(self.mock_config)
        
        # Add some entries
        cache.set("key1", {"data": "value1"}, ttl=3600)
        cache.set("key2", {"data": "value2"})
        cache.set("key3", {"data": "value3"}, ttl=1800)
        
        # Expire one entry
        cache._cache["key3"].expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        stats = cache.get_statistics()
        
        assert stats["total_entries"] == 3
        assert stats["expired_entries"] == 1
        assert stats["valid_entries"] == 2
