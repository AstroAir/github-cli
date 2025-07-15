from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, TypeVar, TYPE_CHECKING
from urllib.parse import urljoin

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from github_cli.utils.exceptions import APIError, NetworkError, NotFoundError

if TYPE_CHECKING:
    from github_cli.auth.authenticator import Authenticator


T = TypeVar('T')


class RateLimitInfo(BaseModel):
    """Rate limit information from GitHub API."""
    remaining: int = Field(default=0, description="Remaining API calls")
    reset_time: int = Field(
        default=0, description="Reset time as Unix timestamp")
    limit: int = Field(default=5000, description="Total rate limit")


class APIResponse(BaseModel):
    """Enhanced API response wrapper."""
    data: Any = Field(description="Response data")
    status_code: int = Field(description="HTTP status code")
    rate_limit: RateLimitInfo = Field(default_factory=RateLimitInfo)
    headers: dict[str, str] = Field(default_factory=dict)


class GitHubClient:
    """Modern GitHub API client with enhanced error handling and performance."""

    API_BASE: str = "https://api.github.com/"
    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    def __init__(self, authenticator: Authenticator) -> None:
        self.authenticator = authenticator
        self._rate_limit_info = RateLimitInfo()
        self._session: aiohttp.ClientSession | None = None

        # Configure structured logging
        logger.configure(
            handlers=[
                {
                    "sink": "logs/github_cli.log",
                    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
                    "rotation": "10 MB",
                    "retention": "1 week",
                    "level": "DEBUG"
                }
            ]
        )

    @property
    def rate_limit_remaining(self) -> int:
        """Get remaining API calls."""
        return self._rate_limit_info.remaining

    @property
    def rate_limit_reset(self) -> int:
        """Get rate limit reset time."""
        return self._rate_limit_info.reset_time

    @asynccontextmanager
    async def _get_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """Get or create an aiohttp session with optimal settings."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT)
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": "GitHub-CLI/0.1.0"}
            )
            logger.debug("Created new aiohttp session with optimized settings")

        try:
            yield self._session
        except Exception:
            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None
            raise

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed aiohttp session")

    def _update_rate_limit(self, headers: dict[str, str]) -> None:
        """Update rate limit information from response headers."""
        try:
            if "X-RateLimit-Remaining" in headers:
                self._rate_limit_info.remaining = int(
                    headers["X-RateLimit-Remaining"])

            if "X-RateLimit-Reset" in headers:
                self._rate_limit_info.reset_time = int(
                    headers["X-RateLimit-Reset"])

            if "X-RateLimit-Limit" in headers:
                self._rate_limit_info.limit = int(headers["X-RateLimit-Limit"])

            logger.debug(
                f"Rate limit updated: {self._rate_limit_info.remaining}/{self._rate_limit_info.limit} remaining"
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        retry_count: int = 0
    ) -> APIResponse:
        """Make a request to the GitHub API with enhanced error handling and retries."""
        url = urljoin(self.API_BASE, endpoint.lstrip("/"))

        # Prepare headers
        request_headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        if headers:
            request_headers.update(headers)

        # Add authorization if available
        if self.authenticator.token:
            request_headers["Authorization"] = f"Bearer {self.authenticator.token}"

        logger.debug(f"Making {method} request to {url}")

        try:
            async with self._get_session() as session:
                async with session.request(
                    method,
                    url,
                    params=params,
                    json=data,
                    headers=request_headers
                ) as response:
                    # Update rate limit info
                    self._update_rate_limit(dict(response.headers))

                    # Handle different response statuses
                    response_data = await self._handle_response(response, endpoint)

                    return APIResponse(
                        data=response_data,
                        status_code=response.status,
                        rate_limit=self._rate_limit_info,
                        headers=dict(response.headers)
                    )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Network error on {method} {url}: {e}")

            # Implement exponential backoff retry
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)
                logger.info(
                    f"Retrying request after {delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})")
                await asyncio.sleep(delay)
                return await self._request(method, endpoint, params, data, headers, retry_count + 1)

            # Convert to our custom exception
            if isinstance(e, asyncio.TimeoutError):
                raise NetworkError(
                    f"Request to {endpoint} timed out after {self.DEFAULT_TIMEOUT}s") from e
            else:
                raise NetworkError(f"Network error: {e}") from e

        except Exception as e:
            logger.exception(f"Unexpected error during request to {endpoint}")
            raise APIError(f"Unexpected error: {e}") from e

    async def _handle_response(self, response: aiohttp.ClientResponse, endpoint: str) -> Any:
        """Handle different response types and status codes."""
        try:
            # Handle successful responses
            if 200 <= response.status < 300:
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()

            # Handle client errors
            elif response.status == 404:
                logger.warning(f"Resource not found: {endpoint}")
                raise NotFoundError(f"Resource not found: {endpoint}")

            elif response.status == 401:
                logger.error(
                    "Authentication failed - invalid or expired token")
                raise APIError("Authentication failed", status_code=401)

            elif response.status == 403:
                error_data = await self._safe_json_parse(response)
                if "rate limit" in str(error_data).lower():
                    logger.warning("Rate limit exceeded")
                    raise APIError("Rate limit exceeded", status_code=403)
                else:
                    logger.error(f"Forbidden access to {endpoint}")
                    raise APIError("Forbidden access", status_code=403)

            elif response.status == 422:
                error_data = await self._safe_json_parse(response)
                logger.error(f"Validation error: {error_data}")
                raise APIError(
                    f"Validation error: {error_data}", status_code=422)

            # Handle server errors
            elif response.status >= 500:
                logger.error(f"Server error {response.status} for {endpoint}")
                raise APIError(
                    f"Server error ({response.status})", status_code=response.status)

            # Handle other client errors
            else:
                error_data = await self._safe_json_parse(response)
                message = str(error_data.get("message", "Unknown API error")) if isinstance(
                    error_data, dict) else "Unknown API error"
                logger.error(f"API error {response.status}: {message}")
                raise APIError(
                    f"API error ({response.status}): {message}", status_code=response.status)

        except ValidationError as e:
            logger.error(f"Response validation error: {e}")
            raise APIError(f"Invalid response format: {e}") from e

    async def _safe_json_parse(self, response: aiohttp.ClientResponse) -> Any:
        """Safely parse JSON response with fallback."""
        try:
            return await response.json()
        except Exception:
            logger.debug("Failed to parse response as JSON, returning text")
            return await response.text()

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> APIResponse:
        """Make a GET request to the GitHub API."""
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> APIResponse:
        """Make a POST request to the GitHub API."""
        return await self._request("POST", endpoint, data=data)

    async def patch(self, endpoint: str, data: dict[str, Any]) -> APIResponse:
        """Make a PATCH request to the GitHub API."""
        return await self._request("PATCH", endpoint, data=data)

    async def delete(self, endpoint: str) -> APIResponse:
        """Make a DELETE request to the GitHub API."""
        return await self._request("DELETE", endpoint)

    async def put(
        self,
        endpoint: str,
        data: dict[str, Any],
        headers: dict[str, str] | None = None
    ) -> APIResponse:
        """Make a PUT request to the GitHub API."""
        return await self._request("PUT", endpoint, data=data, headers=headers)

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None
    ) -> APIResponse:
        """
        Make a request to the GitHub API with any HTTP method.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (starting with /)
            params: Query parameters
            data: Request body data
            headers: Additional headers

        Returns:
            Enhanced API response with metadata
        """
        return await self._request(method, endpoint, params=params, data=data, headers=headers)

    async def paginated_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_pages: int = 10,
        per_page: int = 100
    ) -> list[Any]:
        """
        Make optimized paginated requests using Python 3.12 performance improvements.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (starting with /)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            max_pages: Maximum number of pages to fetch
            per_page: Items per page (max 100 for GitHub API)

        Returns:
            Combined list of items from all pages
        """
        if params is None:
            params = {}

        # Optimize pagination parameters
        params = params.copy()  # Avoid mutating input
        params.setdefault("page", 1)
        params.setdefault("per_page", min(per_page, 100)
                          )  # GitHub API max is 100

        results: list[Any] = []
        current_page = params["page"]

        logger.debug(
            f"Starting paginated request for {endpoint} (max_pages={max_pages}, per_page={params['per_page']})")

        # Use Python 3.12 performance improvements for iteration
        for page_num in range(current_page, current_page + max_pages):
            params["page"] = page_num

            try:
                response = await self._request(method, endpoint, params=params, data=data, headers=headers)
                page_data = response.data

                # Handle paginated responses
                if isinstance(page_data, list):
                    if not page_data:  # Empty page means we're done
                        logger.debug(
                            f"Reached empty page {page_num}, stopping pagination")
                        break

                    results.extend(page_data)
                    logger.debug(
                        f"Fetched page {page_num} with {len(page_data)} items")

                    # If we got fewer results than requested, we're done
                    if len(page_data) < params["per_page"]:
                        logger.debug(
                            f"Partial page received ({len(page_data)} < {params['per_page']}), stopping pagination")
                        break
                else:
                    # Not a paginated response
                    logger.debug("Non-paginated response received")
                    return [page_data]

            except APIError as e:
                if e.status_code == 404 and page_num > 1:
                    # Reached end of results
                    logger.debug(
                        f"404 on page {page_num}, assuming end of results")
                    break
                raise

        logger.info(
            f"Paginated request completed: {len(results)} total items from {page_num - current_page + 1} pages")
        return results

    async def __aenter__(self) -> GitHubClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
