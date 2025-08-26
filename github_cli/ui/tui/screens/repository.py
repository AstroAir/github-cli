from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator,
    Markdown, Placeholder, Static, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
# Add responsive imports
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager


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
    """Detailed view for a single repository with adaptive layout."""

    def __init__(self, repo: Repository, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.repo = repo
        self.client = client
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the repository detail screen with adaptive layout."""
        breakpoint = self.layout_manager.current_breakpoint if self.layout_manager else None

        with Container(id="repo-detail-container", classes="adaptive-container"):
            # Title - always visible but compact if needed
            if breakpoint and breakpoint.name.startswith("horizontal_ultra"):
                yield Static(f"{self.repo.name}", id="repo-title", classes="adaptive-title compact")
            else:
                yield Static(f"Repository: {self.repo.full_name}", id="repo-title", classes="adaptive-title")

            # Determine layout based on available height
            if self.layout_manager:
                available_height = self.layout_manager._get_available_content_height()

                if available_height < 10:
                    # Ultra compact layout - single column with essential info only
                    yield from self._compose_ultra_compact_layout()
                elif available_height < 15:
                    # Compact layout - essential info with minimal tabs
                    yield from self._compose_compact_layout()
                else:
                    # Normal layout
                    yield from self._compose_normal_layout()
            else:
                # Fallback to normal layout
                yield from self._compose_normal_layout()

    def _compose_ultra_compact_layout(self) -> ComposeResult:
        """Ultra compact layout for very small heights."""
        with Container(id="repo-info-compact", classes="adaptive-layout"):
            # Single line with most critical info
            info_text = f"📂 {self.repo.name} ({self.repo.language or 'N/A'}) ⭐{self.repo.stargazers_count} 🍴{self.repo.forks_count}"
            if self.repo.description:
                info_text += f" - {self.repo.description[:50]}..."
            yield Static(info_text, classes="ultra-compact-info")

    def _compose_compact_layout(self) -> ComposeResult:
        """Compact layout for small heights."""
        with Container(id="repo-info-compact", classes="adaptive-layout"):
            with Horizontal():
                with Vertical(classes="compact-info-panel"):
                    yield Label(f"📂 {self.repo.name}", classes="info-item")
                    yield Label(f"🔧 {self.repo.language or 'N/A'}", classes="info-item")

                with Vertical(classes="compact-stats-panel"):
                    yield Label(f"⭐ {self.repo.stargazers_count}", classes="stat-item")
                    yield Label(f"🍴 {self.repo.forks_count}", classes="stat-item")

            # Show description if available
            if self.repo.description:
                yield Label(f"📝 {self.repo.description[:80]}...", classes="compact-description")

    def _compose_normal_layout(self) -> ComposeResult:
        """Normal layout for adequate heights."""
        with Container(id="repo-info", classes="adaptive-layout"):
            with Vertical(id="repo-basic-info", classes="adaptive-panel priority-high"):
                yield Label(f"Name: {self.repo.name}", classes="info-item")
                yield Label(f"Description: {self.repo.description or 'No description'}", classes="info-item")
                yield Label(f"Language: {self.repo.language or 'Unknown'}", classes="info-item")
                yield Label(f"Private: {'Yes' if self.repo.private else 'No'}", classes="info-item")
                yield Label(f"Fork: {'Yes' if self.repo.fork else 'No'}", classes="info-item priority-medium")

            with Vertical(id="repo-stats", classes="adaptive-panel priority-medium"):
                yield Label(f"⭐ Stars: {self.repo.stargazers_count}", classes="stat-item")
                yield Label(f"🍴 Forks: {self.repo.forks_count}", classes="stat-item")
                yield Label(f"📅 Updated: {self.repo.last_updated}", classes="stat-item priority-low")

        # Tabs only for normal layout
        with TabbedContent(id="repo-tabs", classes="adaptive-tabs"):
            with TabPane("Files", id="files-tab"):
                yield Placeholder("File browser coming soon")

            with TabPane("Issues", id="issues-tab"):
                yield Placeholder("Issues list coming soon")

            with TabPane("Pull Requests", id="prs-tab"):
                yield Placeholder("Pull requests coming soon")

            with TabPane("Actions", id="actions-tab"):
                yield Placeholder("GitHub Actions coming soon")

    def _on_responsive_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
        """Handle responsive layout changes."""
        # Refresh the entire screen when layout changes significantly
        if old_breakpoint and new_breakpoint:
            if (old_breakpoint.name.startswith("horizontal") != new_breakpoint.name.startswith("horizontal") or
                    old_breakpoint.compact_mode != new_breakpoint.compact_mode):
                self.refresh()

    async def on_mount(self) -> None:
        """Initialize the detail screen."""
        # Apply initial responsive styling
        if self.layout_manager:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        """Apply responsive layout with enhanced adaptability."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()

        # Apply breakpoint-specific classes with cleanup
        container = self.query_one("#repo-detail-container")
        for bp_name in ["xs", "sm", "md", "lg", "xl", "horizontal_tight", "horizontal_ultra_tight"]:
            container.remove_class(bp_name)
        container.add_class(breakpoint.name)

        # Handle priority-based element visibility
        self._manage_priority_elements(breakpoint)

    def _manage_priority_elements(self, breakpoint: Any) -> None:
        """Manage element visibility based on priority and screen size."""
        try:
            # Hide low-priority elements in compact mode
            low_priority = self.query(".priority-low")
            for element in low_priority:
                element.display = not breakpoint.compact_mode

            # Hide medium-priority elements on very small screens
            medium_priority = self.query(".priority-medium")
            for element in medium_priority:
                element.display = breakpoint.name not in ["xs", "sm"]

        except Exception as e:
            logger.warning(f"Error managing priority elements: {e}")

    @on(Button.Pressed, "#back-button")
    def close_detail(self) -> None:
        """Close the detail screen with proper cleanup."""
        try:
            # Clean up responsive callbacks
            if self.layout_manager:
                self.layout_manager.remove_resize_callback(
                    self._on_responsive_change)

            self.dismiss()
            logger.debug("Closed repository detail screen")
        except Exception as e:
            logger.error(f"Error closing detail screen: {e}")
            # Force close even if cleanup fails
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

            repos_data = response.data if hasattr(
                response, 'data') else response

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
                            stargazers_count=int(
                                repo_data.get("stargazers_count", 0)),
                            forks_count=int(repo_data.get("forks_count", 0)),
                            language=repo_data.get("language"),
                            updated_at=str(repo_data.get("updated_at", "")),
                            html_url=str(repo_data.get("html_url", ""))
                        )
                        self.repositories.append(repo)
                    except (KeyError, TypeError, ValueError) as e:
                        logger.warning(
                            f"Skipping repository due to data error: {e}")
                        continue
            self.filtered_repos = self.repositories.copy()

            # Update table
            await self._update_table(repo_table)

            logger.info(f"Loaded {len(self.repositories)} repositories")
            repo_table.app.notify(
                f"Loaded {len(self.repositories)} repositories", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to load repositories: {e}")
            repo_table.app.notify(
                f"Failed to load repositories: {e}", severity="error")
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
                repo.description[:50] + "..." if repo.description and len(
                    repo.description) > 50 else repo.description or "",
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


# Function to create repository widget for main TUI app
def create_repository_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> Container:
    """Create a repository management widget with responsive capabilities."""
    # Use the new responsive repository widget for better horizontal layout support
    from github_cli.ui.tui.screens.responsive_repository import ResponsiveRepositoryWidget
    return ResponsiveRepositoryWidget(client, layout_manager)
