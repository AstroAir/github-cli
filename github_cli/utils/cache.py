"""
Enhanced cache manager for GitHub CLI with improved performance and reliability.
"""

import json
import hashlib
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Union, Callable, TypeVar
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass, field

from github_cli.utils.config import Config
from github_cli.utils.exceptions import GitHubCLIError, ConfigError

T = TypeVar('T')


@dataclass(frozen=True, slots=True)
class CacheEntry:
    """Immutable cache entry with metadata."""
    data: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get the age of the cache entry in seconds."""
        return time.time() - self.created_at

    @property
    def time_to_expire(self) -> float:
        """Get the time until expiration in seconds."""
        return max(0, self.expires_at - time.time())


class CacheManager:
    """Enhanced cache manager with async support and intelligent invalidation."""

    def __init__(self, config: Config, mode: str = "use"):
        self.config = config
        self.mode = mode  # use, refresh, ignore

        # Cache directory setup
        self.cache_dir = Path.home() / ".github-cli" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache settings with validation
        try:
            self.default_ttl = config.get("cache.default_ttl", 3600)  # 1 hour
            self.max_cache_size = config.get(
                "cache.max_size", 100 * 1024 * 1024)  # 100MB
            self.max_entries = config.get("cache.max_entries", 10000)
            self.cleanup_interval = config.get(
                "cache.cleanup_interval", 3600)  # 1 hour
        except Exception as e:
            logger.warning(
                f"Error loading cache configuration, using defaults: {e}")
            self.default_ttl = 3600
            self.max_cache_size = 100 * 1024 * 1024
            self.max_entries = 10000
            self.cleanup_interval = 3600

        # Runtime cache for frequently accessed items
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._last_cleanup = time.time()

        # Performance metrics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "errors": 0
        }

        logger.info(
            f"Cache manager initialized with mode: {mode}, TTL: {self.default_ttl}s")

    def _get_cache_key(self, key: str) -> str:
        """Generate a deterministic cache key hash."""
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key with directory sharding."""
        cache_key = self._get_cache_key(key)
        # Use first 2 chars for directory sharding to avoid too many files in one dir
        shard_dir = self.cache_dir / cache_key[:2]
        shard_dir.mkdir(exist_ok=True)
        return shard_dir / f"{cache_key[2:]}.json"

    async def get(self, key: str, default: T = None) -> T:
        """Get value from cache with async support and performance tracking."""
        if self.mode == "ignore":
            self._stats["misses"] += 1
            return default

        try:
            # Check memory cache first
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not entry.is_expired:
                    # Update access statistics
                    self._memory_cache[key] = CacheEntry(
                        data=entry.data,
                        created_at=entry.created_at,
                        expires_at=entry.expires_at,
                        access_count=entry.access_count + 1,
                        last_accessed=time.time()
                    )
                    self._stats["hits"] += 1
                    logger.debug(f"Cache hit (memory): {key}")
                    return entry.data
                else:
                    # Remove expired entry
                    del self._memory_cache[key]

            # Check disk cache
            cache_file = self._get_cache_file(key)
            if not cache_file.exists():
                self._stats["misses"] += 1
                return default

            # Load and validate cache file
            async with asyncio.to_thread(self._load_cache_file, cache_file) as cache_data:
                if cache_data is None:
                    self._stats["misses"] += 1
                    return default

                entry = CacheEntry(**cache_data)

                if entry.is_expired and self.mode != "refresh":
                    # Remove expired file
                    await asyncio.to_thread(cache_file.unlink, missing_ok=True)
                    self._stats["misses"] += 1
                    return default

                # Add to memory cache for faster future access
                self._memory_cache[key] = entry
                self._stats["hits"] += 1
                logger.debug(
                    f"Cache hit (disk): {key}, age: {entry.age_seconds:.1f}s")
                return entry.data

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._stats["errors"] += 1
            return default

    def _load_cache_file(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Load cache file synchronously."""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache file {cache_file}: {e}")
            # Remove corrupted file
            cache_file.unlink(missing_ok=True)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with async support and intelligent storage."""
        if self.mode == "ignore":
            return False

        try:
            # Use default TTL if none provided
            ttl_value = self.default_ttl if ttl is None else ttl
            current_time = time.time()
            expires_at = current_time + ttl_value

            # Create cache entry
            entry = CacheEntry(
                data=value,
                created_at=current_time,
                expires_at=expires_at,
                access_count=0,
                last_accessed=current_time
            )

            # Store in memory cache
            self._memory_cache[key] = entry

            # Prepare data for disk storage
            cache_data = {
                "data": value,
                "created_at": current_time,
                "expires_at": expires_at,
                "access_count": 0,
                "last_accessed": current_time
            }

            # Write to disk asynchronously
            cache_file = self._get_cache_file(key)
            await asyncio.to_thread(self._save_cache_file, cache_file, cache_data)

            # Perform periodic cleanup
            await self._periodic_cleanup()

            logger.debug(f"Cache set: {key}, TTL: {ttl_value}s")
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._stats["errors"] += 1
            return False

    def _save_cache_file(self, cache_file: Path, cache_data: Dict[str, Any]) -> None:
        """Save cache file synchronously with atomic write."""
        temp_file = cache_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False,
                          separators=(',', ':'))
            # Atomic move
            temp_file.replace(cache_file)
        except Exception as e:
            temp_file.unlink(missing_ok=True)
            raise e

    async def invalidate(self, key: str) -> bool:
        """Remove a specific key from cache."""
        try:
            # Remove from memory cache
            self._memory_cache.pop(key, None)

            # Remove from disk cache
            cache_file = self._get_cache_file(key)
            await asyncio.to_thread(cache_file.unlink, missing_ok=True)

            logger.debug(f"Cache invalidated: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache invalidation error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern (simple glob-style)."""
        count = 0
        try:
            # Invalidate memory cache entries
            keys_to_remove = []
            for key in self._memory_cache:
                if self._pattern_match(key, pattern):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._memory_cache[key]
                count += 1

            # Invalidate disk cache entries
            for shard_dir in self.cache_dir.iterdir():
                if shard_dir.is_dir():
                    for cache_file in shard_dir.glob("*.json"):
                        # This is a simplified approach - in practice you might want
                        # to store original keys in metadata for pattern matching
                        await asyncio.to_thread(cache_file.unlink, missing_ok=True)
                        count += 1

            logger.info(
                f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return count

    def _pattern_match(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys."""
        # Convert glob-style pattern to regex
        import re
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(regex_pattern, key))

    async def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            # Clear memory cache
            self._memory_cache.clear()

            # Clear disk cache
            await asyncio.to_thread(self._clear_disk_cache)

            # Reset stats
            self._stats = {"hits": 0, "misses": 0, "evictions": 0, "errors": 0}

            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def _clear_disk_cache(self) -> None:
        """Clear disk cache synchronously."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup of expired entries."""
        current_time = time.time()
        if current_time - self._last_cleanup < self.cleanup_interval:
            return

        try:
            # Clean memory cache
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._memory_cache[key]
                self._stats["evictions"] += 1

            # Clean disk cache (run in background)
            asyncio.create_task(self._cleanup_disk_cache())

            self._last_cleanup = current_time

            if expired_keys:
                logger.debug(
                    f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    async def _cleanup_disk_cache(self) -> None:
        """Clean up expired disk cache entries."""
        try:
            cleaned_count = 0
            for shard_dir in self.cache_dir.iterdir():
                if not shard_dir.is_dir():
                    continue

                for cache_file in shard_dir.glob("*.json"):
                    try:
                        cache_data = await asyncio.to_thread(self._load_cache_file, cache_file)
                        if cache_data is None:
                            continue

                        entry = CacheEntry(**cache_data)
                        if entry.is_expired:
                            await asyncio.to_thread(cache_file.unlink, missing_ok=True)
                            cleaned_count += 1

                    except Exception:
                        # Remove corrupted files
                        await asyncio.to_thread(cache_file.unlink, missing_ok=True)
                        cleaned_count += 1

            if cleaned_count > 0:
                logger.debug(
                    f"Cleaned up {cleaned_count} expired disk cache files")

        except Exception as e:
            logger.error(f"Disk cache cleanup error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests *
                    100) if total_requests > 0 else 0

        return {
            **self._stats,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_entries": len(self._memory_cache),
            "cache_dir_size_mb": self._get_cache_dir_size() / (1024 * 1024)
        }

    def _get_cache_dir_size(self) -> int:
        """Get total size of cache directory in bytes."""
        try:
            total_size = 0
            for path in self.cache_dir.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
            return total_size
        except Exception:
            return 0

    async def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """Get from cache or set using factory function if not found."""
        # Try to get from cache first
        result = await self.get(key)
        if result is not None:
            return result

        # Generate value using factory
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            # Store in cache
            await self.set(key, value, ttl)
            return value

        except Exception as e:
            logger.error(f"Factory function error for key {key}: {e}")
            raise
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
