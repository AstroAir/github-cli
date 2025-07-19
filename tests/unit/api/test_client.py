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

from github_cli.api.client import GitHubClient, APIResponse
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
        assert client.API_BASE == "https://api.github.com"
        assert client._session is None
        assert client._rate_limiter is not None

    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self):
        """Test async context manager functionality."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session
            
            client = GitHubClient(self.mock_authenticator)
            
            # Test entering context
            async with client as ctx_client:
                assert ctx_client == client
                assert client._session == mock_session
            
            # Test exiting context
            mock_session.__aexit__.assert_called_once()

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
            url="https://api.github.com/user"
        )) as mock_request:
            
            result = await client.get("/user")
            
            assert result.status_code == 200
            assert result.data == response_data
            mock_request.assert_called_once_with("GET", "/user", None, None, None, 0)

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
            url="https://api.github.com/user/repos"
        )) as mock_request:
            
            result = await client.post("/user/repos", data=request_data)
            
            assert result.status_code == 201
            assert result.data == response_data
            mock_request.assert_called_once_with("POST", "/user/repos", None, request_data, None, 0)

    @pytest.mark.asyncio
    async def test_request_with_custom_headers(self):
        """Test request with custom headers."""
        client = GitHubClient(self.mock_authenticator)
        
        custom_headers = {"Accept": "application/vnd.github.v3+json"}
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data={},
            headers={"content-type": "application/json"},
            url="https://api.github.com/user"
        )) as mock_request:
            
            await client.get("/user", headers=custom_headers)
            
            mock_request.assert_called_once_with("GET", "/user", None, None, custom_headers, 0)

    @pytest.mark.asyncio
    async def test_request_with_query_params(self):
        """Test request with query parameters."""
        client = GitHubClient(self.mock_authenticator)
        
        params = {"sort": "updated", "per_page": 50}
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            url="https://api.github.com/user/repos"
        )) as mock_request:
            
            await client.get("/user/repos", params=params)
            
            mock_request.assert_called_once_with("GET", "/user/repos", params, None, None, 0)

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test handling of authentication errors."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_make_http_request', side_effect=AuthenticationError("Invalid token")):
            with patch.object(client, 'token_expiration_handler', self.mock_token_handler):
                
                with pytest.raises(AuthenticationError, match="Invalid token"):
                    await client.get("/user")

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test handling of rate limit errors."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_make_http_request', side_effect=RateLimitError("Rate limit exceeded")):
            with patch.object(client, 'token_expiration_handler', self.mock_token_handler):
                
                with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                    await client.get("/user")

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_make_http_request', side_effect=NetworkError("Connection failed")):
            with patch.object(client, 'token_expiration_handler', self.mock_token_handler):
                
                with pytest.raises(NetworkError, match="Connection failed"):
                    await client.get("/user")

    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test request retry mechanism."""
        client = GitHubClient(self.mock_authenticator)
        
        # Mock first call to fail, second to succeed
        response_data = {"login": "testuser"}
        success_response = APIResponse(
            status_code=200,
            data=response_data,
            headers={"content-type": "application/json"},
            url="https://api.github.com/user"
        )
        
        with patch.object(client, '_make_http_request', side_effect=[
            NetworkError("Temporary failure"),
            success_response
        ]):
            with patch.object(client, 'token_expiration_handler', self.mock_token_handler):
                
                result = await client.get("/user")
                assert result.data == response_data

    def test_api_response_creation(self):
        """Test APIResponse object creation and properties."""
        response = APIResponse(
            status_code=200,
            data={"test": "data"},
            headers={"content-type": "application/json"},
            url="https://api.github.com/test"
        )
        
        assert response.status_code == 200
        assert response.data == {"test": "data"}
        assert response.headers["content-type"] == "application/json"
        assert response.url == "https://api.github.com/test"
        assert response.success is True

    def test_api_response_error_status(self):
        """Test APIResponse with error status codes."""
        response = APIResponse(
            status_code=404,
            data={"message": "Not Found"},
            headers={"content-type": "application/json"},
            url="https://api.github.com/nonexistent"
        )
        
        assert response.status_code == 404
        assert response.success is False

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test session cleanup."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            client = GitHubClient(self.mock_authenticator)
            
            async with client:
                pass
            
            mock_session.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_put_request(self):
        """Test PUT request."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data={"updated": True},
            headers={"content-type": "application/json"},
            url="https://api.github.com/test"
        )) as mock_request:
            
            result = await client.put("/test", data={"field": "value"})
            
            assert result.status_code == 200
            mock_request.assert_called_once_with("PUT", "/test", None, {"field": "value"}, None, 0)

    @pytest.mark.asyncio
    async def test_delete_request(self):
        """Test DELETE request."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=204,
            data=None,
            headers={},
            url="https://api.github.com/test"
        )) as mock_request:
            
            result = await client.delete("/test")
            
            assert result.status_code == 204
            mock_request.assert_called_once_with("DELETE", "/test", None, None, None, 0)

    @pytest.mark.asyncio
    async def test_patch_request(self):
        """Test PATCH request."""
        client = GitHubClient(self.mock_authenticator)
        
        with patch.object(client, '_request', return_value=APIResponse(
            status_code=200,
            data={"patched": True},
            headers={"content-type": "application/json"},
            url="https://api.github.com/test"
        )) as mock_request:
            
            result = await client.patch("/test", data={"field": "new_value"})
            
            assert result.status_code == 200
            mock_request.assert_called_once_with("PATCH", "/test", None, {"field": "new_value"}, None, 0)
