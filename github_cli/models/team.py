"""
Team data model
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Team:
    """GitHub Team model"""

    id: int
    node_id: str
    name: str
    slug: str
    description: Optional[str]
    privacy: str
    permission: str
    url: str
    html_url: str
    members_url: str
    repositories_url: str
    organization: Dict[str, Any]
    ldap_dn: Optional[str] = None
    parent: Optional[Dict[str, Any]] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Team':
        """Create a Team object from JSON data"""
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            name=data["name"],
            slug=data["slug"],
            description=data.get("description"),
            privacy=data["privacy"],
            permission=data["permission"],
            url=data["url"],
            html_url=data["html_url"],
            members_url=data["members_url"],
            repositories_url=data["repositories_url"],
            organization=data["organization"],
            ldap_dn=data.get("ldap_dn"),
            parent=data.get("parent")
        )

    @property
    def organization_name(self) -> str:
        """Get the organization name"""
        return self.organization.get("login", "Unknown")

    @property
    def is_visible(self) -> bool:
        """Check if the team is visible (not secret)"""
        return self.privacy != "secret"

    @property
    def is_admin_team(self) -> bool:
        """Check if the team has admin permissions"""
        return self.permission == "admin"

    @property
    def parent_team_name(self) -> Optional[str]:
        """Get the parent team name if present"""
        if self.parent:
            return self.parent.get("name")
        return None

    @property
    def team_url(self) -> str:
        """Get the team's URL"""
        return f"https://github.com/orgs/{self.organization_name}/teams/{self.slug}"
