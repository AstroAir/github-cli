"""
Workflow data model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Workflow:
    """GitHub Actions workflow model"""

    id: int
    name: str
    path: str
    state: str
    created_at: str
    updated_at: str
    url: str
    html_url: str
    badge_url: str
    inputs: Optional[Dict[str, Any]] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create a Workflow object from JSON data"""
        return cls(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            url=data["url"],
            html_url=data["html_url"],
            badge_url=data["badge_url"],
            inputs=data.get("inputs")
        )

    @property
    def created_date(self) -> datetime:
        """Get the creation date as datetime"""
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    @property
    def updated_date(self) -> datetime:
        """Get the last update date as datetime"""
        return datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run model"""

    id: int
    name: Optional[str]
    workflow_id: int
    head_branch: str
    run_number: int
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    url: str
    html_url: str
    head_sha: str
    event: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'WorkflowRun':
        """Create a WorkflowRun object from JSON data"""
        return cls(
            id=data["id"],
            name=data.get("name"),
            workflow_id=data["workflow_id"],
            head_branch=data["head_branch"],
            run_number=data["run_number"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            url=data["url"],
            html_url=data["html_url"],
            head_sha=data["head_sha"],
            event=data["event"]
        )

    @property
    def created_date(self) -> datetime:
        """Get the creation date as datetime"""
        return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    @property
    def updated_date(self) -> datetime:
        """Get the last update date as datetime"""
        return datetime.fromisoformat(self.updated_at.replace("Z", "+00:00"))


@dataclass
class WorkflowJob:
    """GitHub Actions workflow job model"""

    id: int
    run_id: int
    name: str
    status: str
    conclusion: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    steps: List[Dict[str, Any]]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'WorkflowJob':
        """Create a WorkflowJob object from JSON data"""
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            steps=data.get("steps", [])
        )

    @property
    def started_date(self) -> Optional[datetime]:
        """Get the started date as datetime if available"""
        if self.started_at:
            return datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        return None

    @property
    def completed_date(self) -> Optional[datetime]:
        """Get the completed date as datetime if available"""
        if self.completed_at:
            return datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))
        return None
