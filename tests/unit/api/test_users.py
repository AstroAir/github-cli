"""
Unit tests for GitHub Users API module.

Tests the users API functions for managing GitHub users and their data.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api import users
from github_cli.api.client import GitHubClient, APIResponse
from github_cli.models.user import User
from github_cli.models.repository import Repository
from github_cli.utils.exceptions import APIError, ValidationError


@pytest.mark.unit
@pytest.mark.api
class TestUsersAPI:
    """Test cases for users API functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, sample_user_data):
        """Test getting a user by username."""
        mock_response = sample_user_data
        self.mock_client.get = AsyncMock(return_value=mock_response)

        mock_user = Mock(spec=User)
        with patch.object(User, 'from_json', return_value=mock_user):
            result = await users.get_user(self.mock_client, "testuser")

            assert result == mock_user
            self.mock_client.get.assert_called_once_with("/users/testuser")

    @pytest.mark.asyncio
    async def test_get_authenticated_user(self, sample_user_data):
        """Test getting the authenticated user."""
        mock_response = sample_user_data
        self.mock_client.get = AsyncMock(return_value=mock_response)

        mock_user = Mock(spec=User)
        with patch.object(User, 'from_json', return_value=mock_user):
            result = await users.get_user(self.mock_client)

            assert result == mock_user
            self.mock_client.get.assert_called_once_with("/user")

    @pytest.mark.asyncio
    async def test_get_authenticated_user_direct(self, sample_user_data):
        """Test getting authenticated user using direct function."""
        mock_response = sample_user_data
        self.mock_client.get = AsyncMock(return_value=mock_response)

        mock_user = Mock(spec=User)
        with patch.object(User, 'from_json', return_value=mock_user):
            result = await users.get_authenticated_user(self.mock_client)

            assert result == mock_user
            self.mock_client.get.assert_called_once_with("/user")

    @pytest.mark.asyncio
    async def test_list_followers(self, sample_user_data):
        """Test listing user followers."""
        followers_data = [sample_user_data, sample_user_data]
        mock_response = followers_data
        self.mock_client.paginated_request = AsyncMock(return_value=mock_response)

        mock_user = Mock(spec=User)
        with patch.object(User, 'from_json', return_value=mock_user):
            result = await users.list_followers(self.mock_client, "testuser")

            assert len(result) == 2
            assert all(user == mock_user for user in result)
            # Check that the correct method was called
            self.mock_client.paginated_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_followers_with_pagination(self, sample_user_data):
        """Test listing followers with pagination."""
        mock_response = [sample_user_data]
        self.mock_client.paginated_request = AsyncMock(return_value=mock_response)

        mock_user = Mock(spec=User)
        with patch.object(User, 'from_json', return_value=mock_user):
            result = await users.list_followers(
                self.mock_client,
                "testuser",
                per_page=50,
                max_pages=2
            )

            assert len(result) == 1
            # Check that the function was called
            self.mock_client.paginated_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_following(self, sample_user_data):
        """Test listing users that a user follows."""
        following_data = [sample_user_data]
        mock_response = following_data
        self.mock_client.paginated_request = AsyncMock(return_value=mock_response)

        mock_user = Mock(spec=User)
        with patch.object(User, 'from_json', return_value=mock_user):
            result = await users.list_following(self.mock_client, "testuser")

            assert len(result) == 1
            assert result[0] == mock_user
            # Check that the function was called
            self.mock_client.paginated_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_following_true(self):
        """Test checking if user follows another user (true case)."""
        # Mock successful response (no exception)
        self.mock_client.get = AsyncMock(return_value=None)

        result = await users.check_following(self.mock_client, "user1", "user2")

        assert result is True
        self.mock_client.get.assert_called_once_with("/users/user1/following/user2")

    @pytest.mark.asyncio
    async def test_check_following_false(self):
        """Test checking if user follows another user (false case)."""
        # Mock APIError to simulate 404 response
        self.mock_client.get = AsyncMock(side_effect=APIError("Not found"))

        result = await users.check_following(self.mock_client, "user1", "user2")

        assert result is False

    @pytest.mark.asyncio
    async def test_follow_user_success(self):
        """Test following a user successfully."""
        # Mock successful response (no exception)
        self.mock_client.put = AsyncMock(return_value=None)

        result = await users.follow_user(self.mock_client, "testuser")

        assert result is True
        self.mock_client.put.assert_called_once_with("/user/following/testuser", data={})

    @pytest.mark.asyncio
    async def test_follow_user_failure(self):
        """Test following a user with failure."""
        self.mock_client.put = AsyncMock(side_effect=APIError("User not found"))

        result = await users.follow_user(self.mock_client, "nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_unfollow_user_success(self):
        """Test unfollowing a user successfully."""
        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={}
        )
        self.mock_client.delete = AsyncMock(return_value=mock_response)

        result = await users.unfollow_user(self.mock_client, "testuser")

        assert result is True
        self.mock_client.delete.assert_called_once_with("/user/following/testuser")

    @pytest.mark.asyncio
    async def test_unfollow_user_failure(self):
        """Test unfollowing a user with failure."""
        self.mock_client.delete = AsyncMock(side_effect=APIError("User not found"))

        result = await users.unfollow_user(self.mock_client, "nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_user_repositories(self, sample_repo_data):
        """Test listing user repositories."""
        repos_data = [sample_repo_data, sample_repo_data]
        mock_response = repos_data
        self.mock_client.paginated_request = AsyncMock(return_value=mock_response)

        mock_repo = Mock(spec=Repository)
        with patch.object(Repository, 'from_json', return_value=mock_repo):
            result = await users.list_user_repositories(
                self.mock_client,
                "testuser",
                type_filter="public",
                sort="updated",
                direction="desc"
            )

            assert len(result) == 2
            assert all(repo == mock_repo for repo in result)

            # Verify function was called
            self.mock_client.paginated_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_user_repositories_authenticated_user(self, sample_repo_data):
        """Test listing repositories for authenticated user."""
        repos_data = [sample_repo_data]
        mock_response = repos_data
        self.mock_client.paginated_request = AsyncMock(return_value=mock_response)

        mock_repo = Mock(spec=Repository)
        with patch.object(Repository, 'from_json', return_value=mock_repo):
            result = await users.list_user_repositories(self.mock_client)

            assert len(result) == 1

            # Verify function was called
            self.mock_client.paginated_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_star_repository_success(self):
        """Test starring a repository successfully."""
        self.mock_client.put = AsyncMock(return_value=None)

        result = await users.star_repository(self.mock_client, "owner", "repo")

        assert result is True
        self.mock_client.put.assert_called_once_with("/user/starred/owner/repo", data={})

    @pytest.mark.asyncio
    async def test_star_repository_failure(self):
        """Test starring a repository with failure."""
        self.mock_client.put = AsyncMock(side_effect=APIError("Repository not found"))

        result = await users.star_repository(self.mock_client, "owner", "nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_unstar_repository_success(self):
        """Test unstarring a repository successfully."""
        self.mock_client.delete = AsyncMock(return_value=None)

        result = await users.unstar_repository(self.mock_client, "owner", "repo")

        assert result is True
        self.mock_client.delete.assert_called_once_with("/user/starred/owner/repo")

    @pytest.mark.asyncio
    async def test_check_starred_true(self):
        """Test checking if repository is starred (true case)."""
        self.mock_client.get = AsyncMock(return_value=None)

        result = await users.check_starred(self.mock_client, "owner", "repo")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_starred_false(self):
        """Test checking if repository is starred (false case)."""
        self.mock_client.get = AsyncMock(side_effect=APIError("Not found"))

        result = await users.check_starred(self.mock_client, "owner", "repo")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_api_error(self):
        """Test API error handling in get_user."""
        self.mock_client.get = AsyncMock(side_effect=APIError("User not found"))

        with pytest.raises(APIError, match="User not found"):
            await users.get_user(self.mock_client, "nonexistent")


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 123456789,
        "login": "testuser",
        "name": "Test User",
        "email": "test@example.com",
        "bio": "A test user",
        "company": "Test Company",
        "location": "Test City",
        "blog": "https://testuser.dev",
        "twitter_username": "testuser",
        "public_repos": 10,
        "public_gists": 5,
        "followers": 100,
        "following": 50,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "avatar_url": "https://github.com/images/error/testuser_happy.gif",
        "html_url": "https://github.com/testuser",
        "type": "User",
        "site_admin": False
    }


@pytest.fixture
def sample_repo_data():
    """Sample repository data for testing."""
    return {
        "id": 987654321,
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "description": "A test repository",
        "private": False,
        "html_url": "https://github.com/testuser/test-repo",
        "clone_url": "https://github.com/testuser/test-repo.git",
        "ssh_url": "git@github.com:testuser/test-repo.git",
        "language": "Python",
        "stargazers_count": 42,
        "watchers_count": 42,
        "forks_count": 10,
        "open_issues_count": 3,
        "default_branch": "main",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "pushed_at": "2023-12-01T00:00:00Z"
    }
