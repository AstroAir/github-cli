"""
Layout manager for dashboard components.
"""

from typing import Dict, Any
from rich.layout import Layout

from github_cli.ui.components.common.headers import HeaderFactory
from github_cli.ui.components.common.footers import FooterFactory
from github_cli.ui.components.github import (
    RepositoryPanel, PullRequestPanel, IssuePanel, NotificationPanel
)


class DashboardLayoutManager:
    """Manages the layout and rendering of dashboard components."""
    
    def __init__(self):
        self.header_factory = HeaderFactory()
        self.footer_factory = FooterFactory()
        
        # Initialize panel components
        self.repo_panel = RepositoryPanel()
        self.pr_panel = PullRequestPanel()
        self.issue_panel = IssuePanel()
        self.notification_panel = NotificationPanel()
    
    def create_layout(self, data: Dict[str, Any]) -> Layout:
        """Create the main dashboard layout."""
        layout = Layout(name="root")

        # Split layout into header, body, and footer
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=1)
        )

        # Create sections
        layout["header"].update(self._create_header(data))
        layout["body"].update(self._create_body(data))
        layout["footer"].update(self._create_footer())

        return layout
    
    def _create_header(self, data: Dict[str, Any]):
        """Create the dashboard header."""
        user_info = data.get("user")
        rate_limit_info = data.get("rate_limit_info")
        
        return self.header_factory.create_dashboard_header(user_info, rate_limit_info)
    
    def _create_body(self, data: Dict[str, Any]) -> Layout:
        """Create the dashboard body layout."""
        body = Layout(name="body")
        
        # Split body into two columns
        body.split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )

        # Split left column for repositories and pull requests
        body["left"].split(
            Layout(name="repositories", ratio=1),
            Layout(name="pull_requests", ratio=1)
        )

        # Split right column for issues and notifications
        body["right"].split(
            Layout(name="issues", ratio=1),
            Layout(name="notifications", ratio=1)
        )

        # Add panels to each section
        body["left"]["repositories"].update(
            self.repo_panel.create_repositories_panel(data.get("repositories", []))
        )
        body["left"]["pull_requests"].update(
            self.pr_panel.create_pull_requests_panel(data.get("pull_requests", []))
        )
        body["right"]["issues"].update(
            self.issue_panel.create_issues_panel(data.get("issues", []))
        )
        body["right"]["notifications"].update(
            self.notification_panel.create_notifications_panel(data.get("notifications", []))
        )
        
        return body
    
    def _create_footer(self):
        """Create the dashboard footer."""
        return self.footer_factory.create_dashboard_footer()
    
    def create_compact_layout(self, data: Dict[str, Any]) -> Layout:
        """Create a compact layout for smaller screens."""
        layout = Layout(name="root")

        # Split layout into header, body, and footer
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=1)
        )

        # Create sections
        layout["header"].update(self._create_header(data))
        layout["footer"].update(self._create_footer())
        
        # Create vertical layout for compact view
        body = Layout(name="body")
        body.split(
            Layout(name="repositories", ratio=1),
            Layout(name="pull_requests", ratio=1),
            Layout(name="issues", ratio=1),
            Layout(name="notifications", ratio=1)
        )

        # Add panels
        body["repositories"].update(
            self.repo_panel.create_repositories_panel(data.get("repositories", []))
        )
        body["pull_requests"].update(
            self.pr_panel.create_pull_requests_panel(data.get("pull_requests", []))
        )
        body["issues"].update(
            self.issue_panel.create_issues_panel(data.get("issues", []))
        )
        body["notifications"].update(
            self.notification_panel.create_notifications_panel(data.get("notifications", []))
        )
        
        layout["body"].update(body)
        return layout
