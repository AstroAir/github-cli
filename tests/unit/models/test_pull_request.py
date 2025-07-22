"""
Unit tests for PullRequest model.

Tests pull request data model creation, validation, and methods.
"""

import pytest
from datetime import datetime, timezone

from github_cli.models.pull_request import PullRequest


def create_test_pull_request(**overrides):
    """Helper function to create a valid PullRequest for testing."""
    defaults = {
        # Issue fields
        "id": 123,
        "number": 1,
        "title": "Test PR",
        "state": "open",
        "locked": False,
        "assignee": None,
        "assignees": [],
        "milestone": None,
        "comments": 0,
        "created_at": "2023-12-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "closed_at": None,
        "author_association": "OWNER",
        "body": "Test PR body",
        "user": {"id": 1, "login": "user", "type": "User"},
        "labels": [],
        "html_url": "https://github.com/user/repo/pull/1",
        "url": "https://api.github.com/repos/user/repo/issues/1",
        "repository_url": "https://api.github.com/repos/user/repo",
        # PullRequest specific fields
        "head": {"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
        "base": {"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
        "merged": False,
        "mergeable": True,
        "mergeable_state": "clean",
        "merged_by": None,
        "merged_at": None,
        "draft": False,
        "requested_reviewers": [],
        "requested_teams": [],
    }
    defaults.update(overrides)
    return PullRequest(**defaults)


@pytest.mark.unit
@pytest.mark.models
class TestPullRequest:
    """Test cases for PullRequest model."""

    def test_pull_request_creation_minimal(self):
        """Test PullRequest creation with minimal required fields."""
        pr = create_test_pull_request(
            id=555666777,
            number=42,
            title="Add new feature",
            body="This PR adds a new feature to the application.",
            state="open",
            head={
                "ref": "feature-branch",
                "sha": "abc123def456",
                "repo": {"name": "test-repo", "full_name": "testuser/test-repo"}
            },
            base={
                "ref": "main",
                "sha": "def456abc123",
                "repo": {"name": "test-repo", "full_name": "testuser/test-repo"}
            },
            user={"id": 987654321, "login": "testuser", "type": "User"},
        )
        
        assert pr.id == 555666777
        assert pr.number == 42
        assert pr.title == "Add new feature"
        assert pr.state == "open"
        assert pr.draft is False
        assert pr.locked is False
        assert pr.merged is False
        assert pr.mergeable is True
        assert pr.mergeable_state == "clean"

    def test_pull_request_creation_full(self, sample_pull_request_data):
        """Test PullRequest creation with full data."""
        pr = PullRequest.from_json(sample_pull_request_data)
        
        assert pr.id == sample_pull_request_data["id"]
        assert pr.number == sample_pull_request_data["number"]
        assert pr.title == sample_pull_request_data["title"]
        assert pr.body == sample_pull_request_data["body"]
        assert pr.state == sample_pull_request_data["state"]
        assert pr.head == sample_pull_request_data["head"]
        assert pr.base == sample_pull_request_data["base"]
        assert pr.user == sample_pull_request_data["user"]

    def test_pull_request_state_open(self):
        """Test PullRequest with open state."""
        pr = create_test_pull_request(
            title="Open PR",
            body="This is an open PR",
            state="open"
        )
        
        assert pr.state == "open"
        assert pr.closed_at is None
        assert pr.merged_at is None
        assert pr.merged is False

    def test_pull_request_state_closed(self):
        """Test PullRequest with closed state."""
        pr = create_test_pull_request(
            title="Closed PR",
            body="This is a closed PR",
            state="closed",
            closed_at="2023-12-01T12:00:00Z",
            updated_at="2023-12-01T12:00:00Z",
            mergeable=None,
            mergeable_state="unknown",
            comments=2
        )
        
        assert pr.state == "closed"
        assert pr.closed_at == "2023-12-01T12:00:00Z"
        assert pr.merged is False

    def test_pull_request_state_merged(self):
        """Test PullRequest with merged state."""
        pr = create_test_pull_request(
            title="Merged PR",
            body="This is a merged PR",
            state="closed",
            updated_at="2023-12-01T12:00:00Z",
            closed_at="2023-12-01T12:00:00Z",
            merged_at="2023-12-01T12:00:00Z",
            merged=True,
            mergeable=None,
            mergeable_state="unknown",
            comments=3
        )
        
        assert pr.state == "closed"
        assert pr.merged is True
        assert pr.merged_at == "2023-12-01T12:00:00Z"

    def test_pull_request_draft(self):
        """Test PullRequest with draft status."""
        pr = create_test_pull_request(
            title="Draft PR",
            body="This is a draft PR",
            state="open",
            draft=True
        )
        
        assert pr.draft is True
        assert pr.state == "open"

    def test_pull_request_with_assignees(self):
        """Test PullRequest with assignees."""
        assignees = [
            {"id": 111, "login": "assignee1", "type": "User"},
            {"id": 222, "login": "assignee2", "type": "User"}
        ]
        pr = create_test_pull_request(
            title="PR with assignees",
            assignees=assignees
        )
        
        assert len(pr.assignees) == 2
        assert pr.assignees[0]["login"] == "assignee1"
        assert pr.assignees[1]["login"] == "assignee2"

    def test_pull_request_with_reviewers(self):
        """Test PullRequest with requested reviewers."""
        reviewers = [
            {"id": 333, "login": "reviewer1", "type": "User"},
            {"id": 444, "login": "reviewer2", "type": "User"}
        ]
        pr = create_test_pull_request(
            title="PR with reviewers",
            requested_reviewers=reviewers
        )
        
        assert len(pr.requested_reviewers) == 2
        assert pr.requested_reviewers[0]["login"] == "reviewer1"
        assert pr.requested_reviewers[1]["login"] == "reviewer2"

    def test_pull_request_with_labels(self):
        """Test PullRequest with labels."""
        labels = [
            {"id": 1, "name": "bug", "color": "d73a4a"},
            {"id": 2, "name": "enhancement", "color": "a2eeef"}
        ]
        pr = create_test_pull_request(
            title="PR with labels",
            labels=labels
        )
        
        assert len(pr.labels) == 2
        assert pr.labels[0]["name"] == "bug"
        assert pr.labels[1]["name"] == "enhancement"

    def test_pull_request_with_milestone(self):
        """Test PullRequest with milestone."""
        milestone = {
            "id": 1,
            "title": "v1.0.0",
            "description": "First major release",
            "state": "open"
        }
        pr = create_test_pull_request(
            title="PR with milestone",
            milestone=milestone
        )
        
        assert pr.milestone is not None
        assert pr.milestone["title"] == "v1.0.0"
        assert pr.milestone["state"] == "open"

    def test_pull_request_head_and_base(self):
        """Test PullRequest head and base branch information."""
        pr = create_test_pull_request(
            head={"ref": "feature-branch", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}}
        )
        
        assert pr.head["ref"] == "feature-branch"
        assert pr.head["sha"] == "abc123"
        assert pr.base["ref"] == "main"
        assert pr.base["sha"] == "def456"

    def test_pull_request_mergeable_states(self):
        """Test PullRequest mergeable states."""
        # Test clean state
        pr_clean = create_test_pull_request(mergeable=True, mergeable_state="clean")
        assert pr_clean.mergeable is True
        assert pr_clean.mergeable_state == "clean"
        
        # Test conflicted state
        pr_conflict = create_test_pull_request(mergeable=False, mergeable_state="dirty")
        assert pr_conflict.mergeable is False
        assert pr_conflict.mergeable_state == "dirty"
        
        # Test unknown state
        pr_unknown = create_test_pull_request(mergeable=None, mergeable_state="unknown")
        assert pr_unknown.mergeable is None
        assert pr_unknown.mergeable_state == "unknown"
