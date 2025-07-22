"""
Unit tests for GitHub Gists API module.

Tests the GistsAPI class and its methods for managing GitHub gists.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api.gists import GistsAPI
from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError


@pytest.mark.unit
@pytest.mark.api
class TestGistsAPI:
    """Test cases for GistsAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        self.mock_ui = Mock(spec=TerminalUI)
        self.gists_api = GistsAPI(self.mock_client, self.mock_ui)

    def test_gists_api_initialization(self):
        """Test GistsAPI initialization."""
        assert self.gists_api.client == self.mock_client
        assert self.gists_api.ui == self.mock_ui

    def test_gists_api_initialization_without_ui(self):
        """Test GistsAPI initialization without UI."""
        api = GistsAPI(self.mock_client)
        assert api.client == self.mock_client
        assert api.ui is None

    @pytest.mark.asyncio
    async def test_list_gists_authenticated_user(self, sample_gist_data):
        """Test listing gists for authenticated user."""
        gists_data = [sample_gist_data]
        
        mock_response = APIResponse(
            status_code=200,
            data=gists_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.gists_api.list_gists()
        
        assert result == gists_data
        assert len(result) == 1
        self.mock_client.get.assert_called_once_with(
            "gists",
            params={"per_page": 30}
        )

    @pytest.mark.asyncio
    async def test_list_gists_specific_user(self, sample_gist_data):
        """Test listing gists for specific user."""
        username = "testuser"
        gists_data = [sample_gist_data]
        
        mock_response = APIResponse(
            status_code=200,
            data=gists_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.gists_api.list_gists(username=username)
        
        assert result == gists_data
        self.mock_client.get.assert_called_once_with(
            f"users/{username}/gists",
            params={"per_page": 30}
        )

    @pytest.mark.asyncio
    async def test_list_gists_custom_per_page(self):
        """Test listing gists with custom per_page parameter."""
        per_page = 50
        
        mock_response = APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        await self.gists_api.list_gists(per_page=per_page)
        
        self.mock_client.get.assert_called_once_with(
            "gists",
            params={"per_page": per_page}
        )

    @pytest.mark.asyncio
    async def test_get_gist_success(self, sample_gist_data):
        """Test successful gist retrieval."""
        gist_id = "abc123def456"
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_gist_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.gists_api.get_gist(gist_id)
        
        assert result == sample_gist_data
        self.mock_client.get.assert_called_once_with(f"gists/{gist_id}")

    @pytest.mark.asyncio
    async def test_get_gist_not_found(self):
        """Test getting non-existent gist."""
        gist_id = "nonexistent"
        
        self.mock_client.get.side_effect = NotFoundError("Gist not found")
        
        with pytest.raises(GitHubCLIError, match=f"Gist {gist_id} not found"):
            await self.gists_api.get_gist(gist_id)

    @pytest.mark.asyncio
    async def test_create_gist_success(self, sample_gist_data):
        """Test successful gist creation."""
        files = {
            "test.py": {
                "content": "print('Hello, World!')"
            },
            "README.md": {
                "content": "# Test Gist\n\nThis is a test gist."
            }
        }
        description = "Test gist"
        public = True
        
        mock_response = APIResponse(
            status_code=201,
            data=sample_gist_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.gists_api.create_gist(files, description, public)
        
        assert result == sample_gist_data
        self.mock_client.post.assert_called_once_with(
            "gists",
            data={
                "files": files,
                "public": public,
                "description": description
            }
        )

    @pytest.mark.asyncio
    async def test_create_gist_minimal(self, sample_gist_data):
        """Test creating gist with minimal data."""
        files = {
            "test.txt": {
                "content": "Hello, World!"
            }
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=sample_gist_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.gists_api.create_gist(files)
        
        assert result == sample_gist_data
        self.mock_client.post.assert_called_once_with(
            "gists",
            data={
                "files": files,
                "public": True
            }
        )

    @pytest.mark.asyncio
    async def test_update_gist_success(self, sample_gist_data):
        """Test successful gist update."""
        gist_id = "abc123def456"
        files = {
            "test.py": {
                "content": "print('Updated content!')"
            }
        }
        description = "Updated description"
        
        updated_gist_data = sample_gist_data.copy()
        updated_gist_data["description"] = description
        
        mock_response = APIResponse(
            status_code=200,
            data=updated_gist_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.patch.return_value = mock_response
        
        result = await self.gists_api.update_gist(gist_id, files, description)
        
        assert result == updated_gist_data
        self.mock_client.patch.assert_called_once_with(
            f"gists/{gist_id}",
            data={
                "files": files,
                "description": description
            }
        )

    @pytest.mark.asyncio
    async def test_update_gist_files_only(self, sample_gist_data):
        """Test updating gist with files only."""
        gist_id = "abc123def456"
        files = {
            "test.py": {
                "content": "print('Updated content!')"
            }
        }
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_gist_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.patch.return_value = mock_response
        
        result = await self.gists_api.update_gist(gist_id, files=files)
        
        assert result == sample_gist_data
        self.mock_client.patch.assert_called_once_with(
            f"gists/{gist_id}",
            data={"files": files}
        )

    @pytest.mark.asyncio
    async def test_update_gist_description_only(self, sample_gist_data):
        """Test updating gist with description only."""
        gist_id = "abc123def456"
        description = "Updated description"
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_gist_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.patch.return_value = mock_response
        
        result = await self.gists_api.update_gist(gist_id, description=description)
        
        assert result == sample_gist_data
        self.mock_client.patch.assert_called_once_with(
            f"gists/{gist_id}",
            data={"description": description}
        )

    @pytest.mark.asyncio
    async def test_update_gist_not_found(self):
        """Test updating non-existent gist."""
        gist_id = "nonexistent"
        files = {"test.txt": {"content": "test"}}
        
        self.mock_client.patch.side_effect = NotFoundError("Gist not found")
        
        with pytest.raises(GitHubCLIError, match=f"Gist {gist_id} not found"):
            await self.gists_api.update_gist(gist_id, files=files)

    @pytest.mark.asyncio
    async def test_delete_gist_success(self):
        """Test successful gist deletion."""
        gist_id = "abc123def456"
        
        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.delete.return_value = mock_response
        
        await self.gists_api.delete_gist(gist_id)
        
        self.mock_client.delete.assert_called_once_with(f"gists/{gist_id}")

    @pytest.mark.asyncio
    async def test_delete_gist_not_found(self):
        """Test deleting non-existent gist."""
        gist_id = "nonexistent"
        
        self.mock_client.delete.side_effect = NotFoundError("Gist not found")
        
        with pytest.raises(GitHubCLIError, match=f"Gist {gist_id} not found"):
            await self.gists_api.delete_gist(gist_id)

    @pytest.mark.asyncio
    async def test_star_gist_success(self):
        """Test successful gist starring."""
        gist_id = "abc123def456"
        
        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.put.return_value = mock_response
        
        await self.gists_api.star_gist(gist_id)
        
        self.mock_client.put.assert_called_once_with(f"gists/{gist_id}/star")

    @pytest.mark.asyncio
    async def test_unstar_gist_success(self):
        """Test successful gist unstarring."""
        gist_id = "abc123def456"
        
        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.delete.return_value = mock_response
        
        await self.gists_api.unstar_gist(gist_id)
        
        self.mock_client.delete.assert_called_once_with(f"gists/{gist_id}/star")

    @pytest.mark.asyncio
    async def test_is_gist_starred_true(self):
        """Test checking if gist is starred (returns True)."""
        gist_id = "abc123def456"
        
        mock_response = APIResponse(
            status_code=204,
            data=None,
            headers={},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.gists_api.is_gist_starred(gist_id)
        
        assert result is True
        self.mock_client.get.assert_called_once_with(f"gists/{gist_id}/star")

    @pytest.mark.asyncio
    async def test_is_gist_starred_false(self):
        """Test checking if gist is starred (returns False)."""
        gist_id = "abc123def456"
        
        self.mock_client.get.side_effect = NotFoundError("Not starred")
        
        result = await self.gists_api.is_gist_starred(gist_id)
        
        assert result is False
        self.mock_client.get.assert_called_once_with(f"gists/{gist_id}/star")

    @pytest.mark.asyncio
    async def test_list_gists_api_error(self):
        """Test handling API error during gist listing."""
        self.mock_client.get.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to list gists: API Error"):
            await self.gists_api.list_gists()

    @pytest.mark.asyncio
    async def test_create_gist_api_error(self):
        """Test handling API error during gist creation."""
        files = {"test.txt": {"content": "test"}}
        
        self.mock_client.post.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to create gist: API Error"):
            await self.gists_api.create_gist(files)
