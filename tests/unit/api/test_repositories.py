"""
Unit tests for Repositories API module.

Tests repository-related API operations including listing, creating,
updating, and managing repositories.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api.repositories import RepositoryAPI
from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
from github_cli.models.repository import Repository
from github_cli.utils.exceptions import GitHubCLIError, NetworkError, NotFoundError


@pytest.mark.unit
@pytest.mark.api
class TestRepositoryAPI:
    """Test cases for RepositoryAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        self.repositories_api = RepositoryAPI(self.mock_client)

    def test_repositories_api_initialization(self):
        """Test RepositoryAPI initialization."""
        assert self.repositories_api.client == self.mock_client

    @pytest.mark.asyncio
    async def test_list_user_repositories_success(self, sample_repository_data):
        """Test successful listing of user repositories."""
        # Mock API response
        repositories_data = [sample_repository_data]
        mock_response = APIResponse(
            status_code=200,
            data=repositories_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.repositories_api.list_user_repos()
        
        assert len(result) == 1
        assert isinstance(result[0], Repository)
        assert result[0].name == sample_repository_data["name"]
        self.mock_client.get.assert_called_once_with("user/repos", params={
            "sort": "updated",
            "per_page": 30,
            "page": 1
        })

    @pytest.mark.asyncio
    async def test_list_user_repositories_with_params(self):
        """Test listing user repositories with parameters."""
        mock_response = APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        # Test with custom parameters
        await self.repositories_api.list_user_repos(sort="updated", per_page=50)

        self.mock_client.get.assert_called_once_with("user/repos", params={
            "sort": "updated",
            "per_page": 50,
            "page": 1
        })

    @pytest.mark.asyncio
    async def test_list_org_repositories_success(self, sample_repository_data):
        """Test successful listing of organization repositories."""
        org_name = "test-org"
        repositories_data = [sample_repository_data]
        mock_response = APIResponse(
            status_code=200,
            data=repositories_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        result = await self.repositories_api.list_org_repos(org_name)

        assert len(result) == 1
        assert isinstance(result[0], Repository)
        self.mock_client.get.assert_called_once_with(f"orgs/{org_name}/repos", params={
            "type": "all",
            "sort": "updated",
            "per_page": 30,
            "page": 1
        })

    @pytest.mark.asyncio
    async def test_get_repository_success(self, sample_repository_data):
        """Test successful repository retrieval."""
        repo_name = "testuser/test-repo"

        mock_response = APIResponse(
            status_code=200,
            data=sample_repository_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        result = await self.repositories_api.get_repo(repo_name)

        assert isinstance(result, Repository)
        assert result.name == sample_repository_data["name"]
        self.mock_client.get.assert_called_once_with(f"repos/{repo_name}")

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self):
        """Test repository retrieval when repository not found."""
        repo_name = "testuser/nonexistent-repo"

        # Mock NotFoundError to be raised by the client
        self.mock_client.get.side_effect = NotFoundError("Not Found")

        with pytest.raises(GitHubCLIError, match="Repository not found"):
            await self.repositories_api.get_repo(repo_name)

    @pytest.mark.asyncio
    async def test_create_repository_success(self):
        """Test successful repository creation."""
        repo_data = {
            "name": "new-repo",
            "description": "A new repository",
            "private": False,
            "auto_init": True
        }
        
        created_repo_data = {
            "id": 123456789,
            "name": "new-repo",
            "full_name": "testuser/new-repo",
            "description": "A new repository",
            "private": False,
            "fork": False,
            "html_url": "https://github.com/testuser/new-repo",
            "clone_url": "https://github.com/testuser/new-repo.git",
            "ssh_url": "git@github.com:testuser/new-repo.git",
            "homepage": None,
            "stargazers_count": 0,
            "watchers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "size": 0,
            "language": None,
            "topics": [],
            "license": None,
            "default_branch": "main",
            "visibility": "public",
            "created_at": "2023-12-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z",
            "pushed_at": "2023-12-01T00:00:00Z",
            "archived": False,
            "disabled": False,
            "owner": {"id": 987654321, "login": "testuser", "type": "User"},
            "url": "https://api.github.com/repos/testuser/new-repo"
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=created_repo_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.post.return_value = mock_response

        result = await self.repositories_api.create_repo(
            name="new-repo",
            description="A new repository",
            private=False,
            auto_init=True
        )

        assert isinstance(result, Repository)
        assert result.name == "new-repo"

        expected_data = {
            "name": "new-repo",
            "private": False,
            "auto_init": True,
            "description": "A new repository"
        }
        self.mock_client.post.assert_called_once_with("user/repos", data=expected_data)

    @pytest.mark.asyncio
    async def test_create_org_repository_success(self):
        """Test successful organization repository creation."""
        org_name = "test-org"
        repo_data = {
            "name": "org-repo",
            "description": "Organization repository",
            "private": True
        }
        
        created_repo_data = {
            "id": 123456789,
            "name": "org-repo",
            "full_name": "test-org/org-repo",
            "description": "Organization repository",
            "private": True,
            "fork": False,
            "html_url": "https://github.com/test-org/org-repo",
            "clone_url": "https://github.com/test-org/org-repo.git",
            "ssh_url": "git@github.com:test-org/org-repo.git",
            "homepage": None,
            "stargazers_count": 0,
            "watchers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "size": 0,
            "language": None,
            "topics": [],
            "license": None,
            "default_branch": "main",
            "visibility": "private",
            "created_at": "2023-12-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z",
            "pushed_at": "2023-12-01T00:00:00Z",
            "archived": False,
            "disabled": False,
            "owner": {"id": 123456789, "login": "test-org", "type": "Organization"},
            "url": "https://api.github.com/repos/test-org/org-repo"
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=created_repo_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.post.return_value = mock_response

        result = await self.repositories_api.create_repo(
            name="org-repo",
            description="Organization repository",
            private=True,
            org=org_name
        )

        assert isinstance(result, Repository)
        assert result.name == "org-repo"

        expected_data = {
            "name": "org-repo",
            "private": True,
            "description": "Organization repository"
        }
        self.mock_client.post.assert_called_once_with(f"orgs/{org_name}/repos", data=expected_data)

    @pytest.mark.asyncio
    async def test_update_repository_success(self, sample_repository_data):
        """Test successful repository update."""
        repo_name = "testuser/test-repo"

        updated_repo_data = sample_repository_data.copy()
        updated_repo_data.update({
            "description": "Updated description",
            "homepage": "https://updated.example.com"
        })

        mock_response = APIResponse(
            status_code=200,
            data=updated_repo_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.patch.return_value = mock_response

        result = await self.repositories_api.update_repo(
            repo_name,
            description="Updated description",
            homepage="https://updated.example.com"
        )

        assert isinstance(result, Repository)
        assert result.description == "Updated description"

        expected_data = {
            "description": "Updated description",
            "homepage": "https://updated.example.com"
        }
        self.mock_client.patch.assert_called_once_with(f"repos/{repo_name}", data=expected_data)

    @pytest.mark.asyncio
    async def test_delete_repository_success(self):
        """Test successful repository deletion."""
        repo_name = "testuser/test-repo"

        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.delete.return_value = mock_response

        result = await self.repositories_api.delete_repo(repo_name)

        assert result is True
        self.mock_client.delete.assert_called_once_with(f"repos/{repo_name}")

    @pytest.mark.asyncio
    async def test_delete_repository_not_found(self):
        """Test repository deletion when repository not found."""
        repo_name = "testuser/nonexistent-repo"

        # Mock the client to raise an exception for 404
        self.mock_client.delete.side_effect = GitHubCLIError("Repository not found")

        with pytest.raises(GitHubCLIError, match="Repository not found"):
            await self.repositories_api.delete_repo(repo_name)





    @pytest.mark.asyncio
    async def test_list_repository_topics_success(self):
        """Test successful repository topics listing."""
        repo_name = "testuser/test-repo"

        topics_data = {
            "names": ["python", "cli", "github", "api"]
        }

        mock_response = APIResponse(
            status_code=200,
            data=topics_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        result = await self.repositories_api.list_topics(repo_name)

        assert result == topics_data["names"]
        self.mock_client.get.assert_called_once_with(
            f"repos/{repo_name}/topics",
            params={"headers": {"Accept": "application/vnd.github.mercy-preview+json"}}
        )

    @pytest.mark.asyncio
    async def test_add_repository_topics_success(self):
        """Test successful repository topics addition."""
        repo_name = "testuser/test-repo"
        new_topics = ["python", "cli"]

        # Mock current topics response
        current_topics_data = {"names": ["github"]}
        current_response = APIResponse(
            status_code=200,
            data=current_topics_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        # Mock updated topics response
        updated_topics_data = {"names": ["github", "python", "cli"]}
        updated_response = APIResponse(
            status_code=200,
            data=updated_topics_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        # Set up mock to return different responses for get and put
        self.mock_client.get.return_value = current_response
        self.mock_client.put.return_value = updated_response

        result = await self.repositories_api.add_topics(repo_name, new_topics)

        assert "github" in result
        assert "python" in result
        assert "cli" in result
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        self.mock_client.get.side_effect = NetworkError("Connection failed")

        with pytest.raises(NetworkError, match="Connection failed"):
            await self.repositories_api.list_user_repos()

    @pytest.mark.asyncio
    async def test_invalid_repository_data_handling(self):
        """Test handling of invalid repository data."""
        # Mock response with missing required fields
        invalid_data = {"name": "incomplete-repo"}  # Missing required fields

        mock_response = APIResponse(
            status_code=200,
            data=[invalid_data],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        # This should raise an error when trying to create Repository objects
        with pytest.raises((GitHubCLIError, KeyError, TypeError)):
            await self.repositories_api.list_user_repos()
