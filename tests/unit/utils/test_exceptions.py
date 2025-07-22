"""
Unit tests for custom exceptions.

Tests custom exception classes including error handling,
message formatting, and exception hierarchy.
"""

import pytest
from unittest.mock import Mock

from github_cli.utils.exceptions import (
    GitHubCLIError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ConfigError,
    ValidationError,
    NotFoundError,
    APIError
)


@pytest.mark.unit
@pytest.mark.utils
class TestGitHubCLIError:
    """Test cases for GitHubCLIError base exception."""

    def test_github_cli_error_creation(self):
        """Test GitHubCLIError creation with message."""
        message = "Something went wrong"
        error = GitHubCLIError(message)
        
        assert str(error) == message
        assert error.message == message
        assert error.cause is None

    def test_github_cli_error_with_cause(self):
        """Test GitHubCLIError creation with cause."""
        message = "High-level error"
        cause = ValueError("Low-level error")
        error = GitHubCLIError(message, cause=cause)
        
        assert str(error) == message
        assert error.message == message
        assert error.cause == cause

    def test_github_cli_error_inheritance(self):
        """Test GitHubCLIError inheritance from Exception."""
        error = GitHubCLIError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GitHubCLIError)

    def test_github_cli_error_repr(self):
        """Test GitHubCLIError string representation."""
        message = "Test error message"
        error = GitHubCLIError(message)
        
        repr_str = repr(error)
        assert "GitHubCLIError" in repr_str
        assert message in repr_str

    def test_github_cli_error_with_details(self):
        """Test GitHubCLIError with additional details."""
        message = "Error with details"
        details = {"code": 404, "url": "https://api.github.com/test"}
        error = GitHubCLIError(message, details=details)
        
        assert error.message == message
        assert error.details == details

    def test_github_cli_error_empty_message(self):
        """Test GitHubCLIError with empty message."""
        error = GitHubCLIError("")
        
        assert str(error) == ""
        assert error.message == ""


@pytest.mark.unit
@pytest.mark.utils
class TestAuthenticationError:
    """Test cases for AuthenticationError."""

    def test_authentication_error_creation(self):
        """Test AuthenticationError creation."""
        message = "Authentication failed"
        error = AuthenticationError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, AuthenticationError)

    def test_authentication_error_with_token_info(self):
        """Test AuthenticationError with token information."""
        message = "Token expired"
        token_info = {"expires_at": "2023-12-01T00:00:00Z", "scopes": ["repo", "user"]}
        error = AuthenticationError(message, token_info=token_info)
        
        assert error.message == message
        assert error.token_info == token_info

    def test_authentication_error_with_cause(self):
        """Test AuthenticationError with underlying cause."""
        message = "OAuth flow failed"
        cause = ConnectionError("Network unreachable")
        error = AuthenticationError(message, cause=cause)
        
        assert error.message == message
        assert error.cause == cause

    def test_authentication_error_inheritance_chain(self):
        """Test AuthenticationError inheritance chain."""
        error = AuthenticationError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, AuthenticationError)


@pytest.mark.unit
@pytest.mark.utils
class TestNetworkError:
    """Test cases for NetworkError."""

    def test_network_error_creation(self):
        """Test NetworkError creation."""
        message = "Network connection failed"
        error = NetworkError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, NetworkError)

    def test_network_error_with_status_code(self):
        """Test NetworkError with HTTP status code."""
        message = "HTTP error"
        status_code = 500
        error = NetworkError(message, status_code=status_code)
        
        assert error.message == message
        assert error.status_code == status_code

    def test_network_error_with_response_data(self):
        """Test NetworkError with response data."""
        message = "API error"
        response_data = {"error": "Internal server error", "code": 500}
        error = NetworkError(message, response_data=response_data)
        
        assert error.message == message
        assert error.response_data == response_data

    def test_network_error_with_url(self):
        """Test NetworkError with URL information."""
        message = "Request failed"
        url = "https://api.github.com/user"
        error = NetworkError(message, url=url)
        
        assert error.message == message
        assert error.url == url


