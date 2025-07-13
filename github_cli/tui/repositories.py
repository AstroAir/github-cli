from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator, 
    Markdown, Static, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator, 
    Placeholder, Static, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError


class Repository(BaseModel):
    """Repository data model for TUI display."""
    id: int
    name: str
    full_name: str
    description: str | None = None
    private: bool = False
    fork: bool = False
    stargazers_count: int = 0
    forks_count: int = 0
    language: str | None = None
    updated_at: str
    html_url: str
    
    @property
    def display_name(self) -> str:
        """Get display name with status indicators."""
        prefix = "🔒" if self.private else "📂"
        fork_indicator = " (fork)" if self.fork else ""
        return f"{prefix} {self.name}{fork_indicator}"
    
    @property
    def stats(self) -> str:
        """Get formatted statistics."""
        return f"�{self.stargazers_count} 🍴 {self.forks_count}"
    
    @property
    def last_updated(self) -> str:
        """Get formatted last updated time."""
        try:
            dt = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return self.updated_at


class RepositoryDetailScreen(Screen[None]):
    """Detailed view for a single repository."""
    
    def __init__(self, repo: Repository, client: GitHubClient) -> None:
        super().__init__()
        self.repo = repo
        self.client = client
    
    def compose(self):
        """Compose the repository detail screen."""
        with Container(id="repo-detail-container"):
            yield Static(f"Repository: {self.repo.full_name}", id="repo-title")
            
            with Horizontal(id="repo-info"):
                with Vertical(id="repo-basic-info"):
                    yield Label(f"Name: {self.repo.name}")
                    yield Label(f"Description: {self.repo.description or 'No description'}")
                    yield Label(f"Language: {self.repo.language or 'Unknown'}")
                    yield Label(f"Private: {'Yes' if self.repo.private else 'No'}")
                    yield Label(f"Fork: {'Yes' if self.repo.fork else 'No'}")
                
                with Vertical(id="repo-stats"):
                    yield Label(f"�Stars: {self.repo.stargazers_count}")
                    yield Label(f"🍴 Forks: {self.repo.forks_count}")
                    yield Label(f"📅 Updated: {self.repo.last_updated}")
            
            with TabbedContent(id="repo-tabs"):
                with TabPane("Files", id="files-tab"):
                    yield Placeholder("File browser coming soon")
                
                with TabPane("Issues", id="issues-tab"):
                    yield Placeholder("Issues list coming soon")
                
                with TabPane("Pull Requests", id="prs-tab"):
                    yield Placeholder("Pull requests coming soon")
                
                with TabPane("Actions", id="actions-tab"):
                    yield Placeholder("GitHub Actions coming soon")
            
            with Horizontal(id="repo-actions"):
                yield Button("🌐 Open in Browser", id="open-browser")
                yield Button("📋 Clone URL", id="copy-clone-url")
                yield Button("🔄 Refresh", id="refresh-repo")
                yield Button("�Close", id="close-detail", variant="error")
    
    @on(Button.Pressed, "#open-browser")
    def open_in_browser(self) -> None:
        """Open repository in browser."""
        import webbrowser
        try:
            webbrowser.open(self.repo.html_url)
            self.notify("Opened in browser", severity="information")
        except Exception as e:
            self.notify(f"Failed to open browser: {e}", severity="error")
    
    @on(Button.Pressed, "#copy-clone-url")
    def copy_clone_url(self) -> None:
        """Copy clone URL to clipboard."""
        try:
            import pyperclip
            clone_url = f"git@github.com:{self.repo.full_name}.git"
            pyperclip.copy(clone_url)
            self.notify("Clone URL copied to clipboard", severity="information")
        except ImportError:
            self.notify("pyperclip not available - install for clipboard support", severity="warning")
        except Exception as e:
            self.notify(f"Failed to copy URL: {e}", severity="error")
    
    @on(Button.Pressed, "#refresh-repo")
    async def refresh_repo(self) -> None:
        """Refresh repository data."""
        self.notify("Refresh functionality coming soon")
    
    @on(Button.Pressed, "#close-detail")
    def close_detail(self) -> None:
        """Close the detail screen."""
        self.dismiss()


