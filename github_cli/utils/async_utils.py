"""
Async utilities for GitHub CLI with enhanced concurrency and performance optimization.
"""

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union, AsyncGenerator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from loguru import logger

T = TypeVar('T')


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Result of an async task with metadata."""
    task_id: str
    result: Any = None
    error: Exception | None = None
    duration: float = 0.0
    completed_at: float = field(default_factory=time.time)

    @property
    def is_success(self) -> bool:
        """Check if the task completed successfully."""
        return self.error is None

    @property
    def is_failure(self) -> bool:
        """Check if the task failed."""
        return self.error is not None


class AsyncTaskManager:
    """Enhanced async task manager with concurrency control and performance monitoring."""

    def __init__(self, max_concurrent_tasks: int = 10, timeout: float = 30.0):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._completed_tasks: List[TaskResult] = []

    async def run_tasks(
        self,
        tasks: Dict[str, Awaitable[T]],
        fail_fast: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, TaskResult]:
        """
        Run multiple async tasks with concurrency control and progress tracking.

        Args:
            tasks: Dictionary mapping task IDs to awaitables
            fail_fast: If True, cancel remaining tasks on first failure
            progress_callback: Optional callback for progress updates (task_id, progress_percent)

        Returns:
            Dictionary mapping task IDs to TaskResult objects
        """
        if not tasks:
            return {}

        logger.info(
            f"Starting {len(tasks)} async tasks with max concurrency: {self.max_concurrent_tasks}")

        results: Dict[str, TaskResult] = {}
        completed_count = 0
        total_tasks = len(tasks)

        async def run_single_task(task_id: str, coro: Awaitable[T]) -> TaskResult:
            """Run a single task with error handling and timing."""
            async with self._semaphore:
                start_time = time.time()
                try:
                    logger.debug(f"Starting task: {task_id}")
                    result = await asyncio.wait_for(coro, timeout=self.timeout)
                    duration = time.time() - start_time

                    task_result = TaskResult(
                        task_id=task_id,
                        result=result,
                        duration=duration
                    )

                    logger.debug(
                        f"Task {task_id} completed successfully in {duration:.2f}s")
                    return task_result

                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    error = asyncio.TimeoutError(
                        f"Task {task_id} timed out after {self.timeout}s")
                    logger.warning(
                        f"Task {task_id} timed out after {duration:.2f}s")

                    return TaskResult(
                        task_id=task_id,
                        error=error,
                        duration=duration
                    )

                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        f"Task {task_id} failed after {duration:.2f}s: {e}")

                    return TaskResult(
                        task_id=task_id,
                        error=e,
                        duration=duration
                    )

        # Create tasks
        async_tasks = {
            task_id: asyncio.create_task(run_single_task(task_id, coro))
            for task_id, coro in tasks.items()
        }

        self._active_tasks.update(async_tasks)

        try:
            # Wait for tasks to complete
            for future in asyncio.as_completed(async_tasks.values()):
                task_result = await future
                results[task_result.task_id] = task_result
                self._completed_tasks.append(task_result)

                completed_count += 1
                progress = (completed_count / total_tasks) * 100

                # Call progress callback if provided
                if progress_callback:
                    try:
                        progress_callback(task_result.task_id, progress)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")

                # Handle fail_fast mode
                if fail_fast and task_result.is_failure:
                    logger.warning(
                        f"Task {task_result.task_id} failed, cancelling remaining tasks")
                    # Cancel remaining tasks
                    for tid, task in async_tasks.items():
                        if tid != task_result.task_id and not task.done():
                            task.cancel()
                    break

            # Wait for any cancelled tasks to finish
            await asyncio.gather(*async_tasks.values(), return_exceptions=True)

        finally:
            # Clean up active tasks tracking
            for task_id in async_tasks:
                self._active_tasks.pop(task_id, None)

        # Log summary
        successful_tasks = sum(1 for r in results.values() if r.is_success)
        failed_tasks = len(results) - successful_tasks
        total_duration = sum(r.duration for r in results.values())

        logger.info(
            f"Task batch completed: {successful_tasks} successful, {failed_tasks} failed, "
            f"total duration: {total_duration:.2f}s"
        )

        return results

    async def cancel_all_tasks(self) -> int:
        """Cancel all active tasks."""
        cancelled_count = 0
        for task_id, task in list(self._active_tasks.items()):
            if not task.done():
                task.cancel()
                cancelled_count += 1
                logger.debug(f"Cancelled task: {task_id}")

        if cancelled_count > 0:
            logger.info(f"Cancelled {cancelled_count} active tasks")

        return cancelled_count

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self._completed_tasks:
            return {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "average_duration": 0.0,
                "total_duration": 0.0
            }

        successful_tasks = [t for t in self._completed_tasks if t.is_success]
        failed_tasks = [t for t in self._completed_tasks if t.is_failure]

        total_duration = sum(t.duration for t in self._completed_tasks)
        average_duration = total_duration / len(self._completed_tasks)

        return {
            "total_tasks": len(self._completed_tasks),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate_percent": round((len(successful_tasks) / len(self._completed_tasks)) * 100, 2),
            "average_duration": round(average_duration, 3),
            "total_duration": round(total_duration, 3),
            "active_tasks": len(self._active_tasks)
        }


class RateLimitedExecutor:
    """Executor that respects rate limits for API calls."""

    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 5):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self._tokens = float(burst_size)
        self._last_update = time.time()
        self._lock = asyncio.Lock()

    async def execute(self, coro: Awaitable[T]) -> T:
        """Execute a coroutine while respecting rate limits."""
        await self._acquire_token()
        return await coro

    async def _acquire_token(self) -> None:
        """Acquire a token from the rate limiter."""
        async with self._lock:
            now = time.time()
            time_passed = now - self._last_update

            # Add tokens based on time passed
            tokens_to_add = time_passed * self.requests_per_second
            self._tokens = min(self.burst_size, self._tokens + tokens_to_add)
            self._last_update = now

            if self._tokens < 1:
                # Wait until we have a token
                wait_time = (1 - self._tokens) / self.requests_per_second
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._tokens = 0
            else:
                self._tokens -= 1


@asynccontextmanager
async def timeout_context(timeout: float, operation_name: str = "operation") -> AsyncGenerator[None, None]:
    """Context manager for timeout handling with logging."""
    start_time = time.time()
    try:
        async with asyncio.timeout(timeout):
            yield
        duration = time.time() - start_time
        logger.debug(f"{operation_name} completed in {duration:.2f}s")
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        logger.warning(f"{operation_name} timed out after {duration:.2f}s")
        raise


async def gather_with_concurrency(
    *awaitables: Awaitable[T],
    max_concurrency: int = 10,
    return_exceptions: bool = False
) -> List[Union[T, BaseException]]:
    """
    Gather awaitables with concurrency control.

    Similar to asyncio.gather() but limits the number of concurrent operations.
    """
    if not awaitables:
        return []

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_with_semaphore(aw: Awaitable[T]) -> T:
        async with semaphore:
            return await aw

    limited_awaitables = [_run_with_semaphore(aw) for aw in awaitables]
    return await asyncio.gather(*limited_awaitables, return_exceptions=return_exceptions)


async def retry_with_backoff(
    coro_func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> T:
    """
    Retry a coroutine function with exponential backoff.

    Args:
        coro_func: Function that returns an awaitable
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry on

    Returns:
        Result of the successful operation

    Raises:
        The last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"Operation failed after {max_retries} retries: {e}")
                raise e

            delay = base_delay * (backoff_factor ** attempt)
            logger.warning(
                f"Operation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected end of retry loop")


