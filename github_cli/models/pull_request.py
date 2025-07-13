"""
Pull Request data model
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from github_cli.models.issue import Issue


@dataclass
class PullRequest(Issue):
    """GitHub pull request model"""

    head: Dict[str, Any]
    base: Dict[str, Any]
    merged: bool
    mergeable: Optional[bool]
    mergeable_state: Optional[str]
    merged_by: Optional[Dict[str, Any]]
    merged_at: Optional[str]
    draft: bool
    requested_reviewers: List[Dict[str, Any]]
    requested_teams: List[Dict[str, Any]]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'PullRequest':
        """Create a PullRequest object from JSON data"""
        # First create with Issue fields
        issue = Issue.from_json(data)

        # Then add PR-specific fields
        return cls(
            id=issue.id,
            number=issue.number,
            title=issue.title,
            state=issue.state,
            locked=issue.locked,
            assignee=issue.assignee,
            assignees=issue.assignees,
            milestone=issue.milestone,
            comments=issue.comments,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            closed_at=issue.closed_at,
            author_association=issue.author_association,
            body=issue.body,
            user=issue.user,
            labels=issue.labels,
            html_url=issue.html_url,
            url=issue.url,
            repository_url=issue.repository_url,

            # PR-specific fields
            head=data["head"],
            base=data["base"],
            merged=data.get("merged", False),
            mergeable=data.get("mergeable"),
            mergeable_state=data.get("mergeable_state"),
            merged_by=data.get("merged_by"),
            merged_at=data.get("merged_at"),
            draft=data.get("draft", False),
            requested_reviewers=data.get("requested_reviewers", []),
            requested_teams=data.get("requested_teams", [])
        )

    @property
    def merged_date(self) -> Optional[datetime]:
        """Get the merged date as datetime if available"""
        if self.merged_at:
            return datetime.fromisoformat(self.merged_at.replace("Z", "+00:00"))
        return None

    @property
    def head_ref(self) -> str:
        """Get the head reference (branch name)"""
        return self.head.get("ref", "")

    @property
    def base_ref(self) -> str:
        """Get the base reference (branch name)"""
        return self.base.get("ref", "")

    @property
    def head_repo_full_name(self) -> Optional[str]:
        """Get the full name of the head repository"""
        if self.head.get("repo"):
            return self.head["repo"].get("full_name")
        return None

    @property
    def base_repo_full_name(self) -> Optional[str]:
        """Get the full name of the base repository"""
        if self.base.get("repo"):
            return self.base["repo"].get("full_name")
        return None
