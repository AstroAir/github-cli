"""
Unit tests for Repository model.

Tests repository data model creation, validation, and methods.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from github_cli.models.repository import Repository


@pytest.mark.unit
@pytest.mark.models
class TestRepository:
    """Test cases for Repository model."""

    def test_repository_creation_minimal(self):
        """Test Repository creation with minimal required fields."""
        repo = Repository(
            id=123456789,
            name="test-repo",
            full_name="testuser/test-repo",
            description="A test repository",
            private=False,
            fork=False,
            html_url="https://github.com/testuser/test-repo",
            clone_url="https://github.com/testuser/test-repo.git",
            ssh_url="git@github.com:testuser/test-repo.git",
            homepage="https://example.com",
            stargazers_count=42,
            watchers_count=42,
            forks_count=5,
            open_issues_count=3,
            size=1024,
            language="Python",
            topics=["python", "cli"],
            license={"key": "mit", "name": "MIT License"},
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            pushed_at="2023-12-01T12:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 987654321, "login": "testuser", "type": "User"}
        )
        
        assert repo.id == 123456789
        assert repo.name == "test-repo"
        assert repo.full_name == "testuser/test-repo"
        assert repo.description == "A test repository"
        assert repo.private is False
        assert repo.fork is False
        assert repo.language == "Python"
        assert repo.topics == ["python", "cli"]
        assert repo.default_branch == "main"
        assert repo.visibility == "public"
        assert repo.archived is False
        assert repo.disabled is False

    def test_repository_creation_full(self, sample_repository_data):
        """Test Repository creation with full data."""
        repo = Repository(**sample_repository_data)
        
        assert repo.id == sample_repository_data["id"]
        assert repo.name == sample_repository_data["name"]
        assert repo.full_name == sample_repository_data["full_name"]
        assert repo.description == sample_repository_data["description"]
        assert repo.stargazers_count == sample_repository_data["stargazers_count"]
        assert repo.forks_count == sample_repository_data["forks_count"]
        assert repo.owner == sample_repository_data["owner"]

    def test_repository_optional_fields(self):
        """Test Repository with optional fields set to None."""
        repo = Repository(
            id=123,
            name="test",
            full_name="user/test",
            description=None,  # Optional field
            private=False,
            fork=False,
            html_url="https://github.com/user/test",
            clone_url="https://github.com/user/test.git",
            ssh_url="git@github.com:user/test.git",
            homepage=None,  # Optional field
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language=None,  # Optional field
            topics=[],
            license=None,  # Optional field
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert repo.description is None
        assert repo.homepage is None
        assert repo.language is None
        assert repo.license is None
        assert repo.topics == []

    def test_repository_boolean_fields(self):
        """Test Repository boolean field handling."""
        # Test private repository
        private_repo = Repository(
            id=123,
            name="private-repo",
            full_name="user/private-repo",
            description="Private repository",
            private=True,
            fork=False,
            html_url="https://github.com/user/private-repo",
            clone_url="https://github.com/user/private-repo.git",
            ssh_url="git@github.com:user/private-repo.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="Python",
            topics=[],
            license=None,
            default_branch="main",
            visibility="private",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert private_repo.private is True
        assert private_repo.visibility == "private"

        # Test forked repository
        fork_repo = Repository(
            id=456,
            name="forked-repo",
            full_name="user/forked-repo",
            description="Forked repository",
            private=False,
            fork=True,
            html_url="https://github.com/user/forked-repo",
            clone_url="https://github.com/user/forked-repo.git",
            ssh_url="git@github.com:user/forked-repo.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="JavaScript",
            topics=[],
            license=None,
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=True,
            disabled=True,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert fork_repo.fork is True
        assert fork_repo.archived is True
        assert fork_repo.disabled is True

    def test_repository_numeric_fields(self):
        """Test Repository numeric field handling."""
        repo = Repository(
            id=999999999,
            name="popular-repo",
            full_name="user/popular-repo",
            description="Very popular repository",
            private=False,
            fork=False,
            html_url="https://github.com/user/popular-repo",
            clone_url="https://github.com/user/popular-repo.git",
            ssh_url="git@github.com:user/popular-repo.git",
            homepage=None,
            stargazers_count=50000,
            watchers_count=50000,
            forks_count=10000,
            open_issues_count=500,
            size=102400,  # 100MB
            language="Python",
            topics=["python", "machine-learning", "ai"],
            license={"key": "apache-2.0", "name": "Apache License 2.0"},
            default_branch="main",
            visibility="public",
            created_at="2020-01-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z",
            pushed_at="2023-12-01T12:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert repo.stargazers_count == 50000
        assert repo.watchers_count == 50000
        assert repo.forks_count == 10000
        assert repo.open_issues_count == 500
        assert repo.size == 102400

    def test_repository_topics_handling(self):
        """Test Repository topics field handling."""
        # Empty topics
        repo_no_topics = Repository(
            id=123,
            name="no-topics",
            full_name="user/no-topics",
            description="Repository with no topics",
            private=False,
            fork=False,
            html_url="https://github.com/user/no-topics",
            clone_url="https://github.com/user/no-topics.git",
            ssh_url="git@github.com:user/no-topics.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="Python",
            topics=[],
            license=None,
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert repo_no_topics.topics == []

        # Multiple topics
        repo_with_topics = Repository(
            id=456,
            name="with-topics",
            full_name="user/with-topics",
            description="Repository with multiple topics",
            private=False,
            fork=False,
            html_url="https://github.com/user/with-topics",
            clone_url="https://github.com/user/with-topics.git",
            ssh_url="git@github.com:user/with-topics.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="Python",
            topics=["python", "web", "api", "rest", "json"],
            license=None,
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert len(repo_with_topics.topics) == 5
        assert "python" in repo_with_topics.topics
        assert "api" in repo_with_topics.topics

    def test_repository_license_handling(self):
        """Test Repository license field handling."""
        # Repository with license
        repo_with_license = Repository(
            id=123,
            name="licensed-repo",
            full_name="user/licensed-repo",
            description="Repository with license",
            private=False,
            fork=False,
            html_url="https://github.com/user/licensed-repo",
            clone_url="https://github.com/user/licensed-repo.git",
            ssh_url="git@github.com:user/licensed-repo.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="Python",
            topics=[],
            license={
                "key": "mit",
                "name": "MIT License",
                "spdx_id": "MIT",
                "url": "https://api.github.com/licenses/mit"
            },
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={"id": 1, "login": "user", "type": "User"}
        )
        
        assert repo_with_license.license is not None
        assert repo_with_license.license["key"] == "mit"
        assert repo_with_license.license["name"] == "MIT License"

    def test_repository_owner_handling(self):
        """Test Repository owner field handling."""
        # User owner
        user_repo = Repository(
            id=123,
            name="user-repo",
            full_name="testuser/user-repo",
            description="Repository owned by user",
            private=False,
            fork=False,
            html_url="https://github.com/testuser/user-repo",
            clone_url="https://github.com/testuser/user-repo.git",
            ssh_url="git@github.com:testuser/user-repo.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="Python",
            topics=[],
            license=None,
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={
                "id": 987654321,
                "login": "testuser",
                "type": "User",
                "site_admin": False,
                "avatar_url": "https://avatars.githubusercontent.com/u/987654321"
            }
        )
        
        assert user_repo.owner["type"] == "User"
        assert user_repo.owner["login"] == "testuser"

        # Organization owner
        org_repo = Repository(
            id=456,
            name="org-repo",
            full_name="testorg/org-repo",
            description="Repository owned by organization",
            private=False,
            fork=False,
            html_url="https://github.com/testorg/org-repo",
            clone_url="https://github.com/testorg/org-repo.git",
            ssh_url="git@github.com:testorg/org-repo.git",
            homepage=None,
            stargazers_count=0,
            watchers_count=0,
            forks_count=0,
            open_issues_count=0,
            size=0,
            language="Python",
            topics=[],
            license=None,
            default_branch="main",
            visibility="public",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            pushed_at="2023-01-01T00:00:00Z",
            archived=False,
            disabled=False,
            owner={
                "id": 123456789,
                "login": "testorg",
                "type": "Organization",
                "site_admin": False,
                "avatar_url": "https://avatars.githubusercontent.com/u/123456789"
            }
        )
        
        assert org_repo.owner["type"] == "Organization"
        assert org_repo.owner["login"] == "testorg"
