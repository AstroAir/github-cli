"""
Notification data model
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Notification:
    """GitHub Notification model"""

    id: str
    repository: Dict[str, Any]
    subject: Dict[str, Any]
    reason: str
    unread: bool
    updated_at: str
    last_read_at: Optional[str] = None
    url: str = ""
    subscription_url: Optional[str] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Notification':
        """Create a Notification object from JSON data"""
        return cls(
            id=data["id"],
            repository=data["repository"],
            subject=data["subject"],
            reason=data["reason"],
            unread=data["unread"],
            updated_at=data["updated_at"],
            last_read_at=data.get("last_read_at"),
            url=data.get("url", ""),
            subscription_url=data.get("subscription_url")
        )

    @property
    def updated_date(self) -> datetime:
        """Get the update date as datetime"""
        return datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))

    @property
    def last_read_date(self) -> Optional[datetime]:
        """Get the last read date as datetime if available"""
        if not self.last_read_at:
            return None
        return datetime.fromisoformat(self.last_read_at.replace("Z", "+00:00"))

    @property
    def read(self) -> bool:
        """Check if the notification has been read"""
        return not self.unread

    @property
    def repository_name(self) -> str:
        """Get the repository name"""
        full_name = self.repository.get("full_name", "unknown/unknown")
        return str(full_name) if full_name else "unknown/unknown"

    @property
    def subject_title(self) -> str:
        """Get the subject title"""
        title = self.subject.get("title", "No title")
        return str(title) if title else "No title"

    @property
    def subject_type(self) -> str:
        """Get the subject type"""
        subject_type = self.subject.get("type", "Unknown")
        return str(subject_type) if subject_type else "Unknown"

    @property
    def subject_url(self) -> Optional[str]:
        """Get the subject URL if available"""
        return self.subject.get("url")

    @property
    def formatted_reason(self) -> str:
        """Get a human-readable reason for the notification"""
        reasons = {
            "assign": "You were assigned",
            "author": "You created this thread",
            "comment": "You commented",
            "invitation": "You accepted an invitation",
            "manual": "You subscribed manually",
            "mention": "You were mentioned",
            "review_requested": "Your review was requested",
            "security_alert": "Security vulnerability alert",
            "state_change": "Thread state changed",
            "subscribed": "You're watching this repository",
            "team_mention": "Your team was mentioned"
        }
        return reasons.get(self.reason, self.reason.replace("_", " ").title())
