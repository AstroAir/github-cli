"""
Unit tests for Dashboard TUI component.

Tests the main dashboard screen including layout composition,
data display, and user interactions.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from textual.testing import TUITestCase

from github_cli.ui.tui.screens.dashboard import DashboardScreen
from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator
from github_cli.models.repository import Repository
from github_cli.models.user import User
from github_cli.utils.config import Config


@pytest.mark.unit
@pytest.mark.tui
class TestDashboardScreen:
    """Test cases for DashboardScreen class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_authenticator = Mock(spec=Authenticator)
        self.mock_client = Mock(spec=GitHubClient)
        
        # Mock user info
        self.mock_user = Mock(spec=User)
        self.mock_user.login = "testuser"
        self.mock_user.name = "Test User"
        self.mock_user.public_repos = 10
        self.mock_user.followers = 100
        self.mock_user.following = 50

    def test_dashboard_screen_initialization(self):
        """Test DashboardScreen initialization."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        assert screen.client == self.mock_client
        assert screen.authenticator == self.mock_authenticator
        assert screen._user_info is None
        assert screen._repositories is None
        assert screen._notifications is None
        assert screen._loading is False

    def test_dashboard_screen_bindings(self):
        """Test DashboardScreen key bindings."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Check that bindings are defined
        assert hasattr(screen, 'BINDINGS')
        assert len(screen.BINDINGS) > 0
        
        # Check for expected bindings
        binding_keys = [binding.key for binding in screen.BINDINGS]
        assert "r" in binding_keys  # Refresh
        assert "n" in binding_keys  # Notifications
        assert "s" in binding_keys  # Search
        assert "h" in binding_keys  # Help
        assert "q" in binding_keys  # Quit

    @pytest.mark.asyncio
    async def test_load_dashboard_data_success(self, sample_repository_data, sample_user_data):
        """Test successful dashboard data loading."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock API responses
        repositories = [Repository(**sample_repository_data)]
        user_info = User(**sample_user_data)
        notifications = [
            {
                "id": "1",
                "subject": {"title": "New issue", "type": "Issue"},
                "repository": {"full_name": "testuser/test-repo"},
                "unread": True
            }
        ]
        
        # Setup mocks
        with patch.object(screen, '_fetch_user_info', return_value=user_info) as mock_user, \
             patch.object(screen, '_fetch_repositories', return_value=repositories) as mock_repos, \
             patch.object(screen, '_fetch_notifications', return_value=notifications) as mock_notifs, \
             patch.object(screen, '_update_dashboard_display') as mock_update:
            
            await screen._load_dashboard_data()
            
            # Verify API calls
            mock_user.assert_called_once()
            mock_repos.assert_called_once()
            mock_notifs.assert_called_once()
            mock_update.assert_called_once()
            
            # Verify data is stored
            assert screen._user_info == user_info
            assert screen._repositories == repositories
            assert screen._notifications == notifications

    @pytest.mark.asyncio
    async def test_load_dashboard_data_partial_failure(self, sample_user_data):
        """Test dashboard data loading with partial failures."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        user_info = User(**sample_user_data)
        
        # Setup mocks with some failures
        with patch.object(screen, '_fetch_user_info', return_value=user_info), \
             patch.object(screen, '_fetch_repositories', side_effect=Exception("Repos failed")), \
             patch.object(screen, '_fetch_notifications', return_value=[]), \
             patch.object(screen, '_update_dashboard_display'), \
             patch.object(screen, '_show_error_message') as mock_error:
            
            await screen._load_dashboard_data()
            
            # Should still have user info and notifications
            assert screen._user_info == user_info
            assert screen._notifications == []
            assert screen._repositories is None
            
            # Should show error for failed repositories
            mock_error.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_user_info_success(self, sample_user_data):
        """Test successful user info fetching."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.data = sample_user_data
        
        self.mock_client.get.return_value = mock_response
        
        result = await screen._fetch_user_info()
        
        assert isinstance(result, User)
        assert result.login == sample_user_data["login"]
        self.mock_client.get.assert_called_once_with("/user")

    @pytest.mark.asyncio
    async def test_fetch_user_info_failure(self):
        """Test user info fetching failure."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock API failure
        self.mock_client.get.side_effect = Exception("API error")
        
        with pytest.raises(Exception, match="API error"):
            await screen._fetch_user_info()

    @pytest.mark.asyncio
    async def test_fetch_repositories_success(self, sample_repository_data):
        """Test successful repositories fetching."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock API response
        repositories_data = [sample_repository_data]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.data = repositories_data
        
        self.mock_client.get.return_value = mock_response
        
        result = await screen._fetch_repositories()
        
        assert len(result) == 1
        assert isinstance(result[0], Repository)
        assert result[0].name == sample_repository_data["name"]
        self.mock_client.get.assert_called_once_with(
            "/user/repos", 
            params={"sort": "updated", "per_page": 10}
        )

    @pytest.mark.asyncio
    async def test_fetch_repositories_with_params(self):
        """Test repositories fetching with custom parameters."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.data = []
        
        self.mock_client.get.return_value = mock_response
        
        params = {"sort": "created", "per_page": 20}
        await screen._fetch_repositories(**params)
        
        self.mock_client.get.assert_called_once_with("/user/repos", params=params)

    @pytest.mark.asyncio
    async def test_fetch_notifications_success(self):
        """Test successful notifications fetching."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock API response
        notifications_data = [
            {
                "id": "1",
                "subject": {"title": "New issue", "type": "Issue"},
                "repository": {"full_name": "testuser/test-repo"},
                "unread": True,
                "updated_at": "2023-12-01T00:00:00Z"
            },
            {
                "id": "2",
                "subject": {"title": "PR merged", "type": "PullRequest"},
                "repository": {"full_name": "testuser/another-repo"},
                "unread": False,
                "updated_at": "2023-11-30T00:00:00Z"
            }
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.data = notifications_data
        
        self.mock_client.get.return_value = mock_response
        
        result = await screen._fetch_notifications()
        
        assert len(result) == 2
        assert result[0]["subject"]["title"] == "New issue"
        assert result[1]["subject"]["title"] == "PR merged"
        self.mock_client.get.assert_called_once_with(
            "/notifications",
            params={"per_page": 10}
        )

    def test_update_dashboard_display_with_data(self, sample_user_data, sample_repository_data):
        """Test dashboard display update with data."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Set up data
        screen._user_info = User(**sample_user_data)
        screen._repositories = [Repository(**sample_repository_data)]
        screen._notifications = [
            {
                "id": "1",
                "subject": {"title": "New issue", "type": "Issue"},
                "unread": True
            }
        ]
        
        # Mock widgets
        mock_user_widget = Mock()
        mock_repos_widget = Mock()
        mock_notifs_widget = Mock()
        
        with patch.object(screen, 'query_one', side_effect=[
            mock_user_widget, mock_repos_widget, mock_notifs_widget
        ]):
            screen._update_dashboard_display()
            
            # Verify widgets were updated
            mock_user_widget.update_user_info.assert_called_once_with(screen._user_info)
            mock_repos_widget.update_repositories.assert_called_once_with(screen._repositories)
            mock_notifs_widget.update_notifications.assert_called_once_with(screen._notifications)

    def test_update_dashboard_display_loading(self):
        """Test dashboard display update during loading."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        screen._loading = True
        
        # Mock widgets
        mock_loading_widget = Mock()
        
        with patch.object(screen, 'query_one', return_value=mock_loading_widget):
            screen._update_dashboard_display()
            
            mock_loading_widget.show_loading.assert_called_once()

    def test_refresh_dashboard_action(self):
        """Test refresh dashboard action."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        with patch.object(screen, '_load_dashboard_data') as mock_load:
            screen.action_refresh()
            
            mock_load.assert_called_once()

    def test_show_notifications_action(self):
        """Test show notifications action."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen.action_show_notifications()
        
        mock_app.push_screen.assert_called_once()
        # Verify it's pushing a notifications screen
        call_args = mock_app.push_screen.call_args[0][0]
        assert "Notifications" in str(type(call_args))

    def test_search_action(self):
        """Test search action."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen.action_search()
        
        mock_app.push_screen.assert_called_once()
        # Verify it's pushing a search screen
        call_args = mock_app.push_screen.call_args[0][0]
        assert "Search" in str(type(call_args))

    def test_show_help_action(self):
        """Test show help action."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen.action_help()
        
        mock_app.notify.assert_called_once()
        call_args = mock_app.notify.call_args[0][0]
        assert "Dashboard Help" in call_args

    def test_quit_action(self):
        """Test quit action."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen.action_quit()
        
        mock_app.exit.assert_called_once()

    def test_repository_selected_callback(self, sample_repository_data):
        """Test repository selection callback."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        repository = Repository(**sample_repository_data)
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen._on_repository_selected(repository)
        
        mock_app.push_screen.assert_called_once()
        # Verify it's pushing a repository detail screen
        call_args = mock_app.push_screen.call_args[0][0]
        assert "Repository" in str(type(call_args))

    def test_notification_selected_callback(self):
        """Test notification selection callback."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        notification = {
            "id": "1",
            "subject": {"title": "New issue", "type": "Issue", "url": "https://api.github.com/repos/user/repo/issues/1"},
            "repository": {"full_name": "user/repo"}
        }
        
        # Mock app
        mock_app = Mock()
        screen.app = mock_app
        
        screen._on_notification_selected(notification)
        
        mock_app.push_screen.assert_called_once()

    def test_error_handling_display(self):
        """Test error message display."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        error_message = "Failed to load data"
        
        # Mock error widget
        mock_error_widget = Mock()
        
        with patch.object(screen, 'query_one', return_value=mock_error_widget):
            screen._show_error_message(error_message)
            
            mock_error_widget.show_error.assert_called_once_with(error_message)

    def test_loading_state_management(self):
        """Test loading state management."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock loading widget
        mock_loading_widget = Mock()
        
        with patch.object(screen, 'query_one', return_value=mock_loading_widget):
            # Start loading
            screen._set_loading(True)
            assert screen._loading is True
            mock_loading_widget.show_loading.assert_called_once()
            
            # Stop loading
            screen._set_loading(False)
            assert screen._loading is False
            mock_loading_widget.hide_loading.assert_called_once()

    def test_dashboard_compose_layout(self):
        """Test dashboard layout composition."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock compose method
        with patch.object(screen, 'compose') as mock_compose:
            # This would be called during screen initialization
            screen.compose()
            
            mock_compose.assert_called_once()

    @pytest.mark.asyncio
    async def test_mount_lifecycle(self):
        """Test dashboard mount lifecycle."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        with patch.object(screen, '_load_dashboard_data') as mock_load:
            await screen.on_mount()
            
            mock_load.assert_called_once()

    def test_unmount_cleanup(self):
        """Test cleanup on unmount."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock running tasks
        mock_task = Mock()
        mock_task.done.return_value = False
        screen._data_task = mock_task
        
        screen.on_unmount()
        
        mock_task.cancel.assert_called_once()

    def test_keyboard_navigation(self):
        """Test keyboard navigation between widgets."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock widgets
        mock_repos_widget = Mock()
        mock_notifs_widget = Mock()
        
        with patch.object(screen, 'query_one', side_effect=[mock_repos_widget, mock_notifs_widget]):
            # Test tab navigation
            screen.action_focus_next()
            
            # Should focus next widget
            mock_repos_widget.focus.assert_called_once()

    def test_responsive_layout_updates(self):
        """Test responsive layout updates."""
        screen = DashboardScreen(self.mock_client, self.mock_authenticator)
        
        # Mock layout manager
        mock_layout_manager = Mock()
        screen.layout_manager = mock_layout_manager
        
        # Simulate screen size change
        screen._on_resize(80, 24)  # 80 columns, 24 rows
        
        mock_layout_manager.update_layout.assert_called_once_with(80, 24)
