"""
Enhanced data loading and state management for GitHub CLI TUI.

This module provides utilities for efficient data loading with caching,
pagination, background loading, and optimistic updates.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Generic, TypeVar, Protocol, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError, APIError
from github_cli.ui.tui.screens.error import TUIErrorHandler

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)  # For Protocol only
K = TypeVar('K')  # Key type


class LoadingState(Enum):
    """States for data loading operations."""
    IDLE = "idle"
    LOADING = "loading"
    REFRESHING = "refreshing"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata and TTL."""
    data: T
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now() > self.expires_at

    def is_stale(self, max_age: timedelta) -> bool:
        """Check if the cache entry is stale based on max age."""
        return datetime.now() - self.created_at > max_age

    def access(self) -> T:
        """Access the cached data and update metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self.data


@dataclass
class LoadResult(Generic[T]):
    """Result of a data loading operation."""
    data: T | None = None
    state: LoadingState = LoadingState.IDLE
    error: GitHubCLIError | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_loading(self) -> bool:
        return self.state in (LoadingState.LOADING, LoadingState.REFRESHING)

    @property
    def is_success(self) -> bool:
        return self.state == LoadingState.SUCCESS and self.data is not None

    @property
    def is_error(self) -> bool:
        return self.state == LoadingState.ERROR


@dataclass
class PaginationState:
    """State for paginated data loading."""
    current_page: int = 1
    per_page: int = 50
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    next_url: str | None = None
    prev_url: str | None = None

    def update_from_response(self, response_data: dict[str, Any]) -> None:
        """Update pagination state from API response."""
        # GitHub API pagination headers
        if 'total_count' in response_data:
            self.total_items = response_data['total_count']
            self.total_pages = (self.total_items +
                                self.per_page - 1) // self.per_page

        # Update navigation flags
        self.has_next = self.current_page < self.total_pages
        self.has_prev = self.current_page > 1


@runtime_checkable
class DataLoadable(Protocol[T_co]):
    """Protocol for data that can be loaded from GitHub API."""

    async def load_data(self, client: GitHubClient, **kwargs: Any) -> T_co:
        """Load data from the GitHub API."""
        ...

    def get_cache_key(self, **kwargs: Any) -> str:
        """Get cache key for this data."""
        ...


class DataLoader(Generic[T]):
    """Enhanced data loader with caching, pagination, and state management."""

    def __init__(
        self,
        client: GitHubClient,
        error_handler: TUIErrorHandler | None = None,
        cache_ttl: timedelta = timedelta(minutes=5),
        max_cache_size: int = 1000
    ) -> None:
        self.client = client
        self.error_handler = error_handler
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size

        # Cache storage
        self._cache: dict[str, CacheEntry[T]] = {}

        # Loading state tracking
        self._loading_states: dict[str, LoadingState] = {}
        self._loading_tasks: dict[str, asyncio.Task] = {}

        # Pagination state
        self._pagination_states: dict[str, PaginationState] = {}

        # Background refresh tasks
        self._refresh_tasks: set[asyncio.Task] = set()

    def get_loading_state(self, key: str) -> LoadingState:
        """Get current loading state for a key."""
        return self._loading_states.get(key, LoadingState.IDLE)

    def get_pagination_state(self, key: str) -> PaginationState:
        """Get pagination state for a key."""
        if key not in self._pagination_states:
            self._pagination_states[key] = PaginationState()
        return self._pagination_states[key]

    def get_cached_data(self, key: str) -> T | None:
        """Get cached data if available and not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.access()
            else:
                # Remove expired entry
                del self._cache[key]
        return None

    def cache_data(self, key: str, data: T, ttl: timedelta | None = None) -> None:
        """Cache data with optional custom TTL."""
        if ttl is None:
            ttl = self.cache_ttl

        now = datetime.now()
        entry = CacheEntry(
            data=data,
            created_at=now,
            expires_at=now + ttl
        )

        self._cache[key] = entry

        # Cleanup old entries if cache is full
        self._cleanup_cache()

    def _cleanup_cache(self) -> None:
        """Remove expired entries and enforce cache size limit."""
        now = datetime.now()

        # Remove expired entries
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]

        # Enforce size limit by removing least recently accessed items
        if len(self._cache) > self.max_cache_size:
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].last_accessed
            )
            excess_count = len(self._cache) - self.max_cache_size
            for key, _ in sorted_entries[:excess_count]:
                del self._cache[key]

    async def load(
        self,
        key: str,
        loader_func: Callable[..., Any],
        *args: Any,
        force_refresh: bool = False,
        use_cache: bool = True,
        **kwargs: Any
    ) -> LoadResult[T]:
        """Load data with caching and state management."""

        # Check if already loading
        if key in self._loading_tasks and not self._loading_tasks[key].done():
            if not force_refresh:
                # Wait for existing load to complete
                try:
                    await self._loading_tasks[key]
                except Exception:
                    pass  # Error handling is done in the task itself

        # Check cache first (unless force refresh)
        if use_cache and not force_refresh:
            cached_data = self.get_cached_data(key)
            if cached_data is not None:
                return LoadResult(
                    data=cached_data,
                    state=LoadingState.SUCCESS,
                    metadata={'from_cache': True}
                )

        # Start loading
        self._loading_states[key] = LoadingState.REFRESHING if force_refresh else LoadingState.LOADING

        try:
            # Execute loader function
            if asyncio.iscoroutinefunction(loader_func):
                data = await loader_func(*args, **kwargs)
            else:
                data = loader_func(*args, **kwargs)

            # Cache the result
            if use_cache:
                self.cache_data(key, data)

            # Update state
            self._loading_states[key] = LoadingState.SUCCESS

            return LoadResult(
                data=data,
                state=LoadingState.SUCCESS,
                metadata={'from_cache': False}
            )

        except Exception as e:
            logger.error(f"Failed to load data for key '{key}': {e}")

            # Convert to GitHubCLIError if needed
            if not isinstance(e, GitHubCLIError):
                github_error = GitHubCLIError(
                    f"Failed to load {key}",
                    cause=e,
                    context={'key': key}
                )
            else:
                github_error = e

            # Update state
            self._loading_states[key] = LoadingState.ERROR

            # Handle error if handler available
            if self.error_handler:
                self.error_handler.notify_error(github_error)

            return LoadResult(
                state=LoadingState.ERROR,
                error=github_error
            )

        finally:
            # Clean up loading task
            if key in self._loading_tasks:
                del self._loading_tasks[key]

    async def load_paginated(
        self,
        key: str,
        endpoint: str,
        page: int = 1,
        per_page: int = 50,
        params: dict[str, Any] | None = None,
        force_refresh: bool = False
    ) -> LoadResult[list[T]]:
        """Load paginated data from GitHub API."""

        pagination_state = self.get_pagination_state(key)
        pagination_state.current_page = page
        pagination_state.per_page = per_page

        # Prepare API parameters
        api_params = params or {}
        api_params.update({
            'page': page,
            'per_page': per_page
        })

        # Create cache key that includes pagination
        cache_key = f"{key}_page_{page}_per_page_{per_page}"

        async def paginated_loader() -> Any:
            response = await self.client.get(endpoint, params=api_params)

            # Extract data from response
            if hasattr(response, 'data'):
                response_data = response.data
            else:
                response_data = response

            # Update pagination state
            if isinstance(response_data, dict):
                pagination_state.update_from_response(response_data)

            # Extract items
            if isinstance(response_data, dict) and 'items' in response_data:
                items = response_data['items']
            elif isinstance(response_data, list):
                items = response_data
            else:
                items = []

            return items

        result = await self.load(
            cache_key,
            paginated_loader,
            force_refresh=force_refresh
        )

        # Convert LoadResult[T] to LoadResult[list[T]]
        # Note: paginated_loader already returns a list, so we cast the result
        if result.is_success and result.data is not None:
            return LoadResult[list[T]](
                data=result.data,  # type: ignore
                state=result.state,
                error=result.error,
                metadata=result.metadata
            )
        else:
            return LoadResult[list[T]](
                data=None,
                state=result.state,
                error=result.error,
                metadata=result.metadata
            )

    def start_background_refresh(
        self,
        key: str,
        loader_func: Callable[..., Any],
        *args: Any,
        interval: timedelta = timedelta(minutes=5),
        **kwargs: Any
    ) -> None:
        """Start background refresh for data."""

        async def refresh_loop() -> None:
            while True:
                try:
                    await asyncio.sleep(interval.total_seconds())
                    await self.load(key, loader_func, *args, force_refresh=True, **kwargs)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Background refresh failed for {key}: {e}")

        task = asyncio.create_task(refresh_loop())
        self._refresh_tasks.add(task)
        task.add_done_callback(self._refresh_tasks.discard)

    def stop_background_refresh(self, key: str | None = None) -> None:
        """Stop background refresh tasks."""
        if key is None:
            # Stop all background tasks
            for task in self._refresh_tasks:
                task.cancel()
            self._refresh_tasks.clear()
        else:
            # Stop specific tasks (would need task tracking by key for this)
            pass

    def invalidate_cache(self, key: str | None = None) -> None:
        """Invalidate cache entries."""
        if key is None:
            self._cache.clear()
        else:
            # Support pattern matching for cache invalidation
            if '*' in key:
                pattern = key.replace('*', '')
                keys_to_remove = [
                    k for k in self._cache.keys() if k.startswith(pattern)]
                for k in keys_to_remove:
                    del self._cache[k]
            elif key in self._cache:
                del self._cache[key]

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values() if entry.is_expired())
        total_accesses = sum(
            entry.access_count for entry in self._cache.values())

        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'total_accesses': total_accesses,
            'cache_hit_ratio': total_accesses / max(1, total_entries),
            'memory_usage_estimate': total_entries * 1024  # Rough estimate
        }


