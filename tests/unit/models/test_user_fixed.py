"""
Unit tests for User model.

Tests user data model creation, validation, and methods.
"""

import pytest
from datetime import datetime, timezone

from github_cli.models.user import User


def create_test_user(**overrides):
    """Helper function to create a valid User for testing."""
    defaults = {
        "id": 123456789,
        "login": "testuser",
        "node_id": "MDQ6VXNlcjEyMzQ1Njc4OQ==",
        "avatar_url": "https://avatars.githubusercontent.com/u/123456789",
        "gravatar_id": "",
        "url": "https://api.github.com/users/testuser",
        "html_url": "https://github.com/testuser",
        "followers_url": "https://api.github.com/users/testuser/followers",
        "following_url": "https://api.github.com/users/testuser/following{/other_user}",
        "gists_url": "https://api.github.com/users/testuser/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/testuser/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/testuser/subscriptions",
        "organizations_url": "https://api.github.com/users/testuser/orgs",
        "repos_url": "https://api.github.com/users/testuser/repos",
        "events_url": "https://api.github.com/users/testuser/events{/privacy}",
        "received_events_url": "https://api.github.com/users/testuser/received_events",
        "type": "User",
        "site_admin": False,
        "name": "Test User",
        "company": "Test Company",
        "blog": "https://testuser.dev",
        "location": "Test City",
        "email": "test@example.com",
        "hireable": True,
        "bio": "A test user",
        "twitter_username": "testuser",
        "public_repos": 10,
        "public_gists": 5,
        "followers": 100,
        "following": 50,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "private_gists": 2,
        "total_private_repos": 3,
        "owned_private_repos": 3,
        "disk_usage": 1024,
        "collaborators": 5,
    }
    defaults.update(overrides)
    return User(**defaults)


