"""
Release data model
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Release:
    """GitHub Release model"""

    id: int
    node_id: str
    tag_name: str
    target_commitish: str
    name: Optional[str]
    body: Optional[str]
    draft: bool
    prerelease: bool
    created_at: str
    published_at: Optional[str]
    url: str
    html_url: str
    assets_url: str
    upload_url: str
    tarball_url: Optional[str]
    zipball_url: Optional[str]
    author: Dict[str, Any]
    assets: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Release':
        """Create a Release object from JSON data"""
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            tag_name=data["tag_name"],
            target_commitish=data["target_commitish"],
            name=data.get("name"),
            body=data.get("body"),
            draft=data["draft"],
            prerelease=data["prerelease"],
            created_at=data["created_at"],
            published_at=data.get("published_at"),
            url=data["url"],
            html_url=data["html_url"],
            assets_url=data["assets_url"],
            upload_url=data["upload_url"],
            tarball_url=data.get("tarball_url"),
            zipball_url=data.get("zipball_url"),
            author=data["author"],
            assets=data.get("assets", [])
        )

    @property
    def created_date(self) -> datetime:
        """Get the creation date as datetime"""
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    @property
    def published_date(self) -> Optional[datetime]:
        """Get the published date as datetime if published"""
        if not self.published_at:
            return None
        return datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))

    @property
    def author_name(self) -> str:
        """Get the username of the release author"""
        if self.author and "login" in self.author:
            return self.author["login"]
        return "Unknown"

    @property
    def download_count(self) -> int:
        """Get the total download count for all assets"""
        return sum(asset.get("download_count", 0) for asset in self.assets)

    @property
    def asset_names(self) -> List[str]:
        """Get the names of all assets"""
        return [asset.get("name", "") for asset in self.assets if asset.get("name")]

    @property
    def is_published(self) -> bool:
        """Check if the release is published (not a draft)"""
        return not self.draft and self.published_at is not None

    @property
    def is_latest(self) -> bool:
        """Check if this is marked as the latest release"""
        return not self.prerelease and not self.draft
