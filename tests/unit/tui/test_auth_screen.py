"""
Unit tests for AuthScreen TUI component.

Tests the authentication screen including layout composition,
user interactions, and authentication flow integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Skip TUI tests if textual is not available
pytest.importorskip("textual")

from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager
from github_cli.ui.tui.screens.auth import AuthScreen
from github_cli.utils.exceptions import AuthenticationError
from dataclasses import dataclass

# Define AuthResult for tests since it's expected but not implemented
@dataclass
class AuthResult:
    """Authentication result for testing."""
    success: bool
    token: str = None
    error: str = None


@pytest.mark.unit
@pytest.mark.tui
class TestAuthScreen:
    """Test cases for AuthScreen class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_authenticator = Mock(spec=Authenticator)
        self.mock_authenticator.config = self.mock_config
        
        # Mock authenticator methods
        self.mock_authenticator._request_device_code = AsyncMock()
        self.mock_authenticator._poll_for_token = AsyncMock()
        self.mock_authenticator.fetch_user_info = AsyncMock()
        self.mock_authenticator.token_manager = Mock()
        
        self.mock_layout_manager = Mock(spec=ResponsiveLayoutManager)

    def test_auth_screen_initialization(self):
        """Test AuthScreen initialization."""
        screen = AuthScreen(self.mock_authenticator)
        
        assert screen.authenticator == self.mock_authenticator
        assert screen._auth_task is None
        assert screen.layout_manager is None
        assert screen.responsive_layout is None
        assert screen.error_handler is None
        assert screen.progress_tracker is None
        assert screen.device_code is None
        assert screen.verification_uri is None

    def test_auth_screen_initialization_with_layout_manager(self):
        """Test AuthScreen initialization with layout manager."""
        screen = AuthScreen(self.mock_authenticator, self.mock_layout_manager)
        
        assert screen.layout_manager == self.mock_layout_manager

    def test_auth_screen_bindings(self):
        """Test AuthScreen key bindings."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Check that bindings are defined
        assert hasattr(screen, 'BINDINGS')
        assert len(screen.BINDINGS) > 0
        
        # Check for expected bindings
        binding_keys = [binding.key for binding in screen.BINDINGS]
        assert "escape" in binding_keys
        assert "ctrl+c" in binding_keys
        assert "r" in binding_keys
        assert "h" in binding_keys

    @pytest.mark.asyncio
    async def test_start_auth_flow_success(self):
        """Test successful authentication flow."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock device code data
        device_code_data = {
            "device_code": "device123",
            "user_code": "USER123",
            "verification_uri": "https://github.com/login/device",
            "expires_in": 900,
            "interval": 5
        }
        
        # Mock token data
        token_data = {
            "access_token": "gho_token123",
            "token_type": "bearer"
        }
        
        # Mock user info
        user_info = {
            "login": "testuser",
            "id": 123,
            "name": "Test User",
            "email": "test@example.com"
        }
        
        # Setup mocks
        self.mock_authenticator._request_device_code.return_value = device_code_data
        self.mock_authenticator._poll_for_token.return_value = token_data
        self.mock_authenticator.fetch_user_info.return_value = user_info
        self.mock_authenticator.token_manager.save_token.return_value = "token_id"
        
        with patch.object(screen, '_update_device_code_display') as mock_update, \
             patch.object(screen, '_open_browser_for_auth') as mock_browser, \
             patch.object(screen, 'dismiss') as mock_dismiss, \
             patch('asyncio.sleep'):
            
            result = await screen._run_auth_flow()
            
            # Verify the flow
            self.mock_authenticator._request_device_code.assert_called_once()
            self.mock_authenticator._poll_for_token.assert_called_once()
            self.mock_authenticator.fetch_user_info.assert_called_once()
            mock_update.assert_called_once()
            mock_browser.assert_called_once()
            
            # Verify result
            assert isinstance(result, AuthResult)
            assert result.success is True
            assert result.user_info == user_info

    @pytest.mark.asyncio
    async def test_start_auth_flow_device_code_failure(self):
        """Test authentication flow with device code failure."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock device code failure
        self.mock_authenticator._request_device_code.side_effect = AuthenticationError("Device code failed")
        
        with pytest.raises(AuthenticationError, match="Device code failed"):
            await screen._run_auth_flow()

    @pytest.mark.asyncio
    async def test_start_auth_flow_token_polling_failure(self):
        """Test authentication flow with token polling failure."""
        screen = AuthScreen(self.mock_authenticator)
        
        device_code_data = {
            "device_code": "device123",
            "user_code": "USER123",
            "verification_uri": "https://github.com/login/device"
        }
        
        self.mock_authenticator._request_device_code.return_value = device_code_data
        self.mock_authenticator._poll_for_token.side_effect = AuthenticationError("Polling failed")
        
        with patch.object(screen, '_update_device_code_display'), \
             patch.object(screen, '_open_browser_for_auth'):
            
            with pytest.raises(AuthenticationError, match="Polling failed"):
                await screen._run_auth_flow()

    @pytest.mark.asyncio
    async def test_request_device_code_success(self):
        """Test successful device code request."""
        screen = AuthScreen(self.mock_authenticator)
        
        device_code_data = {
            "device_code": "device123",
            "user_code": "USER123",
            "verification_uri": "https://github.com/login/device"
        }
        
        self.mock_authenticator._request_device_code.return_value = device_code_data
        
        result = await screen._request_device_code()
        
        assert result == device_code_data
        self.mock_authenticator._request_device_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_device_code_failure(self):
        """Test device code request failure."""
        screen = AuthScreen(self.mock_authenticator)
        
        self.mock_authenticator._request_device_code.return_value = None
        
        with pytest.raises(AuthenticationError, match="Failed to request device code"):
            await screen._request_device_code()

    @pytest.mark.asyncio
    async def test_poll_for_token_success(self):
        """Test successful token polling."""
        screen = AuthScreen(self.mock_authenticator)
        
        device_flow_data = {
            "device_code": "device123",
            "interval": 5
        }
        
        token_data = {
            "access_token": "gho_token123",
            "token_type": "bearer"
        }
        
        self.mock_authenticator._poll_for_token.return_value = token_data
        
        result = await screen._poll_for_token(device_flow_data)
        
        assert result == token_data
        self.mock_authenticator._poll_for_token.assert_called_once_with("device123", 5)

    @pytest.mark.asyncio
    async def test_poll_for_token_failure(self):
        """Test token polling failure."""
        screen = AuthScreen(self.mock_authenticator)
        
        device_flow_data = {
            "device_code": "device123",
            "interval": 5
        }
        
        self.mock_authenticator._poll_for_token.return_value = None
        
        with pytest.raises(AuthenticationError, match="Failed to obtain access token"):
            await screen._poll_for_token(device_flow_data)

    @pytest.mark.asyncio
    async def test_validate_token_success(self):
        """Test successful token validation."""
        screen = AuthScreen(self.mock_authenticator)
        
        token_data = {
            "access_token": "gho_token123"
        }
        
        user_info = Mock()
        user_info.login = "testuser"
        user_info.id = 123
        user_info.name = "Test User"
        user_info.email = "test@example.com"
        
        self.mock_authenticator.token_manager.save_token.return_value = "token_id"
        self.mock_authenticator.fetch_user_info.return_value = user_info
        
        result = await screen._validate_token(token_data)
        
        assert result["login"] == "testuser"
        assert result["id"] == 123
        self.mock_authenticator.token_manager.save_token.assert_called_once_with(token_data)
        self.mock_authenticator.fetch_user_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_token_no_access_token(self):
        """Test token validation with no access token."""
        screen = AuthScreen(self.mock_authenticator)
        
        token_data = {}  # No access_token
        
        with pytest.raises(AuthenticationError, match="No access token received"):
            await screen._validate_token(token_data)

    def test_update_device_code_display_compact(self):
        """Test device code display update for compact layout."""
        screen = AuthScreen(self.mock_authenticator)
        screen.device_code = "USER123"
        screen.verification_uri = "https://github.com/login/device"
        
        # Mock compact layout config
        mock_config = Mock()
        mock_config.layout_type = "compact"
        screen.current_config = mock_config
        
        # Mock widgets
        mock_device_code_widget = Mock()
        mock_verification_widget = Mock()
        
        with patch.object(screen, 'query_one', side_effect=[mock_device_code_widget, mock_verification_widget]):
            screen._update_device_code_display()
            
            mock_device_code_widget.update.assert_called_once_with("Code: USER123")

    def test_update_device_code_display_standard(self):
        """Test device code display update for standard layout."""
        screen = AuthScreen(self.mock_authenticator)
        screen.device_code = "USER123"
        screen.verification_uri = "https://github.com/login/device"
        
        # Mock standard layout config
        mock_config = Mock()
        mock_config.layout_type = "standard"
        screen.current_config = mock_config
        
        # Mock widgets
        mock_device_code_widget = Mock()
        mock_verification_widget = Mock()
        
        with patch.object(screen, 'query_one', side_effect=[mock_device_code_widget, mock_verification_widget]):
            screen._update_device_code_display()
            
            mock_device_code_widget.update.assert_called_once_with("USER123")
            mock_verification_widget.update.assert_called_once_with("URL: https://github.com/login/device")

    def test_cancel_auth_button(self):
        """Test cancel authentication button."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock running auth task
        mock_task = Mock()
        mock_task.done.return_value = False
        screen._auth_task = mock_task
        
        with patch.object(screen, 'dismiss') as mock_dismiss:
            screen.cancel_auth()
            
            mock_task.cancel.assert_called_once()
            mock_dismiss.assert_called_once()
            
            # Check the result passed to dismiss
            call_args = mock_dismiss.call_args[0][0]
            assert isinstance(call_args, AuthResult)
            assert call_args.success is False

    @pytest.mark.asyncio
    async def test_retry_auth_button(self):
        """Test retry authentication button."""
        screen = AuthScreen(self.mock_authenticator)
        
        with patch.object(screen, '_start_auth_flow') as mock_start:
            await screen.retry_auth()
            
            mock_start.assert_called_once()

    def test_show_help_button(self):
        """Test show help button."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen.show_help()
        
        mock_app.notify.assert_called_once()
        call_args = mock_app.notify.call_args
        assert "Authentication Help" in call_args[0][0]

    def test_action_retry(self):
        """Test retry action from keyboard shortcut."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock retry button
        mock_button = Mock()
        
        with patch.object(screen, 'query_one', return_value=mock_button):
            screen.action_retry()
            
            mock_button.press.assert_called_once()

    def test_action_help(self):
        """Test help action from keyboard shortcut."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock help button
        mock_button = Mock()
        
        with patch.object(screen, 'query_one', return_value=mock_button):
            screen.action_help()
            
            mock_button.press.assert_called_once()

    def test_action_help_fallback(self):
        """Test help action fallback when button doesn't exist."""
        screen = AuthScreen(self.mock_authenticator)
        
        with patch.object(screen, 'query_one', side_effect=Exception("Widget not found")), \
             patch.object(screen, 'show_help') as mock_show_help:
            
            screen.action_help()
            
            mock_show_help.assert_called_once()

    def test_device_code_expired_callback(self):
        """Test device code expiration callback."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock progress tracker
        mock_progress_tracker = Mock()
        screen.progress_tracker = mock_progress_tracker
        
        with patch.object(screen, '_show_retry_option') as mock_show_retry:
            screen._on_device_code_expired()
            
            mock_progress_tracker.show_error.assert_called_once()
            mock_show_retry.assert_called_once()

    def test_layout_change_callback(self):
        """Test layout change callback."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock progress tracker
        mock_progress_tracker = Mock()
        screen.progress_tracker = mock_progress_tracker
        
        old_config = Mock()
        old_config.layout_type = "compact"
        
        new_config = Mock()
        new_config.layout_type = "standard"
        
        screen._on_layout_change(old_config, new_config)
        
        assert screen.current_config == new_config
        mock_progress_tracker.update_layout_config.assert_called_once_with(new_config)

    def test_unmount_cleanup(self):
        """Test cleanup on unmount."""
        screen = AuthScreen(self.mock_authenticator)
        
        # Mock running auth task
        mock_task = Mock()
        mock_task.done.return_value = False
        screen._auth_task = mock_task
        
        # Mock progress tracker
        mock_progress_tracker = Mock()
        screen.progress_tracker = mock_progress_tracker
        
        # Mock responsive layout
        mock_responsive_layout = Mock()
        mock_responsive_layout.cleanup = Mock()
        screen.responsive_layout = mock_responsive_layout
        
        screen.on_unmount()
        
        mock_task.cancel.assert_called_once()
        mock_progress_tracker.cleanup.assert_called_once()
        mock_responsive_layout.cleanup.assert_called_once()
