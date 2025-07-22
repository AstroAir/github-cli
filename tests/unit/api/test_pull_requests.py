"""
Unit tests for Pull Requests API module.

Tests pull request-related API operations including listing, creating,
updating, and managing pull requests.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api.pull_requests import PullRequestAPI
from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
from github_cli.models.pull_request import PullRequest
from github_cli.utils.exceptions import GitHubCLIError, NetworkError, NotFoundError


@pytest.mark.unit
@pytest.mark.api
class TestPullRequestAPI:
    """Test cases for PullRequestAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        self.pull_requests_api = PullRequestAPI(self.mock_client)

    def test_pull_requests_api_initialization(self):
        """Test PullRequestAPI initialization."""
        assert self.pull_requests_api.client == self.mock_client

    @pytest.mark.asyncio
    async def test_list_pull_requests_success(self, sample_pull_request_data):
        """Test successful listing of pull requests."""
        repo = "testuser/test-repo"

        pull_requests_data = [sample_pull_request_data]
        mock_response = APIResponse(
            status_code=200,
            data=pull_requests_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        result = await self.pull_requests_api.list_pull_requests(repo)

        assert len(result) == 1
        assert isinstance(result[0], PullRequest)
        assert result[0].number == sample_pull_request_data["number"]
        self.mock_client.get.assert_called_once_with(
            f"repos/{repo}/pulls",
            params={"state": "open", "sort": "created", "direction": "desc"}
        )

    @pytest.mark.asyncio
    async def test_list_pull_requests_with_params(self):
        """Test listing pull requests with parameters."""
        repo = "testuser/test-repo"

        mock_response = APIResponse(
            status_code=200,
            data=[],
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        # Test with custom parameters
        await self.pull_requests_api.list_pull_requests(
            repo, state="closed", sort="updated", direction="desc"
        )

        self.mock_client.get.assert_called_once_with(
            f"repos/{repo}/pulls",
            params={"state": "closed", "sort": "updated", "direction": "desc"}
        )

    @pytest.mark.asyncio
    async def test_get_pull_request_success(self, sample_pull_request_data):
        """Test successful pull request retrieval."""
        repo = "testuser/test-repo"
        pr_number = 42

        mock_response = APIResponse(
            status_code=200,
            data=sample_pull_request_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.get.return_value = mock_response

        result = await self.pull_requests_api.get_pull_request(repo, pr_number)

        assert isinstance(result, PullRequest)
        assert result.number == sample_pull_request_data["number"]
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/pulls/{pr_number}")

    @pytest.mark.asyncio
    async def test_get_pull_request_not_found(self):
        """Test pull request retrieval when PR not found."""
        repo = "testuser/test-repo"
        pr_number = 999

        # Mock NotFoundError to be raised by the client
        self.mock_client.get.side_effect = NotFoundError("Not Found")

        with pytest.raises(GitHubCLIError, match="Pull request #999 not found"):
            await self.pull_requests_api.get_pull_request(repo, pr_number)

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful pull request creation."""
        repo = "testuser/test-repo"

        title = "Add new feature"
        body = "This PR adds a new feature to the application."
        head = "feature-branch"
        base = "main"
        
        created_pr_data = {
            "id": 555666777,
            "number": 42,
            "title": title,
            "body": body,
            "state": "open",
            "draft": False,
            "locked": False,
            "html_url": f"https://github.com/{repo}/pull/42",
            "diff_url": f"https://github.com/{repo}/pull/42.diff",
            "patch_url": f"https://github.com/{repo}/pull/42.patch",
            "created_at": "2023-12-01T00:00:00Z",
            "updated_at": "2023-12-01T00:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "assignees": [],
            "requested_reviewers": [],
            "labels": [],
            "milestone": None,
            "head": {
                "ref": head,
                "sha": "abc123def456",
                "repo": {"name": repo.split('/')[1], "full_name": repo}
            },
            "base": {
                "ref": base,
                "sha": "def456abc123",
                "repo": {"name": repo.split('/')[1], "full_name": repo}
            },
            "user": {"id": 987654321, "login": repo.split('/')[0], "type": "User"},
            "mergeable": True,
            "mergeable_state": "clean",
            "merged": False,
            "comments": 0,
            "review_comments": 0,
            "commits": 1,
            "additions": 10,
            "deletions": 2,
            "changed_files": 1,
            # Additional fields required by Issue model
            "author_association": "OWNER",
            "url": f"https://api.github.com/repos/{repo}/pulls/42",
            "repository_url": f"https://api.github.com/repos/{repo}"
        }
        
        mock_response = APIResponse(
            status_code=201,
            data=created_pr_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.post.return_value = mock_response

        result = await self.pull_requests_api.create_pull_request(repo, title, head, base, body)

        assert isinstance(result, PullRequest)
        assert result.title == title
        assert result.number == 42

        expected_data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": False,
            "body": body
        }
        self.mock_client.post.assert_called_once_with(f"repos/{repo}/pulls", data=expected_data)

    @pytest.mark.asyncio
    async def test_update_pull_request_success(self, sample_pull_request_data):
        """Test successful pull request update."""
        repo = "testuser/test-repo"
        pr_number = 42

        update_data = {
            "title": "Updated PR title",
            "body": "Updated PR description"
        }

        updated_pr_data = sample_pull_request_data.copy()
        updated_pr_data.update(update_data)

        mock_response = APIResponse(
            status_code=200,
            data=updated_pr_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.patch.return_value = mock_response

        result = await self.pull_requests_api.update_pull_request(repo, pr_number, **update_data)

        assert isinstance(result, PullRequest)
        assert result.title == "Updated PR title"
        self.mock_client.patch.assert_called_once_with(
            f"repos/{repo}/pulls/{pr_number}",
            data=update_data
        )

    @pytest.mark.asyncio
    async def test_close_pull_request_success(self, sample_pull_request_data):
        """Test successful pull request closing using update_pull_request."""
        repo = "testuser/test-repo"
        pr_number = 42

        closed_pr_data = sample_pull_request_data.copy()
        closed_pr_data.update({
            "state": "closed",
            "closed_at": "2023-12-01T12:00:00Z"
        })

        mock_response = APIResponse(
            status_code=200,
            data=closed_pr_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.patch.return_value = mock_response

        result = await self.pull_requests_api.update_pull_request(repo, pr_number, state="closed")

        assert isinstance(result, PullRequest)
        assert result.state == "closed"
        self.mock_client.patch.assert_called_once_with(
            f"repos/{repo}/pulls/{pr_number}",
            data={"state": "closed"}
        )

    @pytest.mark.asyncio
    async def test_merge_pull_request_success(self):
        """Test successful pull request merging."""
        repo = "testuser/test-repo"
        pr_number = 42

        commit_title = "Merge pull request #42"
        commit_message = "Add new feature"
        merge_method = "merge"

        merge_result = {
            "sha": "merged_commit_sha",
            "merged": True,
            "message": "Pull Request successfully merged"
        }

        mock_response = APIResponse(
            status_code=200,
            data=merge_result,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )

        self.mock_client.put.return_value = mock_response

        result = await self.pull_requests_api.merge_pull_request(
            repo, pr_number, commit_title, commit_message, merge_method
        )

        assert result["merged"] is True
        assert result["sha"] == "merged_commit_sha"

        expected_data = {
            "merge_method": merge_method,
            "commit_title": commit_title,
            "commit_message": commit_message
        }
        self.mock_client.put.assert_called_once_with(
            f"repos/{repo}/pulls/{pr_number}/merge",
            data=expected_data
        )

    @pytest.mark.asyncio
    async def test_merge_pull_request_conflict(self):
        """Test pull request merging with conflicts."""
        repo = "testuser/test-repo"
        pr_number = 42

        commit_title = "Merge pull request #42"
        merge_method = "merge"

        # Mock GitHubCLIError to be raised by the client
        self.mock_client.put.side_effect = GitHubCLIError("Failed to merge pull request: Pull Request is not mergeable")

        with pytest.raises(GitHubCLIError, match="Failed to merge pull request"):
            await self.pull_requests_api.merge_pull_request(repo, pr_number, commit_title, merge_method=merge_method)

    @pytest.mark.asyncio
    async def test_get_pull_request_files_success(self):
        """Test successful listing of pull request files."""
        repo = "testuser/test-repo"
        pr_number = 42

        files_data = [
            {
                "filename": "src/main.py",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
                "changes": 12,
                "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line"
            },
            {
                "filename": "tests/test_main.py",
                "status": "added",
                "additions": 20,
                "deletions": 0,
                "changes": 20,
                "patch": "@@ -0,0 +1,20 @@\n+new test file"
            }
        ]

        mock_response = APIResponse(
            status_code=200,
            data=files_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        self.mock_client.get.return_value = mock_response

        result = await self.pull_requests_api.get_pull_request_files(repo, pr_number)

        assert len(result) == 2
        assert result[0]["filename"] == "src/main.py"
        assert result[1]["status"] == "added"
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/pulls/{pr_number}/files")

    @pytest.mark.asyncio
    async def test_get_pull_request_reviews_success(self):
        """Test successful listing of pull request reviews."""
        repo = "testuser/test-repo"
        pr_number = 42

        reviews_data = [
            {
                "id": 123,
                "user": {"login": "reviewer1", "id": 111},
                "state": "APPROVED",
                "body": "Looks good to me!",
                "submitted_at": "2023-12-01T10:00:00Z"
            },
            {
                "id": 124,
                "user": {"login": "reviewer2", "id": 222},
                "state": "CHANGES_REQUESTED",
                "body": "Please fix the formatting issues.",
                "submitted_at": "2023-12-01T11:00:00Z"
            }
        ]

        mock_response = APIResponse(
            status_code=200,
            data=reviews_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        self.mock_client.get.return_value = mock_response

        result = await self.pull_requests_api.get_pull_request_reviews(repo, pr_number)

        assert len(result) == 2
        assert result[0]["state"] == "APPROVED"
        assert result[1]["state"] == "CHANGES_REQUESTED"
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/pulls/{pr_number}/reviews")

    @pytest.mark.asyncio
    async def test_create_review_success(self):
        """Test successful pull request review creation."""
        repo = "testuser/test-repo"
        pr_number = 42

        event = "APPROVE"
        body = "This looks great!"

        created_review = {
            "id": 125,
            "user": {"login": "reviewer", "id": 333},
            "state": "APPROVED",
            "body": body,
            "submitted_at": "2023-12-01T12:00:00Z"
        }

        mock_response = APIResponse(
            status_code=200,
            data=created_review,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        self.mock_client.post.return_value = mock_response

        result = await self.pull_requests_api.create_review(repo, pr_number, event, body)

        assert result["state"] == "APPROVED"
        assert result["body"] == body

        expected_data = {"event": event, "body": body}
        self.mock_client.post.assert_called_once_with(
            f"repos/{repo}/pulls/{pr_number}/reviews",
            data=expected_data
        )


