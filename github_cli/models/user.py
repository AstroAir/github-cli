"""
User data model
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class User:
    """GitHub User model"""

    id: int
    login: str
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool
    name: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    hireable: Optional[bool] = None
    bio: Optional[str] = None
    twitter_username: Optional[str] = None
    public_repos: int = 0
    public_gists: int = 0
    followers: int = 0
    following: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    private_gists: int = 0
    total_private_repos: int = 0
    owned_private_repos: int = 0
    disk_usage: int = 0
    collaborators: int = 0
    two_factor_authentication: bool = False
    plan: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'User':
        """Create a User object from JSON data"""
        return cls(
            id=data["id"],
            login=data["login"],
            node_id=data["node_id"],
            avatar_url=data["avatar_url"],
            gravatar_id=data["gravatar_id"],
            url=data["url"],
            html_url=data["html_url"],
            followers_url=data["followers_url"],
            following_url=data["following_url"],
            gists_url=data["gists_url"],
            starred_url=data["starred_url"],
            subscriptions_url=data["subscriptions_url"],
            organizations_url=data["organizations_url"],
            repos_url=data["repos_url"],
            events_url=data["events_url"],
            received_events_url=data["received_events_url"],
            type=data["type"],
            site_admin=data["site_admin"],
            name=data.get("name"),
            company=data.get("company"),
            blog=data.get("blog"),
            location=data.get("location"),
            email=data.get("email"),
            hireable=data.get("hireable"),
            bio=data.get("bio"),
            twitter_username=data.get("twitter_username"),
            public_repos=data.get("public_repos", 0),
            public_gists=data.get("public_gists", 0),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            private_gists=data.get("private_gists", 0),
            total_private_repos=data.get("total_private_repos", 0),
            owned_private_repos=data.get("owned_private_repos", 0),
            disk_usage=data.get("disk_usage", 0),
            collaborators=data.get("collaborators", 0),
            two_factor_authentication=data.get(
                "two_factor_authentication", False),
            plan=data.get("plan", {})
        )

    @property
    def created_date(self) -> Optional[datetime]:
        """Get the creation date as datetime"""
        if not self.created_at:
            return None
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    @property
    def updated_date(self) -> Optional[datetime]:
        """Get the last update date as datetime"""
        if not self.updated_at:
            return None
        return datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))

    @property
    def display_name(self) -> str:
        """Get the display name (real name if available, otherwise login)"""
        return self.name or self.login

    @property
    def profile_url(self) -> str:
        """Get the user's profile URL"""
        return f"https://github.com/{self.login}"

    @property
    def is_organization(self) -> bool:
        """Check if this user is actually an organization"""
        return self.type.lower() == "organization"

    async def get_followers(self, client, per_page: int = 100, max_pages: int = 1) -> List['User']:
        """
        Get followers of this user

        Args:
            client: The GitHub client
            per_page: Number of results per page
            max_pages: Maximum number of pages to fetch

        Returns:
            List of User objects representing followers
        """
        response = await client.paginated_request(
            "GET",
            f"/users/{self.login}/followers",
            params={"per_page": per_page},
            max_pages=max_pages
        )

        return [User.from_json(item) for item in response]

    async def get_following(self, client, per_page: int = 100, max_pages: int = 1) -> List['User']:
        """
        Get users that this user is following

        Args:
            client: The GitHub client
            per_page: Number of results per page
            max_pages: Maximum number of pages to fetch

        Returns:
            List of User objects
        """
        response = await client.paginated_request(
            "GET",
            f"/users/{self.login}/following",
            params={"per_page": per_page},
            max_pages=max_pages
        )

        return [User.from_json(item) for item in response]

    async def is_following(self, client, target_user: str) -> bool:
        """
        Check if this user follows another user

        Args:
            client: The GitHub client
            target_user: Username of the user to check

        Returns:
            True if this user follows the target user
        """
        try:
            await client.get(f"/users/{self.login}/following/{target_user}")
            return True
        except Exception:
            return False

    async def follow(self, client, target_user: str) -> bool:
        """
        Follow a user (authenticated user only)

        Args:
            client: The GitHub client
            target_user: Username of the user to follow

        Returns:
            True if successful
        """
        try:
            await client.put(f"/user/following/{target_user}", data={})
            return True
        except Exception:
            return False

    async def unfollow(self, client, target_user: str) -> bool:
        """
        Unfollow a user (authenticated user only)

        Args:
            client: The GitHub client
            target_user: Username of the user to unfollow

        Returns:
            True if successful
        """
        try:
            await client.delete(f"/user/following/{target_user}")
            return True
        except Exception:
            return False
