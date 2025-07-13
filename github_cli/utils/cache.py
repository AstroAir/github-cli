"""
Cache manager for GitHub CLI
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError


class CacheManager:
    """Manages caching for GitHub CLI"""

    def __init__(self, config: Config, mode: str = "use"):
        self.config = config
        self.mode = mode  # use, refresh, ignore
        self.logger = logging.getLogger(__name__)

        # Cache directory
        self.cache_dir = Path.home() / ".github-cli" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache settings
        self.default_ttl = config.get("cache.default_ttl", 3600)  # 1 hour
        self.max_cache_size = config.get(
            "cache.max_size", 100 * 1024 * 1024)  # 100MB

    def _get_cache_key(self, key: str) -> str:
        """Generate a cache key hash"""
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key"""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if self.mode == "ignore":
            return default

        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return default

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check if cache is expired
            if cache_data.get('expires_at', 0) < time.time():
                cache_file.unlink(missing_ok=True)
                return default

            return cache_data.get('data', default)

        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"Failed to read cache for key {key}: {e}")
            cache_file.unlink(missing_ok=True)
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if self.mode == "ignore":
            return

        # Use default TTL if none provided
        ttl_value = self.default_ttl if ttl is None else ttl

        cache_file = self._get_cache_file(key)

        current_time = time.time()
        cache_data = {
            'data': value,
            'created_at': current_time,
            'expires_at': current_time + ttl_value,
            'key': key
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, default=str, indent=2)

        except OSError as e:
            self.logger.warning(f"Failed to write cache for key {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete value from cache"""
        cache_file = self._get_cache_file(key)
        cache_file.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
        self.logger.info("Cache cleared")

    def is_cached(self, key: str) -> bool:
        """Check if key is cached and not expired"""
        if self.mode == "ignore":
            return False

        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return False

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            return cache_data.get('expires_at', 0) >= time.time()

        except (json.JSONDecodeError, OSError):
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())

        valid_entries = 0
        expired_entries = 0

        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                if cache_data.get('expires_at', 0) >= time.time():
                    valid_entries += 1
                else:
                    expired_entries += 1

            except (json.JSONDecodeError, OSError):
                expired_entries += 1

        return {
            'total_entries': len(cache_files),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'total_size': total_size,
            'cache_dir': str(self.cache_dir)
        }

    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        cleaned = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                if cache_data.get('expires_at', 0) < time.time():
                    cache_file.unlink()
                    cleaned += 1

            except (json.JSONDecodeError, OSError):
                cache_file.unlink(missing_ok=True)
                cleaned += 1

        self.logger.info(f"Cleaned up {cleaned} expired cache entries")
        return cleaned

    def cache_api_response(self, endpoint: str, params: Dict[str, Any], response: Any, ttl: Optional[int] = None) -> None:
        """Cache an API response"""
        # Create a cache key from endpoint and parameters
        cache_key = f"api:{endpoint}:{json.dumps(params, sort_keys=True)}"
        self.set(cache_key, response, ttl)

    def get_cached_api_response(self, endpoint: str, params: Dict[str, Any]) -> Any:
        """Get cached API response"""
        cache_key = f"api:{endpoint}:{json.dumps(params, sort_keys=True)}"
        return self.get(cache_key)