@pytest.mark.unit
@pytest.mark.models
class TestUser:
    """Test cases for User model."""

    def test_user_creation_minimal(self):
        """Test User creation with minimal required fields."""
        user = create_test_user(
            id=123456789,
            login="minimaluser",
            name=None,
            company=None,
            blog=None,
            location=None,
            email=None,
            hireable=None,
            bio=None,
            twitter_username=None
        )
        
        assert user.id == 123456789
        assert user.login == "minimaluser"
        assert user.type == "User"
        assert user.site_admin is False
        assert user.name is None
        assert user.company is None
        assert user.blog is None
        assert user.location is None
        assert user.email is None
        assert user.hireable is None
        assert user.bio is None
        assert user.twitter_username is None

    def test_user_creation_full(self, sample_user_data):
        """Test User creation with full data."""
        user = User.from_json(sample_user_data)
        
        assert user.id == sample_user_data["id"]
        assert user.login == sample_user_data["login"]
        assert user.name == sample_user_data["name"]
        assert user.email == sample_user_data["email"]
        assert user.bio == sample_user_data["bio"]
        assert user.company == sample_user_data["company"]
        assert user.location == sample_user_data["location"]
        assert user.blog == sample_user_data["blog"]
        assert user.twitter_username == sample_user_data["twitter_username"]

    def test_user_optional_fields_none(self):
        """Test User with optional fields set to None."""
        user = create_test_user(
            name=None,
            company=None,
            blog=None,
            location=None,
            email=None,
            hireable=None,
            bio=None,
            twitter_username=None
        )
        
        assert user.name is None
        assert user.company is None
        assert user.blog is None
        assert user.location is None
        assert user.email is None
        assert user.hireable is None
        assert user.bio is None
        assert user.twitter_username is None

    def test_user_type_user(self):
        """Test User with type 'User'."""
        user = create_test_user(type="User", site_admin=False)
        
        assert user.type == "User"
        assert user.site_admin is False

    def test_user_type_organization(self):
        """Test User with type 'Organization'."""
        user = create_test_user(
            login="testorg",
            type="Organization",
            site_admin=False
        )
        
        assert user.type == "Organization"
        assert user.login == "testorg"
        assert user.site_admin is False

    def test_user_site_admin(self):
        """Test User with site_admin privileges."""
        admin_user = create_test_user(site_admin=True)
        regular_user = create_test_user(site_admin=False)
        
        assert admin_user.site_admin is True
        assert regular_user.site_admin is False

    def test_user_statistics_defaults(self):
        """Test User statistics with default values."""
        user = create_test_user()
        
        assert user.public_repos >= 0
        assert user.public_gists >= 0
        assert user.followers >= 0
        assert user.following >= 0
        assert user.private_gists >= 0
        assert user.total_private_repos >= 0
        assert user.owned_private_repos >= 0
        assert user.disk_usage >= 0
        assert user.collaborators >= 0

    def test_user_statistics_custom_values(self):
        """Test User statistics with custom values."""
        user = create_test_user(
            public_repos=25,
            public_gists=10,
            followers=500,
            following=100,
            private_gists=5,
            total_private_repos=8,
            owned_private_repos=8,
            disk_usage=2048,
            collaborators=10
        )
        
        assert user.public_repos == 25
        assert user.public_gists == 10
        assert user.followers == 500
        assert user.following == 100
        assert user.private_gists == 5
        assert user.total_private_repos == 8
        assert user.owned_private_repos == 8
        assert user.disk_usage == 2048
        assert user.collaborators == 10

    def test_user_profile_information(self):
        """Test User profile information."""
        user = create_test_user(
            name="John Doe",
            company="Acme Corp",
            blog="https://johndoe.dev",
            location="San Francisco, CA",
            email="john@example.com",
            bio="Software developer and open source enthusiast",
            twitter_username="johndoe",
            hireable=True
        )
        
        assert user.name == "John Doe"
        assert user.company == "Acme Corp"
        assert user.blog == "https://johndoe.dev"
        assert user.location == "San Francisco, CA"
        assert user.email == "john@example.com"
        assert user.bio == "Software developer and open source enthusiast"
        assert user.twitter_username == "johndoe"
        assert user.hireable is True

    def test_user_urls_validation(self):
        """Test User URL fields."""
        user = create_test_user(
            login="urluser",
            html_url="https://github.com/urluser",
            url="https://api.github.com/users/urluser",
            avatar_url="https://avatars.githubusercontent.com/u/123456789"
        )
        
        assert user.html_url == "https://github.com/urluser"
        assert user.url == "https://api.github.com/users/urluser"
        assert user.avatar_url == "https://avatars.githubusercontent.com/u/123456789"
        assert "github.com" in user.html_url
        assert "api.github.com" in user.url

    def test_user_timestamps(self):
        """Test User timestamp fields."""
        user = create_test_user(
            created_at="2020-01-01T00:00:00Z",
            updated_at="2023-12-01T00:00:00Z"
        )
        
        assert user.created_at == "2020-01-01T00:00:00Z"
        assert user.updated_at == "2023-12-01T00:00:00Z"

    def test_user_equality(self):
        """Test User equality comparison."""
        user1 = create_test_user(id=123, login="user1")
        user2 = create_test_user(id=123, login="user1")
        user3 = create_test_user(id=456, login="user2")
        
        # Users with same id and login should be considered equal
        assert user1.id == user2.id
        assert user1.login == user2.login
        assert user1.id != user3.id
        assert user1.login != user3.login

    def test_user_string_representation(self):
        """Test User string representation."""
        user = create_test_user(login="testuser", name="Test User")
        
        # The string representation should contain the login
        user_str = str(user)
        assert "testuser" in user_str

    def test_user_private_information_fields(self):
        """Test User private information fields."""
        user = create_test_user(
            private_gists=3,
            total_private_repos=5,
            owned_private_repos=4,
            disk_usage=1536,
            collaborators=8
        )
        
        assert user.private_gists == 3
        assert user.total_private_repos == 5
        assert user.owned_private_repos == 4
        assert user.disk_usage == 1536
        assert user.collaborators == 8