class AsyncCache:
    """Simple async-safe cache with TTL support."""

    def __init__(self, default_ttl: float = 300.0):  # 5 minutes default
        self.default_ttl = default_ttl
        # key -> (value, expires_at)
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache."""
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if time.time() < expires_at:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]
            return default

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value in the cache with optional TTL."""
        expires_at = time.time() + (ttl or self.default_ttl)
        async with self._lock:
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        async with self._lock:
            return self._cache.pop(key, None) is not None

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        now = time.time()
        expired_keys = []

        async with self._lock:
            for key, (value, expires_at) in self._cache.items():
                if now >= expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        return len(expired_keys)


# Utility functions for common async patterns

async def batch_process(
    items: List[T],
    processor: Callable[[T], Awaitable[Any]],
    batch_size: int = 10,
    delay_between_batches: float = 0.1
) -> List[Any]:
    """Process items in batches with delay between batches."""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[processor(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)

        # Add delay between batches (except for the last batch)
        if i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)

    return results


async def wait_for_condition(
    condition: Callable[[], Awaitable[bool]],
    timeout: float = 30.0,
    poll_interval: float = 0.5
) -> bool:
    """Wait for a condition to become true with timeout."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        if await condition():
            return True
        await asyncio.sleep(poll_interval)

    return False
