"""
Issue data model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Issue:
    """GitHub issue model"""

    id: int
    number: int
    title: str
    state: str
    locked: bool
    assignee: Optional[Dict[str, Any]]
    assignees: List[Dict[str, Any]]
    milestone: Optional[Dict[str, Any]]
    comments: int
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    author_association: str
    body: Optional[str]
    user: Dict[str, Any]
    labels: List[Dict[str, Any]]
    html_url: str
    url: str
    repository_url: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Issue':
        """Create an Issue object from JSON data"""
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            state=data["state"],
            locked=data["locked"],
            assignee=data.get("assignee"),
            assignees=data.get("assignees", []),
            milestone=data.get("milestone"),
            comments=data["comments"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            author_association=data["author_association"],
            body=data.get("body"),
            user=data["user"],
            labels=data.get("labels", []),
            html_url=data["html_url"],
            url=data["url"],
            repository_url=data["repository_url"]
        )

    @property
    def created_date(self) -> datetime:
        """Get the creation date as datetime"""
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    @property
    def updated_date(self) -> datetime:
        """Get the last update date as datetime"""
        return datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))

    @property
    def closed_date(self) -> Optional[datetime]:
        """Get the closed date as datetime if available"""
        if self.closed_at:
            return datetime.fromisoformat(self.closed_at.replace("Z", "+00:00"))
        return None

    @property
    def creator_name(self) -> str:
        """Get the creator's login name"""
        login = self.user.get("login", "")
        return str(login) if login else ""

    @property
    def label_names(self) -> List[str]:
        """Get a list of label names"""
        return [label.get("name", "") for label in self.labels]
