from __future__ import annotations

from typing import Any

from loguru import logger


class GitHubCLIError(Exception):
    """Enhanced base exception for all GitHub CLI errors with structured logging."""

    def __init__(self, message: str, *, cause: Exception | None = None, context: dict[str, Any] | None = None, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self._message = message
        self.cause = cause
        self.context = context or {}
        self.details = details or {}

        # Log the error creation (disabled to avoid format string issues)
        # logger.error(
        #     "Exception created: {}: {}".format(self.__class__.__name__, message),
        #     extra={
        #         "exception_type": self.__class__.__name__,
        #         "cause": str(cause) if cause else None,
        #         "context": self.context
        #     }
        # )

    @property
    def message(self) -> str:
        """Get the error message."""
        return self._message

    def __str__(self) -> str:
        # Return just the message for test compatibility
        return self._message

    def add_context(self, key: str, value: Any) -> GitHubCLIError:
        """Add contextual information to the exception."""
        self.context[key] = value
        return self

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get contextual information from the exception."""
        return self.context.get(key, default)


class AuthenticationError(GitHubCLIError):
    """Enhanced authentication error with detailed context."""

    def __init__(
        self,
        message: str,
        *,
        auth_type: str | None = None,
        status_code: int | None = None,
        token_info: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None
    ) -> None:
        context: dict[str, Any] = {}
        if auth_type:
            context["auth_type"] = auth_type
        if status_code is not None:
            context["status_code"] = status_code
        if details:
            context.update(details)

        super().__init__(message, cause=cause, context=context)
        self.token_info = token_info or {}
        self.details = details or {}


class NetworkError(GitHubCLIError):
    """Enhanced network error with retry and timeout information."""

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        timeout: float | None = None,
        retry_count: int = 0,
        status_code: int | None = None,
        response_data: dict | None = None,
        cause: Exception | None = None
    ) -> None:
        context: dict[str, Any] = {
            "retry_count": retry_count
        }
        if url:
            context["url"] = url
        if timeout is not None:
            context["timeout"] = timeout
        if status_code is not None:
            context["status_code"] = status_code
        if response_data is not None:
            context["response_data"] = response_data

        super().__init__(message, cause=cause, context=context)

        # Add attributes expected by tests
        self.url = url
        self.status_code = status_code
        self.response_data = response_data


class APIError(GitHubCLIError):
    """Enhanced API error with comprehensive GitHub API context."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 0,
        endpoint: str | None = None,
        method: str | None = None,
        response_headers: dict[str, str] | None = None,
        response: dict[str, Any] | None = None,
        rate_limit_remaining: int | None = None,
        cause: Exception | None = None
    ) -> None:
        context: dict[str, Any] = {
            "status_code": status_code
        }
        if endpoint:
            context["endpoint"] = endpoint
        if method:
            context["method"] = method
        if response_headers:
            context["response_headers"] = response_headers
        if rate_limit_remaining is not None:
            context["rate_limit_remaining"] = rate_limit_remaining

        super().__init__(message, cause=cause, context=context)
        self.status_code = status_code
        self.endpoint = endpoint
        self.method = method
        self.response = response or {}

    @property
    def is_rate_limited(self) -> bool:
        """Check if this error is due to rate limiting."""
        return self.status_code == 403 and self.get_context("rate_limit_remaining", 1) == 0

    @property
    def is_authentication_error(self) -> bool:
        """Check if this error is due to authentication issues."""
        return self.status_code == 401

    @property
    def is_permission_error(self) -> bool:
        """Check if this error is due to insufficient permissions."""
        return self.status_code == 403 and not self.is_rate_limited


class NotFoundError(APIError):
    """Enhanced not found error with resource information."""

    def __init__(
        self,
        message: str,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        endpoint: str | None = None,
        cause: Exception | None = None
    ) -> None:
        context = {}
        if resource_type:
            context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id

        super().__init__(
            message,
            status_code=404,
            endpoint=endpoint,
            cause=cause
        )
        self.context.update(context)


class ConfigError(GitHubCLIError):
    """Enhanced configuration error with file and key information."""

    def __init__(
        self,
        message: str,
        *,
        config_file: str | None = None,
        config_key: str | None = None,
        cause: Exception | None = None
    ) -> None:
        context = {}
        if config_file:
            context["config_file"] = config_file
        if config_key:
            context["config_key"] = config_key

        super().__init__(message, cause=cause, context=context)

        # Add attributes expected by tests
        self.config_file = config_file
        self.config_key = config_key