class StateManager:
    """Centralized state manager for TUI components."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}
        self._subscribers: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock()

    async def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value with thread safety."""
        async with self._lock:
            return self._state.get(key, default)

    async def set_state(self, key: str, value: Any) -> None:
        """Set state value and notify subscribers."""
        async with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value

        # Notify subscribers (outside lock to prevent deadlock)
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key, old_value, value)
                    else:
                        callback(key, old_value, value)
                except Exception as e:
                    logger.error(f"State subscriber error for {key}: {e}")

    def subscribe(self, key: str, callback: Callable) -> None:
        """Subscribe to state changes."""
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable) -> None:
        """Unsubscribe from state changes."""
        if key in self._subscribers:
            try:
                self._subscribers[key].remove(callback)
            except ValueError:
                pass

    async def update_state(self, updates: dict[str, Any]) -> None:
        """Batch update multiple state values."""
        for key, value in updates.items():
            await self.set_state(key, value)


# Factory functions for easy integration
def create_data_loader(
    client: GitHubClient,
    error_handler: TUIErrorHandler | None = None,
    cache_ttl_minutes: int = 5
) -> DataLoader:
    """Create a configured data loader."""
    return DataLoader(
        client=client,
        error_handler=error_handler,
        cache_ttl=timedelta(minutes=cache_ttl_minutes)
    )


def create_state_manager() -> StateManager:
    """Create a new state manager."""
    return StateManager()