class RepositoryManager:
    """Repository management for the TUI."""
    
    def __init__(self, client: GitHubClient) -> None:
        self.client = client
        self.repositories: list[Repository] = []
        self.filtered_repos: list[Repository] = []
        self.loading = False
    
    async def load_repositories(self, repo_table: DataTable) -> None:
        """Load repositories from GitHub API."""
        if self.loading:
            return
        
        self.loading = True
        loading_indicator = repo_table.app.query_one("#repo-loading")
        loading_indicator.display = True
        
        try:
            logger.info("Loading repositories from GitHub API")
            
            # Fetch user repositories
            response = await self.client.get("/user/repos", params={
                "type": "all",
                "sort": "updated",
                "per_page": 100
            })
            
            repos_data = response.data if hasattr(response, 'data') else response
            
            self.repositories = []
            for repo_data in repos_data:
                if isinstance(repo_data, dict):
                    try:
                        # Create Repository with basic fields
                        repo = Repository(
                            id=int(repo_data.get("id", 0)),
                            name=str(repo_data.get("name", "")),
                            full_name=str(repo_data.get("full_name", "")),
                            description=repo_data.get("description"),
                            private=bool(repo_data.get("private", False)),
                            fork=bool(repo_data.get("fork", False)),
                            stargazers_count=int(repo_data.get("stargazers_count", 0)),
                            forks_count=int(repo_data.get("forks_count", 0)),
                            language=repo_data.get("language"),
                            updated_at=str(repo_data.get("updated_at", "")),
                            html_url=str(repo_data.get("html_url", ""))
                        )
                        self.repositories.append(repo)
                    except (KeyError, TypeError, ValueError) as e:
                        logger.warning(f"Skipping repository due to data error: {e}")
                        continue
            self.filtered_repos = self.repositories.copy()
            
            # Update table
            await self._update_table(repo_table)
            
            logger.info(f"Loaded {len(self.repositories)} repositories")
            repo_table.app.notify(f"Loaded {len(self.repositories)} repositories", severity="information")
            
        except GitHubCLIError as e:
            logger.error(f"Failed to load repositories: {e}")
            repo_table.app.notify(f"Failed to load repositories: {e}", severity="error")
        except Exception as e:
            logger.error(f"Unexpected error loading repositories: {e}")
            repo_table.app.notify(f"Unexpected error: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False
    
    async def _update_table(self, repo_table: DataTable) -> None:
        """Update the repository table with current data."""
        repo_table.clear()
        
        for repo in self.filtered_repos:
            repo_table.add_row(
                repo.display_name,
                repo.description[:50] + "..." if repo.description and len(repo.description) > 50 else repo.description or "",
                repo.language or "",
                repo.stats,
                repo.last_updated,
                key=str(repo.id)
            )
    
    def filter_repositories(self, search_term: str, repo_table: DataTable) -> None:
        """Filter repositories based on search term."""
        if not search_term:
            self.filtered_repos = self.repositories.copy()
        else:
            search_lower = search_term.lower()
            self.filtered_repos = [
                repo for repo in self.repositories
                if search_lower in repo.name.lower() or 
                   (repo.description and search_lower in repo.description.lower()) or
                   (repo.language and search_lower in repo.language.lower())
            ]
        
        asyncio.create_task(self._update_table(repo_table))
    
    def get_repository_by_id(self, repo_id: str) -> Repository | None:
        """Get repository by ID."""
        for repo in self.repositories:
            if str(repo.id) == repo_id:
                return repo
        return None


class RepositoryWidget(Container):
    """Complete repository management widget."""
    
    def __init__(self, client: GitHubClient) -> None:
        super().__init__()
        self.client = client
        self.repo_manager = RepositoryManager(client)
    
    def compose(self):
        """Compose the repository widget."""
        # Search and filter controls
        with Horizontal(id="repo-controls"):
            yield Input(placeholder="Search repositories...", id="repo-search")
            yield Button("🔄 Refresh", id="refresh-repos")
            yield Button("�New Repo", id="new-repo", variant="primary")
        
        # Repository table
        repo_table = DataTable(id="repo-table", classes="repo-table")
        repo_table.add_columns("Name", "Description", "Language", "Stats", "Updated")
        yield repo_table
        
        # Loading indicator
        yield LoadingIndicator(id="repo-loading")
    
    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        repo_table = self.query_one("#repo-table", DataTable)
        loading_indicator = self.query_one("#repo-loading")
        loading_indicator.display = False
        
        # Load repositories
        await self.repo_manager.load_repositories(repo_table)
    
    @on(Input.Changed, "#repo-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        repo_table = self.query_one("#repo-table", DataTable)
        self.repo_manager.filter_repositories(event.value, repo_table)
    
    @on(Button.Pressed, "#refresh-repos")
    async def on_refresh_repos(self) -> None:
        """Handle refresh button press."""
        repo_table = self.query_one("#repo-table", DataTable)
        await self.repo_manager.load_repositories(repo_table)
    
    @on(Button.Pressed, "#new-repo")
    def on_new_repo(self) -> None:
        """Handle new repository button press."""
        self.notify("New repository creation coming soon", severity="information")
    
    @on(DataTable.RowSelected, "#repo-table")
    def on_repo_selected(self, event: DataTable.RowSelected) -> None:
        """Handle repository selection."""
        if event.row_key:
            repo = self.repo_manager.get_repository_by_id(str(event.row_key.value))
            if repo:
                self.app.push_screen(RepositoryDetailScreen(repo, self.client))


# Function to replace placeholder in main TUI app
def create_repository_widget(client: GitHubClient) -> RepositoryWidget:
    """Create a repository management widget."""
    return RepositoryWidget(client)