class PluginError(GitHubCLIError):
    """Enhanced plugin error with plugin information."""

    def __init__(
        self,
        message: str,
        *,
        plugin_name: str | None = None,
        plugin_version: str | None = None,
        cause: Exception | None = None
    ) -> None:
        context = {}
        if plugin_name:
            context["plugin_name"] = plugin_name
        if plugin_version:
            context["plugin_version"] = plugin_version

        super().__init__(message, cause=cause, context=context)


class ValidationError(GitHubCLIError):
    """Enhanced validation error with field and value information."""

    def __init__(
        self,
        message: str,
        *,
        field_name: str | None = None,
        field_value: Any = None,
        validation_rule: str | None = None,
        field: str | None = None,  # Alias for field_name
        value: Any = None,  # Alias for field_value
        constraints: str | None = None,  # Alias for validation_rule
        cause: Exception | None = None
    ) -> None:
        # Use aliases if provided
        actual_field_name = field or field_name
        actual_field_value = value if value is not None else field_value
        actual_validation_rule = constraints or validation_rule

        context: dict[str, Any] = {}
        if actual_field_name:
            context["field_name"] = actual_field_name
        if actual_field_value is not None:
            # Convert to string for logging
            context["field_value"] = str(actual_field_value)
        if actual_validation_rule:
            context["validation_rule"] = actual_validation_rule

        super().__init__(message, cause=cause, context=context)

        # Add attributes expected by tests
        self.field = actual_field_name
        self.value = actual_field_value
        self.constraints = actual_validation_rule


class RateLimitError(APIError):
    """Specific error for GitHub API rate limiting with reset information."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        *,
        reset_time: int | None = None,
        remaining: int = 0,
        limit: int = 5000,
        retry_after: int | None = None,
        endpoint: str | None = None,
        cause: Exception | None = None
    ) -> None:
        context = {
            "remaining": remaining,
            "limit": limit
        }
        if reset_time:
            context["reset_time"] = reset_time
        if retry_after is not None:
            context["retry_after"] = retry_after

        super().__init__(
            message,
            status_code=403,
            endpoint=endpoint,
            rate_limit_remaining=remaining,
            cause=cause
        )
        self.context.update(context)

        # Add attributes expected by tests
        self.retry_after = retry_after

    @property
    def reset_time(self) -> int | None:
        """Get the time when the rate limit resets."""
        value = self.get_context("reset_time")
        return int(value) if value is not None else None

    @property
    def remaining(self) -> int:
        """Get the number of remaining API calls."""
        return int(self.get_context("remaining", 0))

    @property
    def limit(self) -> int:
        """Get the total API rate limit."""
        return int(self.get_context("limit", 5000))


class TimeoutError(NetworkError):
    """Specific error for request timeouts."""

    def __init__(
        self,
        message: str = "Request timed out",
        *,
        timeout_duration: float | None = None,
        url: str | None = None,
        cause: Exception | None = None
    ) -> None:
        context = {}
        if timeout_duration:
            context["timeout_duration"] = timeout_duration

        super().__init__(
            message,
            url=url,
            timeout=timeout_duration,
            cause=cause
        )
        self.context.update(context)


class TokenExpiredError(AuthenticationError):
    """Specific error for expired authentication tokens."""

    def __init__(
        self,
        message: str = "Authentication token has expired",
        *,
        operation: str | None = None,
        expiry_time: int | None = None,
        cause: Exception | None = None
    ) -> None:
        context: dict[str, Any] = {}
        if operation:
            context["operation"] = operation
        if expiry_time is not None:
            context["expiry_time"] = expiry_time

        super().__init__(
            message,
            auth_type="token_expiration",
            status_code=401,
            cause=cause
        )
        self.context.update(context)


class RepositoryError(GitHubCLIError):
    """Enhanced repository error with repository information."""

    def __init__(
        self,
        message: str,
        *,
        owner: str | None = None,
        repo: str | None = None,
        operation: str | None = None,
        cause: Exception | None = None
    ) -> None:
        context: dict[str, Any] = {}
        if owner:
            context["owner"] = owner
        if repo:
            context["repo"] = repo
        if operation:
            context["operation"] = operation

        super().__init__(message, cause=cause, context=context)
        self.owner = owner
        self.repo = repo
