"""
Unit tests for User model.

Tests user data model creation, validation, and methods.
"""

import pytest
from datetime import datetime, timezone

from github_cli.models.user import User


@pytest.mark.unit
@pytest.mark.models
class TestUser:
    """Test cases for User model."""

    def test_user_creation_minimal(self):
        """Test User creation with minimal required fields."""
        user = User(
            id=987654321,
            login="testuser",
            node_id="MDQ6VXNlcjk4NzY1NDMyMQ==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/987654321",
            html_url="https://github.com/testuser",
            url="https://api.github.com/users/testuser"
        )
        
        assert user.id == 987654321
        assert user.login == "testuser"
        assert user.node_id == "MDQ6VXNlcjk4NzY1NDMyMQ=="
        assert user.type == "User"
        assert user.site_admin is False
        assert user.avatar_url == "https://avatars.githubusercontent.com/u/987654321"
        assert user.html_url == "https://github.com/testuser"
        assert user.url == "https://api.github.com/users/testuser"

    def test_user_creation_full(self, sample_user_data):
        """Test User creation with full data."""
        user = User(**sample_user_data)
        
        assert user.id == sample_user_data["id"]
        assert user.login == sample_user_data["login"]
        assert user.name == sample_user_data["name"]
        assert user.email == sample_user_data["email"]
        assert user.bio == sample_user_data["bio"]
        assert user.company == sample_user_data["company"]
        assert user.location == sample_user_data["location"]
        assert user.blog == sample_user_data["blog"]
        assert user.twitter_username == sample_user_data["twitter_username"]
        assert user.public_repos == sample_user_data["public_repos"]
        assert user.followers == sample_user_data["followers"]
        assert user.following == sample_user_data["following"]

    def test_user_optional_fields_none(self):
        """Test User with optional fields set to None."""
        user = User(
            id=123,
            login="minimal_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/minimal_user",
            url="https://api.github.com/users/minimal_user",
            name=None,
            email=None,
            bio=None,
            company=None,
            location=None,
            blog=None,
            twitter_username=None
        )
        
        assert user.name is None
        assert user.email is None
        assert user.bio is None
        assert user.company is None
        assert user.location is None
        assert user.blog is None
        assert user.twitter_username is None

    def test_user_type_user(self):
        """Test User with type 'User'."""
        user = User(
            id=123,
            login="regular_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/regular_user",
            url="https://api.github.com/users/regular_user"
        )
        
        assert user.type == "User"
        assert user.site_admin is False

    def test_user_type_organization(self):
        """Test User with type 'Organization'."""
        org = User(
            id=456,
            login="test_org",
            node_id="MDEyOk9yZ2FuaXphdGlvbjQ1Ng==",
            type="Organization",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/456",
            html_url="https://github.com/test_org",
            url="https://api.github.com/orgs/test_org"
        )
        
        assert org.type == "Organization"
        assert org.login == "test_org"

    def test_user_site_admin(self):
        """Test User with site_admin=True."""
        admin_user = User(
            id=789,
            login="admin_user",
            node_id="MDQ6VXNlcjc4OQ==",
            type="User",
            site_admin=True,
            avatar_url="https://avatars.githubusercontent.com/u/789",
            html_url="https://github.com/admin_user",
            url="https://api.github.com/users/admin_user"
        )
        
        assert admin_user.site_admin is True

    def test_user_statistics_defaults(self):
        """Test User statistics with default values."""
        user = User(
            id=123,
            login="new_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/new_user",
            url="https://api.github.com/users/new_user"
        )
        
        assert user.public_repos == 0
        assert user.public_gists == 0
        assert user.followers == 0
        assert user.following == 0
        assert user.private_gists == 0
        assert user.total_private_repos == 0
        assert user.owned_private_repos == 0
        assert user.disk_usage == 0
        assert user.collaborators == 0
        assert user.two_factor_authentication is False

    def test_user_statistics_custom_values(self):
        """Test User statistics with custom values."""
        user = User(
            id=123,
            login="active_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/active_user",
            url="https://api.github.com/users/active_user",
            public_repos=50,
            public_gists=25,
            followers=1000,
            following=500,
            private_gists=10,
            total_private_repos=20,
            owned_private_repos=15,
            disk_usage=1024000,  # 1GB
            collaborators=5,
            two_factor_authentication=True
        )
        
        assert user.public_repos == 50
        assert user.public_gists == 25
        assert user.followers == 1000
        assert user.following == 500
        assert user.private_gists == 10
        assert user.total_private_repos == 20
        assert user.owned_private_repos == 15
        assert user.disk_usage == 1024000
        assert user.collaborators == 5
        assert user.two_factor_authentication is True

    def test_user_profile_information(self):
        """Test User profile information fields."""
        user = User(
            id=123,
            login="profile_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/profile_user",
            url="https://api.github.com/users/profile_user",
            name="Profile User",
            email="profile@example.com",
            bio="I'm a software developer passionate about open source.",
            company="Tech Company Inc.",
            location="San Francisco, CA",
            blog="https://profileuser.dev",
            twitter_username="profile_user"
        )
        
        assert user.name == "Profile User"
        assert user.email == "profile@example.com"
        assert user.bio == "I'm a software developer passionate about open source."
        assert user.company == "Tech Company Inc."
        assert user.location == "San Francisco, CA"
        assert user.blog == "https://profileuser.dev"
        assert user.twitter_username == "profile_user"

    def test_user_urls_validation(self):
        """Test User URL fields."""
        user = User(
            id=123,
            login="url_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123?v=4",
            html_url="https://github.com/url_user",
            url="https://api.github.com/users/url_user"
        )
        
        assert user.avatar_url.startswith("https://avatars.githubusercontent.com/")
        assert user.html_url.startswith("https://github.com/")
        assert user.url.startswith("https://api.github.com/")

    def test_user_timestamps(self):
        """Test User timestamp fields."""
        user = User(
            id=123,
            login="timestamp_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/timestamp_user",
            url="https://api.github.com/users/timestamp_user",
            created_at="2020-01-01T00:00:00Z",
            updated_at="2023-12-01T12:00:00Z"
        )
        
        assert user.created_at == "2020-01-01T00:00:00Z"
        assert user.updated_at == "2023-12-01T12:00:00Z"

    def test_user_equality(self):
        """Test User equality comparison."""
        user1 = User(
            id=123,
            login="test_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/test_user",
            url="https://api.github.com/users/test_user"
        )
        
        user2 = User(
            id=123,
            login="test_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/test_user",
            url="https://api.github.com/users/test_user"
        )
        
        user3 = User(
            id=456,
            login="different_user",
            node_id="MDQ6VXNlcjQ1Ng==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/456",
            html_url="https://github.com/different_user",
            url="https://api.github.com/users/different_user"
        )
        
        assert user1 == user2
        assert user1 != user3
        assert user2 != user3

    def test_user_string_representation(self):
        """Test User string representation."""
        user = User(
            id=123,
            login="repr_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/repr_user",
            url="https://api.github.com/users/repr_user",
            name="Repr User"
        )
        
        user_str = str(user)
        assert "repr_user" in user_str
        assert "123" in user_str

    def test_user_private_information_fields(self):
        """Test User private information fields (for authenticated user)."""
        user = User(
            id=123,
            login="private_user",
            node_id="MDQ6VXNlcjEyMw==",
            type="User",
            site_admin=False,
            avatar_url="https://avatars.githubusercontent.com/u/123",
            html_url="https://github.com/private_user",
            url="https://api.github.com/users/private_user",
            email="private@example.com",
            private_gists=5,
            total_private_repos=10,
            owned_private_repos=8,
            disk_usage=512000,
            collaborators=3,
            two_factor_authentication=True
        )
        
        # These fields are typically only available for the authenticated user
        assert user.email == "private@example.com"
        assert user.private_gists == 5
        assert user.total_private_repos == 10
        assert user.owned_private_repos == 8
        assert user.disk_usage == 512000
        assert user.collaborators == 3
        assert user.two_factor_authentication is True
