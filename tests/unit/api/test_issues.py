"""
Unit tests for GitHub Issues API module.

Tests the IssuesAPI class and its methods for managing GitHub issues.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api.issues import IssuesAPI
from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
from github_cli.ui.terminal import TerminalUI
from github_cli.models.issue import Issue
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError


@pytest.mark.unit
@pytest.mark.api
class TestIssuesAPI:
    """Test cases for IssuesAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        self.mock_ui = Mock(spec=TerminalUI)
        self.issues_api = IssuesAPI(self.mock_client, self.mock_ui)

    def test_issues_api_initialization(self):
        """Test IssuesAPI initialization."""
        assert self.issues_api.client == self.mock_client
        assert self.issues_api.ui == self.mock_ui

    def test_issues_api_initialization_without_ui(self):
        """Test IssuesAPI initialization without UI."""
        api = IssuesAPI(self.mock_client)
        assert api.client == self.mock_client
        assert api.ui is None

    @pytest.mark.asyncio
    async def test_list_issues_success(self, sample_issue_data):
        """Test successful listing of issues."""
        repo = "testuser/test-repo"
        issues_data = [sample_issue_data]
        
        mock_response = APIResponse(
            status_code=200,
            data=issues_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.issues_api.list_issues(repo=repo)
        
        assert len(result) == 1
        assert isinstance(result[0], Issue)
        assert result[0].number == sample_issue_data["number"]
        self.mock_client.get.assert_called_once_with(
            f"repos/{repo}/issues",
            params={
                "state": "open",
                "sort": "created", 
                "direction": "desc"
            }
        )

    @pytest.mark.asyncio
    async def test_list_issues_with_filters(self):
        """Test listing issues with various filters."""
        repo = "testuser/test-repo"
        
        mock_response = APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        await self.issues_api.list_issues(
            repo=repo,
            state="closed",
            labels="bug,enhancement",
            assignee="testuser",
            creator="author",
            mentioned="mentioned_user",
            sort="updated",
            direction="asc"
        )
        
        self.mock_client.get.assert_called_once_with(
            f"repos/{repo}/issues",
            params={
                "state": "closed",
                "sort": "updated",
                "direction": "asc",
                "labels": "bug,enhancement",
                "assignee": "testuser",
                "creator": "author",
                "mentioned": "mentioned_user"
            }
        )

    @pytest.mark.asyncio
    async def test_list_issues_user_issues(self):
        """Test listing user's issues (no repo specified)."""
        mock_response = APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        await self.issues_api.list_issues()
        
        self.mock_client.get.assert_called_once_with(
            "issues",
            params={
                "state": "open",
                "sort": "created",
                "direction": "desc"
            }
        )

    @pytest.mark.asyncio
    async def test_get_issue_success(self, sample_issue_data):
        """Test successful issue retrieval."""
        repo = "testuser/test-repo"
        issue_number = 42
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_issue_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.issues_api.get_issue(repo, issue_number)
        
        assert isinstance(result, Issue)
        assert result.number == sample_issue_data["number"]
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/issues/{issue_number}")

    @pytest.mark.asyncio
    async def test_get_issue_not_found(self):
        """Test getting non-existent issue."""
        repo = "testuser/test-repo"
        issue_number = 999
        
        self.mock_client.get.side_effect = NotFoundError("Issue not found")
        
        with pytest.raises(GitHubCLIError, match=f"Issue #{issue_number} not found in {repo}"):
            await self.issues_api.get_issue(repo, issue_number)

    @pytest.mark.asyncio
    async def test_create_issue_success(self, sample_issue_data):
        """Test successful issue creation."""
        repo = "testuser/test-repo"
        title = "Test Issue"
        body = "This is a test issue"
        assignees = ["testuser"]
        labels = ["bug", "enhancement"]
        milestone = 1
        
        mock_response = APIResponse(
            status_code=201,
            data=sample_issue_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.issues_api.create_issue(
            repo=repo,
            title=title,
            body=body,
            assignees=assignees,
            labels=labels,
            milestone=milestone
        )
        
        assert isinstance(result, Issue)
        assert result.number == sample_issue_data["number"]
        self.mock_client.post.assert_called_once_with(
            f"repos/{repo}/issues",
            data={
                "title": title,
                "body": body,
                "assignees": assignees,
                "labels": labels,
                "milestone": milestone
            }
        )

    @pytest.mark.asyncio
    async def test_create_issue_minimal(self, sample_issue_data):
        """Test creating issue with minimal data."""
        repo = "testuser/test-repo"
        title = "Test Issue"
        
        mock_response = APIResponse(
            status_code=201,
            data=sample_issue_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.issues_api.create_issue(repo=repo, title=title)
        
        assert isinstance(result, Issue)
        self.mock_client.post.assert_called_once_with(
            f"repos/{repo}/issues",
            data={"title": title}
        )

    @pytest.mark.asyncio
    async def test_update_issue_success(self, sample_issue_data):
        """Test successful issue update."""
        repo = "testuser/test-repo"
        issue_number = 42
        update_data = {
            "title": "Updated Issue Title",
            "body": "Updated issue body",
            "state": "closed"
        }
        
        updated_issue_data = sample_issue_data.copy()
        updated_issue_data.update(update_data)
        
        mock_response = APIResponse(
            status_code=200,
            data=updated_issue_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.patch.return_value = mock_response
        
        result = await self.issues_api.update_issue(repo, issue_number, **update_data)
        
        assert isinstance(result, Issue)
        self.mock_client.patch.assert_called_once_with(
            f"repos/{repo}/issues/{issue_number}",
            data=update_data
        )

    @pytest.mark.asyncio
    async def test_add_comment_success(self):
        """Test successful comment addition."""
        repo = "testuser/test-repo"
        issue_number = 42
        comment_body = "This is a test comment"
        
        comment_data = {
            "id": 123456,
            "body": comment_body,
            "user": {"login": "testuser"},
            "created_at": "2023-12-01T00:00:00Z",
            "html_url": "https://github.com/testuser/test-repo/issues/42#issuecomment-123456"
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=comment_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.issues_api.add_comment(repo, issue_number, comment_body)
        
        assert result == comment_data
        self.mock_client.post.assert_called_once_with(
            f"repos/{repo}/issues/{issue_number}/comments",
            data={"body": comment_body}
        )

    @pytest.mark.asyncio
    async def test_list_comments_success(self):
        """Test successful comment listing."""
        repo = "testuser/test-repo"
        issue_number = 42
        
        comments_data = [
            {
                "id": 123456,
                "body": "First comment",
                "user": {"login": "user1"},
                "created_at": "2023-12-01T00:00:00Z"
            },
            {
                "id": 123457,
                "body": "Second comment",
                "user": {"login": "user2"},
                "created_at": "2023-12-01T01:00:00Z"
            }
        ]
        
        mock_response = APIResponse(
            status_code=200,
            data=comments_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.issues_api.list_comments(repo, issue_number)
        
        assert result == comments_data
        assert len(result) == 2
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/issues/{issue_number}/comments")

    @pytest.mark.asyncio
    async def test_list_issues_api_error(self):
        """Test handling API error during issue listing."""
        repo = "testuser/test-repo"
        
        self.mock_client.get.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to list issues: API Error"):
            await self.issues_api.list_issues(repo=repo)

    @pytest.mark.asyncio
    async def test_create_issue_api_error(self):
        """Test handling API error during issue creation."""
        repo = "testuser/test-repo"
        title = "Test Issue"
        
        self.mock_client.post.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to create issue: API Error"):
            await self.issues_api.create_issue(repo=repo, title=title)
