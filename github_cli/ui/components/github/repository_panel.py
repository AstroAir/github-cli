"""
Repository panel component for displaying GitHub repositories.
"""

from typing import List, Optional
from datetime import datetime
from rich.panel import Panel
from rich.text import Text

from github_cli.ui.components.common.panels import InfoPanel
from github_cli.ui.components.common.tables import GitHubTable
from github_cli.models.repository import Repository


class RepositoryPanel:
    """Component for displaying repository information."""
    
    def __init__(self):
        self.info_panel = InfoPanel()
        self.table_factory = GitHubTable("Recent Repositories")
    
    def create_repositories_panel(self, repos: List[Repository]) -> Panel:
        """Create a panel displaying repositories."""
        if not repos:
            return self.info_panel.create_empty_state_panel(
                "No recent repositories", "Recent Repositories"
            )
        
        table = self.table_factory.create_repository_table()
        
        for repo in repos[:5]:  # Show up to 5 repos
            # Format the repository data
            name = repo.full_name or repo.name or "Unknown"
            description = (repo.description[:50] + "..." 
                         if repo.description and len(repo.description) > 50 
                         else repo.description or "No description")
            language = repo.language or "None"
            stars = str(repo.stargazers_count or 0)
            
            # Format updated date
            updated = "Unknown"
            if repo.updated_at:
                try:
                    if isinstance(repo.updated_at, str):
                        dt = datetime.fromisoformat(repo.updated_at.replace("Z", "+00:00"))
                    else:
                        dt = repo.updated_at
                    updated = dt.strftime("%Y-%m-%d")
                except (ValueError, AttributeError):
                    updated = "Unknown"
            
            table.add_row(name, description, language, stars, updated)
        
        return Panel(table, title="Recent Repositories", border_style="cyan")
    
    def create_repository_details_panel(self, repo: Repository) -> Panel:
        """Create a detailed panel for a single repository."""
        content = Text()
        
        # Repository name and description
        content.append(f"Repository: ", style="bold")
        content.append(f"{repo.full_name or repo.name}\n", style="cyan")
        
        if repo.description:
            content.append(f"Description: ", style="bold")
            content.append(f"{repo.description}\n", style="white")
        
        # Repository statistics
        content.append(f"Language: ", style="bold")
        content.append(f"{repo.language or 'None'}\n", style="green")
        
        content.append(f"Stars: ", style="bold")
        content.append(f"{repo.stargazers_count or 0}\n", style="yellow")
        
        content.append(f"Forks: ", style="bold")
        content.append(f"{repo.forks_count or 0}\n", style="blue")
        
        if repo.homepage:
            content.append(f"Homepage: ", style="bold")
            content.append(f"{repo.homepage}\n", style="link")
        
        return Panel(content, title="Repository Details", border_style="cyan")
