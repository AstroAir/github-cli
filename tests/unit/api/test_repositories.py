"""
Unit tests for Repositories API module.

Tests repository-related API operations including listing, creating,
updating, and managing repositories.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api.repositories import RepositoriesAPI
from github_cli.api.client import GitHubClient, APIResponse
from github_cli.models.repository import Repository
from github_cli.utils.exceptions import GitHubCLIError, NetworkError


@pytest.mark.unit
@pytest.mark.api
class TestRepositoriesAPI:
    """Test cases for RepositoriesAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        self.repositories_api = RepositoriesAPI(self.mock_client)

    def test_repositories_api_initialization(self):
        """Test RepositoriesAPI initialization."""
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
            url="https://api.github.com/user/repos"
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.repositories_api.list_user_repositories()
        
        assert len(result) == 1
        assert isinstance(result[0], Repository)
        assert result[0].name == sample_repository_data["name"]
        self.mock_client.get.assert_called_once_with("/user/repos", params={})

    @pytest.mark.asyncio
    async def test_list_user_repositories_with_params(self):
        """Test listing user repositories with parameters."""
        mock_response = APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            url="https://api.github.com/user/repos"
        )
        
        self.mock_client.get.return_value = mock_response
        
        params = {
            "visibility": "private",
            "sort": "updated",
            "direction": "desc",
            "per_page": 50
        }
        
        await self.repositories_api.list_user_repositories(**params)
        
        self.mock_client.get.assert_called_once_with("/user/repos", params=params)

    @pytest.mark.asyncio
    async def test_list_org_repositories_success(self, sample_repository_data):
        """Test successful listing of organization repositories."""
        org_name = "test-org"
        repositories_data = [sample_repository_data]
        mock_response = APIResponse(
            status_code=200,
            data=repositories_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/orgs/{org_name}/repos"
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.repositories_api.list_org_repositories(org_name)
        
        assert len(result) == 1
        assert isinstance(result[0], Repository)
        self.mock_client.get.assert_called_once_with(f"/orgs/{org_name}/repos", params={})

    @pytest.mark.asyncio
    async def test_get_repository_success(self, sample_repository_data):
        """Test successful repository retrieval."""
        owner = "testuser"
        repo = "test-repo"
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_repository_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}"
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.repositories_api.get_repository(owner, repo)
        
        assert isinstance(result, Repository)
        assert result.name == sample_repository_data["name"]
        self.mock_client.get.assert_called_once_with(f"/repos/{owner}/{repo}")

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self):
        """Test repository retrieval when repository not found."""
        owner = "testuser"
        repo = "nonexistent-repo"
        
        mock_response = APIResponse(
            status_code=404,
            data={"message": "Not Found"},
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}"
        )
        
        self.mock_client.get.return_value = mock_response
        
        with pytest.raises(GitHubCLIError, match="Repository not found"):
            await self.repositories_api.get_repository(owner, repo)

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
            "owner": {"id": 987654321, "login": "testuser", "type": "User"}
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=created_repo_data,
            headers={"content-type": "application/json"},
            url="https://api.github.com/user/repos"
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.repositories_api.create_repository(repo_data)
        
        assert isinstance(result, Repository)
        assert result.name == "new-repo"
        self.mock_client.post.assert_called_once_with("/user/repos", data=repo_data)

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
            "owner": {"id": 123456789, "login": "test-org", "type": "Organization"}
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=created_repo_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/orgs/{org_name}/repos"
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.repositories_api.create_org_repository(org_name, repo_data)
        
        assert isinstance(result, Repository)
        assert result.name == "org-repo"
        self.mock_client.post.assert_called_once_with(f"/orgs/{org_name}/repos", data=repo_data)

    @pytest.mark.asyncio
    async def test_update_repository_success(self, sample_repository_data):
        """Test successful repository update."""
        owner = "testuser"
        repo = "test-repo"
        update_data = {
            "description": "Updated description",
            "homepage": "https://updated.example.com"
        }
        
        updated_repo_data = sample_repository_data.copy()
        updated_repo_data.update(update_data)
        
        mock_response = APIResponse(
            status_code=200,
            data=updated_repo_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}"
        )
        
        self.mock_client.patch.return_value = mock_response
        
        result = await self.repositories_api.update_repository(owner, repo, update_data)
        
        assert isinstance(result, Repository)
        assert result.description == "Updated description"
        self.mock_client.patch.assert_called_once_with(f"/repos/{owner}/{repo}", data=update_data)

    @pytest.mark.asyncio
    async def test_delete_repository_success(self):
        """Test successful repository deletion."""
        owner = "testuser"
        repo = "test-repo"
        
        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={},
            url=f"https://api.github.com/repos/{owner}/{repo}"
        )
        
        self.mock_client.delete.return_value = mock_response
        
        result = await self.repositories_api.delete_repository(owner, repo)
        
        assert result is True
        self.mock_client.delete.assert_called_once_with(f"/repos/{owner}/{repo}")

    @pytest.mark.asyncio
    async def test_delete_repository_not_found(self):
        """Test repository deletion when repository not found."""
        owner = "testuser"
        repo = "nonexistent-repo"
        
        mock_response = APIResponse(
            status_code=404,
            data={"message": "Not Found"},
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}"
        )
        
        self.mock_client.delete.return_value = mock_response
        
        with pytest.raises(GitHubCLIError, match="Repository not found"):
            await self.repositories_api.delete_repository(owner, repo)

    @pytest.mark.asyncio
    async def test_fork_repository_success(self, sample_repository_data):
        """Test successful repository forking."""
        owner = "original-owner"
        repo = "original-repo"
        
        forked_repo_data = sample_repository_data.copy()
        forked_repo_data.update({
            "name": "original-repo",
            "full_name": "testuser/original-repo",
            "fork": True,
            "parent": {
                "id": 987654321,
                "name": "original-repo",
                "full_name": "original-owner/original-repo"
            }
        })
        
        mock_response = APIResponse(
            status_code=202,
            data=forked_repo_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}/forks"
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.repositories_api.fork_repository(owner, repo)
        
        assert isinstance(result, Repository)
        assert result.fork is True
        self.mock_client.post.assert_called_once_with(f"/repos/{owner}/{repo}/forks", data={})

    @pytest.mark.asyncio
    async def test_fork_repository_to_org(self, sample_repository_data):
        """Test forking repository to organization."""
        owner = "original-owner"
        repo = "original-repo"
        org = "target-org"
        
        forked_repo_data = sample_repository_data.copy()
        forked_repo_data.update({
            "name": "original-repo",
            "full_name": f"{org}/original-repo",
            "fork": True,
            "owner": {"id": 123456789, "login": org, "type": "Organization"}
        })
        
        mock_response = APIResponse(
            status_code=202,
            data=forked_repo_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}/forks"
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.repositories_api.fork_repository(owner, repo, organization=org)
        
        assert isinstance(result, Repository)
        assert result.owner["login"] == org
        self.mock_client.post.assert_called_once_with(
            f"/repos/{owner}/{repo}/forks", 
            data={"organization": org}
        )

    @pytest.mark.asyncio
    async def test_list_repository_topics_success(self):
        """Test successful repository topics listing."""
        owner = "testuser"
        repo = "test-repo"
        
        topics_data = {
            "names": ["python", "cli", "github", "api"]
        }
        
        mock_response = APIResponse(
            status_code=200,
            data=topics_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}/topics"
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.repositories_api.list_repository_topics(owner, repo)
        
        assert result == topics_data["names"]
        self.mock_client.get.assert_called_once_with(
            f"/repos/{owner}/{repo}/topics",
            headers={"Accept": "application/vnd.github.mercy-preview+json"}
        )

    @pytest.mark.asyncio
    async def test_update_repository_topics_success(self):
        """Test successful repository topics update."""
        owner = "testuser"
        repo = "test-repo"
        topics = ["python", "cli", "github"]
        
        topics_data = {
            "names": topics
        }
        
        mock_response = APIResponse(
            status_code=200,
            data=topics_data,
            headers={"content-type": "application/json"},
            url=f"https://api.github.com/repos/{owner}/{repo}/topics"
        )
        
        self.mock_client.put.return_value = mock_response
        
        result = await self.repositories_api.update_repository_topics(owner, repo, topics)
        
        assert result == topics
        self.mock_client.put.assert_called_once_with(
            f"/repos/{owner}/{repo}/topics",
            data={"names": topics},
            headers={"Accept": "application/vnd.github.mercy-preview+json"}
        )

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        self.mock_client.get.side_effect = NetworkError("Connection failed")
        
        with pytest.raises(NetworkError, match="Connection failed"):
            await self.repositories_api.list_user_repositories()

    @pytest.mark.asyncio
    async def test_invalid_repository_data_handling(self):
        """Test handling of invalid repository data."""
        # Mock response with missing required fields
        invalid_data = {"name": "incomplete-repo"}  # Missing required fields
        
        mock_response = APIResponse(
            status_code=200,
            data=[invalid_data],
            headers={"content-type": "application/json"},
            url="https://api.github.com/user/repos"
        )
        
        self.mock_client.get.return_value = mock_response
        
        with pytest.raises(GitHubCLIError, match="Invalid repository data"):
            await self.repositories_api.list_user_repositories()
