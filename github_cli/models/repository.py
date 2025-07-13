"""
Repository data model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Repository:
    """GitHub repository model"""

    id: int
    name: str
    full_name: str
    private: bool
    owner: Dict[str, Any]
    html_url: str
    description: Optional[str]
    fork: bool
    created_at: str
    updated_at: str
    pushed_at: str
    homepage: Optional[str]
    size: int
    stargazers_count: int
    watchers_count: int
    language: Optional[str]
    forks_count: int
    open_issues_count: int
    license: Optional[Dict[str, Any]]
    topics: List[str]
    default_branch: str
    visibility: str
    url: str
    archived: bool = False
    disabled: bool = False

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Repository':
        """Create a Repository object from JSON data"""
        # Extract the required fields, set default values for optional ones
        return cls(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            private=data["private"],
            owner=data["owner"],
            html_url=data["html_url"],
            description=data.get("description"),
            fork=data["fork"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            pushed_at=data["pushed_at"],
            homepage=data.get("homepage"),
            size=data["size"],
            stargazers_count=data["stargazers_count"],
            watchers_count=data["watchers_count"],
            language=data.get("language"),
            forks_count=data["forks_count"],
            open_issues_count=data["open_issues_count"],
            license=data.get("license"),
            topics=data.get("topics", []),
            default_branch=data["default_branch"],
            visibility=data.get(
                "visibility", "public" if not data["private"] else "private"),
            url=data["url"],
            archived=data.get("archived", False),
            disabled=data.get("disabled", False)
        )

    @property
    def owner_name(self) -> str:
        """Get the owner's login name"""
        return self.owner.get("login", "")

    @property
    def created_date(self) -> datetime:
        """Get the creation date as datetime"""
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    @property
    def updated_date(self) -> datetime:
        """Get the last update date as datetime"""
        return datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))

    @property
    def license_name(self) -> Optional[str]:
        """Get the license name if available"""
        if self.license:
            return self.license.get("name")
        return None
