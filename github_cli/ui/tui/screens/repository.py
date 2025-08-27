from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, Collapsible, DataTable, Digits, Input, Label, Link, ListView,
    LoadingIndicator, Markdown, Placeholder, Pretty, Rule, Static,
    TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
# Add responsive imports
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager
from github_cli.ui.tui.widgets import (
    create_enhanced_static, create_visual_separator, create_enhanced_button,
    create_digits_display, create_link_widget, create_list_view, create_pretty_display,
    create_collapsible_section
)


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
        """Ultra compact layout for very small heights with modern widgets."""
        with Container(id="repo-info-compact", classes="adaptive-layout"):
            # Use modern widgets for better display
            with Horizontal():
                # Repository name with link
                yield create_link_widget(
                    f"📂 {self.repo.name}",
                    self.repo.html_url,
                    link_id="repo-link"
                )

                # Statistics using Digits widgets
                yield create_digits_display(
                    self.repo.stargazers_count,
                    digits_id="stars-count"
                )
                yield Static("⭐", classes="stat-icon")

                yield create_digits_display(
                    self.repo.forks_count,
                    digits_id="forks-count"
                )
                yield Static("🍴", classes="stat-icon")

    def _compose_compact_layout(self) -> ComposeResult:
        """Compact layout for small heights with modern collapsible sections."""
        with Container(id="repo-info-compact", classes="adaptive-layout"):
            # Essential info with modern widgets
            with Horizontal():
                with Vertical(classes="compact-info-panel"):
                    # Repository name as clickable link
                    yield create_link_widget(
                        f"📂 {self.repo.name}",
                        self.repo.html_url,
                        link_id="compact-repo-link"
                    )
                    yield create_enhanced_static(
                        f"🔧 {self.repo.language or 'N/A'}",
                        static_id="compact-language",
                        markup=True
                    )

                with Vertical(classes="compact-stats-panel"):
                    # Use Digits widgets for statistics
                    with Horizontal():
                        yield Static("⭐", classes="stat-icon")
                        yield create_digits_display(
                            self.repo.stargazers_count,
                            digits_id="compact-stars"
                        )
                    with Horizontal():
                        yield Static("🍴", classes="stat-icon")
                        yield create_digits_display(
                            self.repo.forks_count,
                            digits_id="compact-forks"
                        )

            # Modern collapsible details section
            yield create_collapsible_section(
                title="ℹ️ Repository Details",
                collapsed=True,
                collapsible_id="compact-details"
            )

            # Add content to collapsible section programmatically
            if self.repo.description:
                yield create_enhanced_static(
                    f"📝 {self.repo.description}",
                    static_id="compact-description",
                    markup=True
                )

    def _compose_normal_layout(self) -> ComposeResult:
        """Normal layout for adequate heights with modern Collapsible sections."""
        with Container(id="repo-info", classes="adaptive-layout"):
            # Basic Information Collapsible Section
            with Collapsible(
                title="📂 Repository Information",
                collapsed=False,
                id="basic-info-collapsible",
                classes="adaptive-panel priority-high"
            ):
                yield create_enhanced_static(
                    f"[bold cyan]Name:[/bold cyan] {self.repo.name}",
                    static_id="repo-name",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold cyan]Description:[/bold cyan] {self.repo.description or 'No description'}",
                    static_id="repo-description",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold cyan]Language:[/bold cyan] {self.repo.language or 'Unknown'}",
                    static_id="repo-language",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold cyan]Private:[/bold cyan] {'Yes' if self.repo.private else 'No'}",
                    static_id="repo-private",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold cyan]Fork:[/bold cyan] {'Yes' if self.repo.fork else 'No'}",
                    static_id="repo-fork",
                    markup=True
                )

            # Statistics Collapsible Section
            with Collapsible(
                title="📊 Repository Statistics",
                collapsed=False,
                id="stats-collapsible",
                classes="adaptive-panel priority-medium"
            ):
                yield create_enhanced_static(
                    f"[bold yellow]⭐ Stars:[/bold yellow] {self.repo.stargazers_count}",
                    static_id="repo-stars",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold yellow]🍴 Forks:[/bold yellow] {self.repo.forks_count}",
                    static_id="repo-forks",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold yellow]📅 Updated:[/bold yellow] {self.repo.last_updated}",
                    static_id="repo-updated",
                    markup=True
                )

            # Visual separator
            yield create_visual_separator("heavy", "horizontal", "info-separator")

        # Enhanced tabs with modern content organization
        with TabbedContent(id="repo-tabs", classes="adaptive-tabs modern-tabs"):
            with TabPane("📁 Files", id="files-tab"):
                with Collapsible(
                    title="🗂️ File Browser",
                    collapsed=False,
                    id="files-collapsible"
                ):
                    yield create_enhanced_static(
                        "[dim]File browser functionality coming soon...[/dim]",
                        static_id="files-placeholder",
                        markup=True
                    )

            with TabPane("🐛 Issues", id="issues-tab"):
                with Collapsible(
                    title="📋 Issue Management",
                    collapsed=False,
                    id="issues-collapsible"
                ):
                    yield create_enhanced_static(
                        "[dim]Issues list and management coming soon...[/dim]",
                        static_id="issues-placeholder",
                        markup=True
                    )

            with TabPane("🔀 Pull Requests", id="prs-tab"):
                with Collapsible(
                    title="🔄 Pull Request Management",
                    collapsed=False,
                    id="prs-collapsible"
                ):
                    yield create_enhanced_static(
                        "[dim]Pull requests list and management coming soon...[/dim]",
                        static_id="prs-placeholder",
                        markup=True
                    )

            with TabPane("⚡ Actions", id="actions-tab"):
                with Collapsible(
                    title="🚀 GitHub Actions",
                    collapsed=False,
                    id="actions-collapsible"
                ):
                    yield create_enhanced_static(
                        "[dim]GitHub Actions workflows and runs coming soon...[/dim]",
                        static_id="actions-placeholder",
                        markup=True
                    )

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

    def create_code_viewer(self, file_content: str, language: str | None = None) -> ComposeResult:
        """Create a modern code viewer using TextArea widget."""
        # Use TextArea for syntax-highlighted code display
        yield create_text_area(
            text=file_content,
            language=language,
            text_area_id="code-viewer",
            read_only=True
        )

    def create_repository_stats_display(self) -> ComposeResult:
        """Create a modern statistics display using new widgets."""
        with Container(id="stats-container", classes="stats-display"):
            # Use Pretty widget to display repository metadata
            repo_data = {
                "name": self.repo.name,
                "language": self.repo.language,
                "private": self.repo.private,
                "fork": self.repo.fork,
                "created": self.repo.updated_at
            }
            yield create_pretty_display(
                repo_data,
                pretty_id="repo-metadata"
            )

            # Use Digits widgets for large numbers
            with Horizontal(classes="stats-row"):
                yield Static("Stars:", classes="stat-label")
                yield create_digits_display(
                    self.repo.stargazers_count,
                    digits_id="stars-display"
                )

                yield Static("Forks:", classes="stat-label")
                yield create_digits_display(
                    self.repo.forks_count,
                    digits_id="forks-display"
                )


# Function to create repository widget for main TUI app
def create_repository_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> Container:
    """Create a repository management widget with responsive capabilities."""
    # Use the new responsive repository widget for better horizontal layout support
    from github_cli.ui.tui.screens.responsive_repository import ResponsiveRepositoryWidget
    return ResponsiveRepositoryWidget(client, layout_manager)
