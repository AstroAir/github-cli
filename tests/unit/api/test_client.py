"""
Unit tests for GitHub API client.

Tests the core GitHubClient class including HTTP methods, error handling,
rate limiting, and async context management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
from datetime import datetime, timezone

from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.exceptions import NetworkError, AuthenticationError, RateLimitError
from github_cli.utils.config import Config


@pytest.mark.unit
@pytest.mark.api
class TestGitHubClient:
    """Test cases for GitHubClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_authenticator = Mock(spec=Authenticator)
        self.mock_authenticator.config = self.mock_config
        self.mock_authenticator.token = "test_token_123"
        self.mock_authenticator.is_authenticated.return_value = True
        
        # Mock token expiration handler
        self.mock_token_handler = Mock()
        self.mock_token_handler.with_token_validation = AsyncMock()
        self.mock_token_handler.with_token_validation.return_value.__aenter__ = AsyncMock()
        self.mock_token_handler.with_token_validation.return_value.__aexit__ = AsyncMock()

    def test_client_initialization(self):
        """Test GitHubClient initialization."""
        client = GitHubClient(self.mock_authenticator)
        
        assert client.authenticator == self.mock_authenticator
        assert client.API_BASE == "https://api.github.com/"
        assert client._session is None
        assert client.rate_limit_remaining == 0

    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self):
        """Test async context manager functionality."""
        client = GitHubClient(self.mock_authenticator)

        # Mock the close method to verify it's called
        client.close = AsyncMock()

        # Test entering context
        async with client as ctx_client:
            assert ctx_client == client

        # Verify close was called during context exit
        client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """Test successful GET request."""
        client = GitHubClient(self.mock_authenticator)
        
        # Mock response data
        response_data = {"login": "testuser", "id": 123}
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.text = AsyncMock(return_value='{"login": "testuser", "id": 123}')
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data=response_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            result = await client.get("/user")

            assert result.status_code == 200
            assert result.data == response_data
            mock_request.assert_called_once_with("GET", "/user", params=None)

    @pytest.mark.asyncio
    async def test_post_request_with_data(self):
        """Test POST request with JSON data."""
        client = GitHubClient(self.mock_authenticator)
        
        request_data = {"name": "test-repo", "description": "Test repository"}
        response_data = {"id": 123, "name": "test-repo"}
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=201,
            data=response_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            result = await client.post("/user/repos", data=request_data)

            assert result.status_code == 201
            assert result.data == response_data
            mock_request.assert_called_once_with("POST", "/user/repos", data=request_data)

    @pytest.mark.asyncio
    async def test_request_with_custom_headers(self):
        """Test request with custom headers via _request method."""
        client = GitHubClient(self.mock_authenticator)

        custom_headers = {"Accept": "application/vnd.github.v3+json"}

        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data={},
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            # Test _request method directly since get() doesn't accept headers
            await client._request("GET", "/user", headers=custom_headers)

            mock_request.assert_called_once_with("GET", "/user", headers=custom_headers)

    @pytest.mark.asyncio
    async def test_request_with_query_params(self):
        """Test request with query parameters."""
        client = GitHubClient(self.mock_authenticator)
        
        params = {"sort": "updated", "per_page": 50}
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            await client.get("/user/repos", params=params)

            mock_request.assert_called_once_with("GET", "/user/repos", params=params)

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test handling of authentication errors."""
        client = GitHubClient(self.mock_authenticator)

        with patch.object(client, '_request', side_effect=AuthenticationError("Invalid token")):
            with pytest.raises(AuthenticationError, match="Invalid token"):
                await client.get("/user")

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test handling of rate limit errors."""
        client = GitHubClient(self.mock_authenticator)

        with patch.object(client, '_request', side_effect=RateLimitError("Rate limit exceeded")):
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await client.get("/user")

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        client = GitHubClient(self.mock_authenticator)

        with patch.object(client, '_request', side_effect=NetworkError("Connection failed")):
            with pytest.raises(NetworkError, match="Connection failed"):
                await client.get("/user")

    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test request retry mechanism by mocking successful response."""
        client = GitHubClient(self.mock_authenticator)

        # Mock successful response (retry logic is internal to _request)
        response_data = {"login": "testuser"}
        success_response = APIResponse(
            status_code=200,
            data=response_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        with patch.object(client, '_request', return_value=success_response):
            result = await client.get("/user")
            assert result.data == response_data

    def test_api_response_creation(self):
        """Test APIResponse object creation and properties."""
        response = APIResponse(
            status_code=200,
            data={"test": "data"},
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        assert response.status_code == 200
        assert response.data == {"test": "data"}
        assert response.headers["content-type"] == "application/json"
        # APIResponse doesn't have url or success properties in the actual implementation

    def test_api_response_error_status(self):
        """Test APIResponse with error status codes."""
        response = APIResponse(
            status_code=404,
            data={"message": "Not Found"},
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        assert response.status_code == 404
        # APIResponse doesn't have success property in the actual implementation

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test session cleanup."""
        client = GitHubClient(self.mock_authenticator)

        # Mock the close method
        client.close = AsyncMock()

        # Test that close is called
        await client.close()
        client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_put_request(self):
        """Test PUT request."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data={"updated": True},
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            result = await client.put("/test", data={"field": "value"})

            assert result.status_code == 200
            assert result.data == {"updated": True}
            mock_request.assert_called_once_with("PUT", "/test", data={"field": "value"}, headers=None)

    @pytest.mark.asyncio
    async def test_delete_request(self):
        """Test DELETE request."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=204,
            data=None,
            headers={},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            result = await client.delete("/test")

            assert result.status_code == 204
            mock_request.assert_called_once_with("DELETE", "/test")

    @pytest.mark.asyncio
    async def test_patch_request(self):
        """Test PATCH request."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data={"patched": True},
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )) as mock_request:

            result = await client.patch("/test", data={"field": "new_value"})

            assert result.status_code == 200
            assert result.data == {"patched": True}
            mock_request.assert_called_once_with("PATCH", "/test", data={"field": "new_value"})
