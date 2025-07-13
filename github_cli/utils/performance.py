from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, ParamSpec, TypeVar

from loguru import logger

P = ParamSpec('P')
T = TypeVar('T')


@dataclass(slots=True, frozen=True)
class PerformanceMetrics:
    """Performance metrics with Python 3.11+ slots optimization."""
    operation: str
    duration: float
    timestamp: float = field(default_factory=time.time)
    memory_usage: int | None = None
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class PerformanceMonitor:
    """Enhanced performance monitoring with Python 3.12 optimizations."""
    
    def __init__(self) -> None:
        self._metrics: list[PerformanceMetrics] = []
        self._start_times: dict[str, float] = {}
        
        # Configure eager task factory for Python 3.12 performance gains
        try:
            # Use eager task factory if available (Python 3.12+)
            loop = asyncio.get_running_loop()
            if hasattr(asyncio, 'eager_task_factory'):
                loop.set_task_factory(asyncio.eager_task_factory())
                logger.debug("Enabled eager task factory for performance optimization")
        except RuntimeError:
            # No running loop yet, will be set when loop starts
            pass
    
    @asynccontextmanager
    async def measure(self, operation: str) -> AsyncGenerator[None, None]:
        """Async context manager for measuring operation performance."""
        start_time = time.perf_counter()
        logger.debug(f"Starting performance measurement for: {operation}")
        
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            metrics = PerformanceMetrics(
                operation=operation,
                duration=duration
            )
            self._metrics.append(metrics)
            logger.debug(f"Operation '{operation}' completed in {duration:.4f}s")
    
    def start_timing(self, operation: str) -> None:
        """Start timing an operation."""
        self._start_times[operation] = time.perf_counter()
        logger.debug(f"Started timing: {operation}")
    
    def end_timing(self, operation: str, **kwargs) -> PerformanceMetrics:
        """End timing an operation and record metrics."""
        if operation not in self._start_times:
            raise ValueError(f"No start time recorded for operation: {operation}")
        
        duration = time.perf_counter() - self._start_times.pop(operation)
        metrics = PerformanceMetrics(
            operation=operation,
            duration=duration,
            **kwargs
        )
        self._metrics.append(metrics)
        logger.debug(f"Completed timing for '{operation}': {duration:.4f}s")
        return metrics
    
    def get_metrics(self, operation: str | None = None) -> list[PerformanceMetrics]:
        """Get performance metrics, optionally filtered by operation."""
        if operation is None:
            return self._metrics.copy()
        return [m for m in self._metrics if m.operation == operation]
    
    def get_average_duration(self, operation: str) -> float:
        """Get average duration for a specific operation."""
        metrics = self.get_metrics(operation)
        if not metrics:
            return 0.0
        return sum(m.duration for m in metrics) / len(metrics)
    
    def clear_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()
        logger.debug("Cleared all performance metrics")


def async_performance_monitor(operation: str | None = None):
    """Decorator for monitoring async function performance."""
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.perf_counter()
            logger.debug(f"Starting async operation: {op_name}")
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                logger.debug(f"Async operation '{op_name}' completed in {duration:.4f}s")
        
        return wrapper
    return decorator


def performance_monitor(operation: str | None = None):
    """Decorator for monitoring sync function performance."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        op_name = operation or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.perf_counter()
            logger.debug(f"Starting sync operation: {op_name}")
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                logger.debug(f"Sync operation '{op_name}' completed in {duration:.4f}s")
        
        return wrapper
    return decorator


class AsyncCache:
    """High-performance async cache with Python 3.12 optimizations."""
    
    def __init__(self, maxsize: int = 128, ttl: float = 300.0) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}
        self._maxsize = maxsize
        self._ttl = ttl
        self._hits = 0
        self._misses = 0
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > self._ttl
    
    def _evict_expired(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if not self._is_expired(timestamp):
                self._hits += 1
                return value
            else:
                del self._cache[key]
        
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with automatic eviction."""
        # Evict expired entries first
        self._evict_expired()
        
        # Evict oldest entry if at max size
        if len(self._cache) >= self._maxsize and key not in self._cache:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = (value, time.time())
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": self.hit_ratio,
            "size": len(self._cache),
            "maxsize": self._maxsize
        }
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


def cached_async(
    cache: AsyncCache | None = None,
    key_func: Callable[..., str] | None = None,
    ttl: float = 300.0
):
    """Decorator for caching async function results."""
    if cache is None:
        cache = AsyncCache(ttl=ttl)
    
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__qualname__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__qualname__}")
                return cached_result
            
            # Compute result and cache it
            logger.debug(f"Cache miss for {func.__qualname__}, computing result")
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_global_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor


async def setup_performance_optimizations() -> None:
    """Setup Python 3.12 performance optimizations."""
    try:
        loop = asyncio.get_running_loop()
        
        # Enable eager task factory if available (Python 3.12+)
        if hasattr(asyncio, 'eager_task_factory'):
            loop.set_task_factory(asyncio.eager_task_factory())
            logger.info("Enabled eager task factory for 2-5x performance improvement")
        
        # Optimize event loop settings
        if hasattr(loop, 'set_debug'):
            loop.set_debug(False)  # Disable debug mode for performance
        
        logger.info("Performance optimizations configured successfully")
        
    except Exception as e:
        logger.warning(f"Failed to setup some performance optimizations: {e}")