@pytest.mark.unit
@pytest.mark.utils
class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error_creation(self):
        """Test RateLimitError creation."""
        message = "Rate limit exceeded"
        error = RateLimitError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, RateLimitError)

    def test_rate_limit_error_with_reset_time(self):
        """Test RateLimitError with reset time."""
        message = "Rate limit exceeded"
        reset_time = 1701388800  # Unix timestamp
        error = RateLimitError(message, reset_time=reset_time)
        
        assert error.message == message
        assert error.reset_time == reset_time

    def test_rate_limit_error_with_remaining(self):
        """Test RateLimitError with remaining requests."""
        message = "Rate limit exceeded"
        remaining = 0
        limit = 5000
        error = RateLimitError(message, remaining=remaining, limit=limit)
        
        assert error.message == message
        assert error.remaining == remaining
        assert error.limit == limit

    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry after header."""
        message = "Rate limit exceeded"
        retry_after = 3600  # 1 hour
        error = RateLimitError(message, retry_after=retry_after)
        
        assert error.message == message
        assert error.retry_after == retry_after


@pytest.mark.unit
@pytest.mark.utils
class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_configuration_error_creation(self):
        """Test ConfigurationError creation."""
        message = "Invalid configuration"
        error = ConfigurationError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, ConfigurationError)

    def test_configuration_error_with_config_key(self):
        """Test ConfigurationError with configuration key."""
        message = "Missing required configuration"
        config_key = "api.base_url"
        error = ConfigurationError(message, config_key=config_key)
        
        assert error.message == message
        assert error.config_key == config_key

    def test_configuration_error_with_config_file(self):
        """Test ConfigurationError with configuration file."""
        message = "Failed to parse config file"
        config_file = "/home/user/.config/github-cli/config.json"
        error = ConfigurationError(message, config_file=config_file)
        
        assert error.message == message
        assert error.config_file == config_file


@pytest.mark.unit
@pytest.mark.utils
class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        message = "Validation failed"
        error = ValidationError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, ValidationError)

    def test_validation_error_with_field(self):
        """Test ValidationError with field name."""
        message = "Invalid field value"
        field = "repository.name"
        error = ValidationError(message, field=field)
        
        assert error.message == message
        assert error.field == field

    def test_validation_error_with_value(self):
        """Test ValidationError with invalid value."""
        message = "Invalid value"
        value = "invalid@name"
        error = ValidationError(message, value=value)
        
        assert error.message == message
        assert error.value == value

    def test_validation_error_with_constraints(self):
        """Test ValidationError with validation constraints."""
        message = "Value out of range"
        constraints = {"min": 1, "max": 100}
        error = ValidationError(message, constraints=constraints)
        
        assert error.message == message
        assert error.constraints == constraints


@pytest.mark.unit
@pytest.mark.utils
class TestRepositoryError:
    """Test cases for RepositoryError."""

    def test_repository_error_creation(self):
        """Test RepositoryError creation."""
        message = "Repository operation failed"
        error = RepositoryError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, RepositoryError)

    def test_repository_error_with_repo_info(self):
        """Test RepositoryError with repository information."""
        message = "Repository not found"
        owner = "testuser"
        repo = "test-repo"
        error = RepositoryError(message, owner=owner, repo=repo)
        
        assert error.message == message
        assert error.owner == owner
        assert error.repo == repo

    def test_repository_error_with_operation(self):
        """Test RepositoryError with operation type."""
        message = "Operation failed"
        operation = "clone"
        error = RepositoryError(message, operation=operation)
        
        assert error.message == message
        assert error.operation == operation


@pytest.mark.unit
@pytest.mark.utils
class TestAPIError:
    """Test cases for APIError."""

    def test_api_error_creation(self):
        """Test APIError creation."""
        message = "API request failed"
        error = APIError(message)
        
        assert str(error) == message
        assert isinstance(error, GitHubCLIError)
        assert isinstance(error, APIError)

    def test_api_error_with_endpoint(self):
        """Test APIError with API endpoint."""
        message = "Endpoint not found"
        endpoint = "/repos/user/repo"
        error = APIError(message, endpoint=endpoint)
        
        assert error.message == message
        assert error.endpoint == endpoint

    def test_api_error_with_method(self):
        """Test APIError with HTTP method."""
        message = "Method not allowed"
        method = "POST"
        error = APIError(message, method=method)
        
        assert error.message == message
        assert error.method == method

    def test_api_error_with_response(self):
        """Test APIError with response data."""
        message = "API error"
        response = {
            "status_code": 422,
            "data": {"message": "Validation Failed", "errors": []},
            "headers": {"content-type": "application/json"}
        }
        error = APIError(message, response=response)
        
        assert error.message == message
        assert error.response == response


@pytest.mark.unit
@pytest.mark.utils
class TestExceptionChaining:
    """Test cases for exception chaining and cause handling."""

    def test_exception_chaining(self):
        """Test exception chaining with cause."""
        original_error = ValueError("Original error")
        wrapped_error = GitHubCLIError("Wrapped error", cause=original_error)
        
        assert wrapped_error.cause == original_error
        assert str(wrapped_error) == "Wrapped error"

    def test_nested_exception_chaining(self):
        """Test nested exception chaining."""
        level1_error = ConnectionError("Connection failed")
        level2_error = NetworkError("Network error", cause=level1_error)
        level3_error = GitHubCLIError("High-level error", cause=level2_error)
        
        assert level3_error.cause == level2_error
        assert level2_error.cause == level1_error
        assert level1_error.__cause__ is None

    def test_exception_with_multiple_attributes(self):
        """Test exception with multiple custom attributes."""
        error = APIError(
            "Complex API error",
            endpoint="/repos/user/repo",
            method="POST",
            response={"status_code": 422, "data": {"message": "Validation Failed"}},
            cause=ValueError("Invalid input")
        )
        
        assert error.message == "Complex API error"
        assert error.endpoint == "/repos/user/repo"
        assert error.method == "POST"
        assert error.response["status_code"] == 422
        assert isinstance(error.cause, ValueError)


@pytest.mark.unit
@pytest.mark.utils
class TestExceptionFormatting:
    """Test cases for exception message formatting."""

    def test_error_message_formatting(self):
        """Test error message formatting with context."""
        error = AuthenticationError("Token validation failed for user 'testuser'")
        
        assert "testuser" in str(error)
        assert "Token validation failed" in str(error)

    def test_error_with_formatted_details(self):
        """Test error with formatted details."""
        details = {
            "status_code": 401,
            "error_type": "invalid_token",
            "timestamp": "2023-12-01T12:00:00Z"
        }
        error = AuthenticationError("Authentication failed", details=details)
        
        assert error.details["status_code"] == 401
        assert error.details["error_type"] == "invalid_token"

    def test_error_message_with_suggestions(self):
        """Test error message with helpful suggestions."""
        message = (
            "Configuration file not found. "
            "Please run 'github-cli config init' to create a default configuration."
        )
        error = ConfigurationError(message)
        
        assert "github-cli config init" in str(error)
        assert "Configuration file not found" in str(error)
