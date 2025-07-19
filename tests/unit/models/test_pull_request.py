"""
Unit tests for PullRequest model.

Tests pull request data model creation, validation, and methods.
"""

import pytest
from datetime import datetime, timezone

from github_cli.models.pull_request import PullRequest


@pytest.mark.unit
@pytest.mark.models
class TestPullRequest:
    """Test cases for PullRequest model."""

    def test_pull_request_creation_minimal(self):
        """Test PullRequest creation with minimal required fields."""
        pr = PullRequest(
            id=555666777,
            number=42,
            title="Add new feature",
            body="This PR adds a new feature to the application.",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/testuser/test-repo/pull/42",
            diff_url="https://github.com/testuser/test-repo/pull/42.diff",
            patch_url="https://github.com/testuser/test-repo/pull/42.patch",
            created_at="2023-11-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
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
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=10,
            deletions=2,
            changed_files=1
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
        pr = PullRequest(**sample_pull_request_data)
        
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
        pr = PullRequest(
            id=123,
            number=1,
            title="Open PR",
            body="This is an open PR",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert pr.state == "open"
        assert pr.closed_at is None
        assert pr.merged_at is None
        assert pr.merged is False

    def test_pull_request_state_closed(self):
        """Test PullRequest with closed state."""
        pr = PullRequest(
            id=123,
            number=1,
            title="Closed PR",
            body="This is a closed PR",
            state="closed",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T12:00:00Z",
            closed_at="2023-12-01T12:00:00Z",
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=None,
            mergeable_state="unknown",
            merged=False,
            comments=2,
            review_comments=1,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert pr.state == "closed"
        assert pr.closed_at == "2023-12-01T12:00:00Z"
        assert pr.merged is False

    def test_pull_request_state_merged(self):
        """Test PullRequest with merged state."""
        pr = PullRequest(
            id=123,
            number=1,
            title="Merged PR",
            body="This is a merged PR",
            state="closed",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T12:00:00Z",
            closed_at="2023-12-01T12:00:00Z",
            merged_at="2023-12-01T12:00:00Z",
            merge_commit_sha="merged123abc",
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=None,
            mergeable_state="unknown",
            merged=True,
            comments=3,
            review_comments=2,
            commits=2,
            additions=15,
            deletions=3,
            changed_files=2
        )
        
        assert pr.state == "closed"
        assert pr.merged is True
        assert pr.merged_at == "2023-12-01T12:00:00Z"
        assert pr.merge_commit_sha == "merged123abc"

    def test_pull_request_draft(self):
        """Test PullRequest with draft status."""
        pr = PullRequest(
            id=123,
            number=1,
            title="Draft PR",
            body="This is a draft PR",
            state="open",
            draft=True,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert pr.draft is True
        assert pr.state == "open"

    def test_pull_request_with_assignees(self):
        """Test PullRequest with assignees."""
        assignees = [
            {"id": 111, "login": "assignee1", "type": "User"},
            {"id": 222, "login": "assignee2", "type": "User"}
        ]
        
        pr = PullRequest(
            id=123,
            number=1,
            title="PR with assignees",
            body="This PR has assignees",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=assignees,
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
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
        
        pr = PullRequest(
            id=123,
            number=1,
            title="PR with reviewers",
            body="This PR has requested reviewers",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=reviewers,
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert len(pr.requested_reviewers) == 2
        assert pr.requested_reviewers[0]["login"] == "reviewer1"
        assert pr.requested_reviewers[1]["login"] == "reviewer2"

    def test_pull_request_with_labels(self):
        """Test PullRequest with labels."""
        labels = [
            {"name": "bug", "color": "d73a4a"},
            {"name": "enhancement", "color": "a2eeef"},
            {"name": "priority-high", "color": "ff0000"}
        ]
        
        pr = PullRequest(
            id=123,
            number=1,
            title="PR with labels",
            body="This PR has labels",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=labels,
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert len(pr.labels) == 3
        assert pr.labels[0]["name"] == "bug"
        assert pr.labels[1]["name"] == "enhancement"
        assert pr.labels[2]["name"] == "priority-high"

    def test_pull_request_with_milestone(self):
        """Test PullRequest with milestone."""
        milestone = {
            "id": 555,
            "number": 1,
            "title": "v1.0.0",
            "description": "First major release",
            "state": "open"
        }
        
        pr = PullRequest(
            id=123,
            number=1,
            title="PR with milestone",
            body="This PR has a milestone",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=milestone,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert pr.milestone is not None
        assert pr.milestone["title"] == "v1.0.0"
        assert pr.milestone["state"] == "open"

    def test_pull_request_head_and_base(self):
        """Test PullRequest head and base branch information."""
        head = {
            "ref": "feature/new-feature",
            "sha": "abc123def456",
            "repo": {
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "owner": {"login": "testuser"}
            }
        }
        
        base = {
            "ref": "main",
            "sha": "def456abc123",
            "repo": {
                "name": "test-repo",
                "full_name": "testuser/test-repo",
                "owner": {"login": "testuser"}
            }
        }
        
        pr = PullRequest(
            id=123,
            number=1,
            title="Feature PR",
            body="This PR adds a new feature",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/testuser/test-repo/pull/1",
            diff_url="https://github.com/testuser/test-repo/pull/1.diff",
            patch_url="https://github.com/testuser/test-repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head=head,
            base=base,
            user={"id": 1, "login": "testuser", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=0,
            review_comments=0,
            commits=1,
            additions=5,
            deletions=1,
            changed_files=1
        )
        
        assert pr.head["ref"] == "feature/new-feature"
        assert pr.head["sha"] == "abc123def456"
        assert pr.base["ref"] == "main"
        assert pr.base["sha"] == "def456abc123"

    def test_pull_request_statistics(self):
        """Test PullRequest statistics fields."""
        pr = PullRequest(
            id=123,
            number=1,
            title="PR with stats",
            body="This PR has statistics",
            state="open",
            draft=False,
            locked=False,
            html_url="https://github.com/user/repo/pull/1",
            diff_url="https://github.com/user/repo/pull/1.diff",
            patch_url="https://github.com/user/repo/pull/1.patch",
            created_at="2023-12-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            closed_at=None,
            merged_at=None,
            merge_commit_sha=None,
            assignees=[],
            requested_reviewers=[],
            labels=[],
            milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True,
            mergeable_state="clean",
            merged=False,
            comments=5,
            review_comments=3,
            commits=4,
            additions=100,
            deletions=25,
            changed_files=8
        )
        
        assert pr.comments == 5
        assert pr.review_comments == 3
        assert pr.commits == 4
        assert pr.additions == 100
        assert pr.deletions == 25
        assert pr.changed_files == 8

    def test_pull_request_mergeable_states(self):
        """Test PullRequest mergeable states."""
        # Clean state
        pr_clean = PullRequest(
            id=123, number=1, title="Clean PR", body="", state="open", draft=False, locked=False,
            html_url="https://github.com/user/repo/pull/1", diff_url="", patch_url="",
            created_at="2023-12-01T00:00:00Z", updated_at="2023-12-01T00:00:00Z",
            closed_at=None, merged_at=None, merge_commit_sha=None,
            assignees=[], requested_reviewers=[], labels=[], milestone=None,
            head={"ref": "feature", "sha": "abc123", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=True, mergeable_state="clean", merged=False,
            comments=0, review_comments=0, commits=1, additions=5, deletions=1, changed_files=1
        )
        
        assert pr_clean.mergeable is True
        assert pr_clean.mergeable_state == "clean"
        
        # Dirty state
        pr_dirty = PullRequest(
            id=124, number=2, title="Dirty PR", body="", state="open", draft=False, locked=False,
            html_url="https://github.com/user/repo/pull/2", diff_url="", patch_url="",
            created_at="2023-12-01T00:00:00Z", updated_at="2023-12-01T00:00:00Z",
            closed_at=None, merged_at=None, merge_commit_sha=None,
            assignees=[], requested_reviewers=[], labels=[], milestone=None,
            head={"ref": "feature2", "sha": "abc124", "repo": {"name": "repo", "full_name": "user/repo"}},
            base={"ref": "main", "sha": "def456", "repo": {"name": "repo", "full_name": "user/repo"}},
            user={"id": 1, "login": "user", "type": "User"},
            mergeable=False, mergeable_state="dirty", merged=False,
            comments=0, review_comments=0, commits=1, additions=5, deletions=1, changed_files=1
        )
        
        assert pr_dirty.mergeable is False
        assert pr_dirty.mergeable_state == "dirty"
