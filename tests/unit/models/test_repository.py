"""
Unit tests for Repository model.

Tests repository data model creation, validation, and methods.
"""

import pytest
from datetime import datetime, timezone

from github_cli.models.repository import Repository


def create_test_repository(**overrides):
    """Helper function to create a valid Repository for testing."""
    defaults = {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "private": False,
        "owner": {"id": 987654321, "login": "testuser", "type": "User"},
        "html_url": "https://github.com/testuser/test-repo",
        "description": "A test repository",
        "fork": False,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "pushed_at": "2023-12-01T12:00:00Z",
        "homepage": "https://example.com",
        "size": 1024,
        "stargazers_count": 42,
        "watchers_count": 42,
        "language": "Python",
        "forks_count": 5,
        "open_issues_count": 3,
        "license": {"key": "mit", "name": "MIT License"},
        "topics": ["python", "cli", "github"],
        "default_branch": "main",
        "visibility": "public",
        "url": "https://api.github.com/repos/testuser/test-repo",
        "archived": False,
        "disabled": False,
    }
    defaults.update(overrides)
    return Repository(**defaults)


@pytest.mark.unit
@pytest.mark.models
class TestRepository:
    """Test cases for Repository model."""

    def test_repository_creation_minimal(self):
        """Test Repository creation with minimal required fields."""
        repo = create_test_repository(
            id=123456789,
            name="minimal-repo",
            full_name="user/minimal-repo",
            private=False,
            description=None,
            homepage=None,
            language=None,
            license=None,
            topics=[]
        )
        
        assert repo.id == 123456789
        assert repo.name == "minimal-repo"
        assert repo.full_name == "user/minimal-repo"
        assert repo.private is False
        assert repo.fork is False
        assert repo.description is None
        assert repo.homepage is None
        assert repo.language is None
        assert repo.license is None
        assert repo.topics == []

    def test_repository_creation_full(self, sample_repository_data):
        """Test Repository creation with full data."""
        repo = Repository.from_json(sample_repository_data)
        
        assert repo.id == sample_repository_data["id"]
        assert repo.name == sample_repository_data["name"]
        assert repo.full_name == sample_repository_data["full_name"]
        assert repo.private == sample_repository_data["private"]
        assert repo.description == sample_repository_data["description"]
        assert repo.fork == sample_repository_data["fork"]
        assert repo.owner == sample_repository_data["owner"]

    def test_repository_optional_fields(self):
        """Test Repository with optional fields set to None."""
        repo = create_test_repository(
            description=None,
            homepage=None,
            language=None,
            license=None
        )
        
        assert repo.description is None
        assert repo.homepage is None
        assert repo.language is None
        assert repo.license is None

    def test_repository_boolean_fields(self):
        """Test Repository boolean fields."""
        # Test public repository
        public_repo = create_test_repository(
            private=False,
            fork=False,
            archived=False,
            disabled=False
        )
        
        assert public_repo.private is False
        assert public_repo.fork is False
        assert public_repo.archived is False
        assert public_repo.disabled is False
        
        # Test private forked repository
        private_fork = create_test_repository(
            private=True,
            fork=True,
            archived=True,
            disabled=True
        )
        
        assert private_fork.private is True
        assert private_fork.fork is True
        assert private_fork.archived is True
        assert private_fork.disabled is True

    def test_repository_numeric_fields(self):
        """Test Repository numeric fields."""
        repo = create_test_repository(
            size=2048,
            stargazers_count=100,
            watchers_count=95,
            forks_count=25,
            open_issues_count=10
        )
        
        assert repo.size == 2048
        assert repo.stargazers_count == 100
        assert repo.watchers_count == 95
        assert repo.forks_count == 25
        assert repo.open_issues_count == 10

    def test_repository_topics_handling(self):
        """Test Repository topics handling."""
        # Test with topics
        repo_with_topics = create_test_repository(
            topics=["python", "cli", "github", "api"]
        )
        
        assert len(repo_with_topics.topics) == 4
        assert "python" in repo_with_topics.topics
        assert "cli" in repo_with_topics.topics
        assert "github" in repo_with_topics.topics
        assert "api" in repo_with_topics.topics
        
        # Test without topics
        repo_no_topics = create_test_repository(topics=[])
        assert repo_no_topics.topics == []

    def test_repository_license_handling(self):
        """Test Repository license handling."""
        # Test with license
        mit_license = {"key": "mit", "name": "MIT License", "url": "https://api.github.com/licenses/mit"}
        repo_with_license = create_test_repository(license=mit_license)
        
        assert repo_with_license.license is not None
        assert repo_with_license.license["key"] == "mit"
        assert repo_with_license.license["name"] == "MIT License"
        
        # Test without license
        repo_no_license = create_test_repository(license=None)
        assert repo_no_license.license is None

    def test_repository_owner_handling(self):
        """Test Repository owner handling."""
        # Test user owner
        user_owner = {"id": 123, "login": "testuser", "type": "User"}
        user_repo = create_test_repository(owner=user_owner)
        
        assert user_repo.owner["type"] == "User"
        assert user_repo.owner["login"] == "testuser"
        
        # Test organization owner
        org_owner = {"id": 456, "login": "testorg", "type": "Organization"}
        org_repo = create_test_repository(owner=org_owner)
        
        assert org_repo.owner["type"] == "Organization"
        assert org_repo.owner["login"] == "testorg"
