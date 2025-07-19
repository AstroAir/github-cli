"""
Data loader for dashboard components.
"""

import asyncio
from typing import Dict, List, Any

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError
from github_cli.models.repository import Repository


class DashboardDataLoader:
    """Handles data loading for the dashboard."""
    
    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.data = {
            "user": None,
            "repositories": [],
            "pull_requests": [],
            "issues": [],
            "notifications": [],
            "workflow_runs": []
        }
    
    async def load_all_data(self) -> Dict[str, Any]:
        """Load all dashboard data."""
        try:
            # Load all data concurrently
            await asyncio.gather(
                self._load_user_info(),
                self._load_repositories(),
                self._load_pull_requests(),
                self._load_issues(),
                self._load_notifications(),
                return_exceptions=True
            )
        except Exception as e:
            self.terminal.display_error(f"Error loading dashboard data: {str(e)}")
        
        return self.data.copy()
    
    async def _load_user_info(self) -> None:
        """Load user information."""
        try:
            if not self.data["user"]:
                self.data["user"] = await self.client.authenticator.fetch_user_info()
        except Exception as e:
            self.terminal.display_error(f"Error loading user info: {str(e)}")
    
    async def _load_repositories(self) -> None:
        """Load user repositories."""
        try:
            response = await self.client.get("user/repos", params={
                "sort": "updated", 
                "per_page": 5
            })
            
            # Extract data from response
            repos_data = response.data if hasattr(response, 'data') else response
            if isinstance(repos_data, list):
                self.data["repositories"] = [
                    Repository.from_json(repo) for repo in repos_data 
                    if isinstance(repo, dict)
                ]
            else:
                self.data["repositories"] = []
        except Exception as e:
            self.terminal.display_error(f"Error loading repositories: {str(e)}")
            self.data["repositories"] = []
    
    async def _load_pull_requests(self) -> None:
        """Load user pull requests."""
        try:
            response = await self.client.get("search/issues", params={
                "q": "is:pr is:open author:@me",
                "sort": "updated",
                "per_page": 5
            })
            
            # Extract data from response
            response_data = response.data if hasattr(response, 'data') else response
            if isinstance(response_data, dict):
                self.data["pull_requests"] = response_data.get("items", [])
            else:
                self.data["pull_requests"] = []
        except Exception as e:
            self.terminal.display_error(f"Error loading pull requests: {str(e)}")
            self.data["pull_requests"] = []
    
    async def _load_issues(self) -> None:
        """Load user issues."""
        try:
            response = await self.client.get("search/issues", params={
                "q": "is:issue is:open assignee:@me",
                "sort": "updated",
                "per_page": 5
            })
            
            # Extract data from response
            response_data = response.data if hasattr(response, 'data') else response
            if isinstance(response_data, dict):
                self.data["issues"] = response_data.get("items", [])
            else:
                self.data["issues"] = []
        except Exception as e:
            self.terminal.display_error(f"Error loading issues: {str(e)}")
            self.data["issues"] = []
    
    async def _load_notifications(self) -> None:
        """Load user notifications."""
        try:
            response = await self.client.get("notifications", params={"per_page": 5})
            response_data = response.data if hasattr(response, 'data') else response
            self.data["notifications"] = response_data if isinstance(response_data, list) else []
        except Exception as e:
            self.terminal.display_error(f"Error loading notifications: {str(e)}")
            self.data["notifications"] = []
    
    def get_cached_data(self) -> Dict[str, Any]:
        """Get currently cached data without reloading."""
        return self.data.copy()
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.data = {
            "user": None,
            "repositories": [],
            "pull_requests": [],
            "issues": [],
            "notifications": [],
            "workflow_runs": []
        }
