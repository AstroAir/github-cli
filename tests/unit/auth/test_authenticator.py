"""
Unit tests for GitHub authenticator.

Tests the core Authenticator class including OAuth device flow,
token management, and authentication state.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from github_cli.auth.authenticator import Authenticator, AuthenticationConfig
from github_cli.auth.token_manager import TokenManager
from github_cli.auth.sso_handler import SSOHandler
from github_cli.utils.config import Config
from github_cli.utils.exceptions import AuthenticationError
from github_cli.models.user import User


@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticator:
    """Test cases for Authenticator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_config.get.return_value = "test_value"
        
        # Mock token manager
        self.mock_token_manager = Mock(spec=TokenManager)
        self.mock_token_manager.get_token.return_value = "test_token_123"
        self.mock_token_manager.save_token.return_value = "test_token_123"
        self.mock_token_manager.delete_token.return_value = True
        
        # Mock SSO handler
        self.mock_sso_handler = Mock(spec=SSOHandler)

    def test_authenticator_initialization(self):
        """Test Authenticator initialization."""
        authenticator = Authenticator(self.mock_config)
        
        assert authenticator.config == self.mock_config
        assert isinstance(authenticator._auth_config, AuthenticationConfig)
        assert authenticator._token is None
        assert authenticator._user_info is None

    def test_token_manager_property(self):
        """Test token_manager property lazy loading."""
        authenticator = Authenticator(self.mock_config)

        with patch('github_cli.auth.token_manager.TokenManager') as mock_tm_class:
            mock_tm_class.return_value = self.mock_token_manager

            # First access should create the token manager
            token_manager = authenticator.token_manager
            assert token_manager == self.mock_token_manager
            mock_tm_class.assert_called_once_with(self.mock_config)

            # Second access should return the same instance
            token_manager2 = authenticator.token_manager
            assert token_manager2 == self.mock_token_manager
            assert mock_tm_class.call_count == 1

    def test_sso_handler_property(self):
        """Test sso_handler property lazy loading."""
        authenticator = Authenticator(self.mock_config)

        with patch('github_cli.auth.sso_handler.SSOHandler') as mock_sso_class:
            mock_sso_class.return_value = self.mock_sso_handler

            # First access should create the SSO handler
            sso_handler = authenticator.sso_handler
            assert sso_handler == self.mock_sso_handler
            mock_sso_class.assert_called_once_with(self.mock_config)

    def test_token_property_with_cached_token(self):
        """Test token property when token is cached."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = "cached_token_456"
        
        assert authenticator.token == "cached_token_456"

    def test_token_property_loads_from_manager(self):
        """Test token property loads from token manager when not cached."""
        authenticator = Authenticator(self.mock_config)
        
        with patch.object(authenticator, 'token_manager', self.mock_token_manager):
            token = authenticator.token
            assert token == "test_token_123"
            assert authenticator._token == "test_token_123"
            self.mock_token_manager.get_token.assert_called_once()

    def test_is_authenticated_with_token(self):
        """Test is_authenticated returns True when token exists."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = "test_token"
        
        assert authenticator.is_authenticated() is True

    def test_is_authenticated_without_token(self):
        """Test is_authenticated returns False when no token."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        with patch.object(authenticator, 'token_manager', self.mock_token_manager):
            self.mock_token_manager.get_token.return_value = None
            
            assert authenticator.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_login_interactive_already_authenticated(self):
        """Test login_interactive when already authenticated."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = "existing_token"
        
        with patch('builtins.print') as mock_print:
            await authenticator.login_interactive()
            # Should not attempt login
            mock_print.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_interactive_success(self):
        """Test successful interactive login."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        # Mock device code response
        device_code_data = {
            "device_code": "device123",
            "user_code": "USER123",
            "verification_uri": "https://github.com/login/device",
            "expires_in": 900,
            "interval": 5
        }
        
        # Mock token response
        token_data = {
            "access_token": "gho_token123",
            "token_type": "bearer",
            "scope": "repo,user"
        }
        
        # Mock user info
        user_info = User(
            id=123,
            login="testuser",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/testuser",
            url="https://api.github.com/users/testuser"
        )
        
        with patch.object(authenticator, '_request_device_code', return_value=device_code_data) as mock_request, \
             patch.object(authenticator, '_display_auth_instructions') as mock_display, \
             patch.object(authenticator, '_poll_for_token', return_value=token_data) as mock_poll, \
             patch.object(authenticator, 'token_manager', self.mock_token_manager), \
             patch.object(authenticator, 'fetch_user_info', return_value=user_info) as mock_fetch, \
             patch('builtins.print') as mock_print:
            
            await authenticator.login_interactive()
            
            # Verify the flow
            mock_request.assert_called_once()
            mock_display.assert_called_once_with(device_code_data)
            mock_poll.assert_called_once_with("device123", 5)
            self.mock_token_manager.save_token.assert_called_once_with(token_data)
            mock_fetch.assert_called_once()
            
            # Verify token is set
            assert authenticator._token == "test_token_123"

    @pytest.mark.asyncio
    async def test_login_interactive_with_sso(self):
        """Test interactive login with SSO configuration."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        device_code_data = {"device_code": "device123", "interval": 5}
        token_data = {"access_token": "gho_token123"}
        
        with patch.object(authenticator, '_request_device_code', return_value=device_code_data), \
             patch.object(authenticator, '_display_auth_instructions'), \
             patch.object(authenticator, '_poll_for_token', return_value=token_data), \
             patch.object(authenticator, 'token_manager', self.mock_token_manager), \
             patch.object(authenticator, '_configure_sso') as mock_sso, \
             patch.object(authenticator, 'fetch_user_info', return_value=None), \
             patch('builtins.print'):
            
            await authenticator.login_interactive(sso="test-org")
            
            mock_sso.assert_called_once_with("test-org")

    @pytest.mark.asyncio
    async def test_login_interactive_device_code_failure(self):
        """Test login failure when device code request fails."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        with patch.object(authenticator, '_request_device_code', return_value=None):
            
            with pytest.raises(AuthenticationError, match="Failed to start authentication flow"):
                await authenticator.login_interactive()

    @pytest.mark.asyncio
    async def test_login_interactive_token_polling_failure(self):
        """Test login failure when token polling fails."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        device_code_data = {"device_code": "device123", "interval": 5}
        
        with patch.object(authenticator, '_request_device_code', return_value=device_code_data), \
             patch.object(authenticator, '_display_auth_instructions'), \
             patch.object(authenticator, '_poll_for_token', return_value=None):
            
            with pytest.raises(AuthenticationError, match="Authentication was not completed"):
                await authenticator.login_interactive()

    @pytest.mark.asyncio
    async def test_login_interactive_unexpected_error(self):
        """Test login handles unexpected errors."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        with patch.object(authenticator, '_request_device_code', side_effect=Exception("Network error")):
            
            with pytest.raises(AuthenticationError, match="Authentication failed due to an unexpected error"):
                await authenticator.login_interactive()

    @pytest.mark.asyncio
    async def test_logout_success(self):
        """Test successful logout."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = "test_token"
        authenticator._user_info = Mock()
        
        with patch.object(authenticator, 'token_manager', self.mock_token_manager):
            self.mock_token_manager.delete_token.return_value = True
            
            result = await authenticator.logout()
            
            assert result is True
            assert authenticator._token is None
            assert authenticator._user_info is None
            self.mock_token_manager.delete_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_not_authenticated(self):
        """Test logout when not authenticated."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        result = await authenticator.logout()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_user_info_success(self):
        """Test successful user info fetching."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = "test_token"
        
        user_data = {
            "id": 123,
            "login": "testuser",
            "node_id": "MDQ6VXNlcjEyMw==",
            "type": "User",
            "site_admin": False,
            "avatar_url": "https://avatars.githubusercontent.com/u/123",
            "html_url": "https://github.com/testuser",
            "url": "https://api.github.com/users/testuser"
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=user_data)
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            user_info = await authenticator.fetch_user_info()
            
            assert isinstance(user_info, User)
            assert user_info.login == "testuser"
            assert user_info.id == 123
            assert authenticator._user_info == user_info

    @pytest.mark.asyncio
    async def test_fetch_user_info_not_authenticated(self):
        """Test user info fetching when not authenticated."""
        authenticator = Authenticator(self.mock_config)
        authenticator._token = None
        
        with pytest.raises(AuthenticationError, match="Not authenticated"):
            await authenticator.fetch_user_info()

    def test_authentication_config_defaults(self):
        """Test AuthenticationConfig default values."""
        config = AuthenticationConfig()
        
        assert config.client_id == "Iv1.b507a08c87ecfe98"
        assert config.device_code_url == "https://github.com/login/device/code"
        assert config.token_url == "https://github.com/login/oauth/access_token"
        assert config.default_scopes == "repo,user,gist"
        assert config.poll_interval == 5
        assert config.timeout == 900
