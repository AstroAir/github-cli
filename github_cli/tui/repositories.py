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
from github_cli.tui.responsive import ResponsiveLayoutManager


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
        with Container(id="repo-detail-container", classes="adaptive-container"):
            yield Static(f"Repository: {self.repo.full_name}", id="repo-title", classes="adaptive-title")

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

            with TabbedContent(id="repo-tabs", classes="adaptive-tabs"):
                with TabPane("Files", id="files-tab"):
                    yield Placeholder("File browser coming soon")

                with TabPane("Issues", id="issues-tab"):
                    yield Placeholder("Issues list coming soon")

                with TabPane("Pull Requests", id="prs-tab"):
                    yield Placeholder("Pull requests coming soon")

                with TabPane("Actions", id="actions-tab"):
                    yield Placeholder("GitHub Actions coming soon")

            # Action buttons with adaptive layout
            with Horizontal(id="repo-actions", classes="adaptive-horizontal"):
                yield Button("🌐 Open in Browser", id="open-browser", classes="adaptive-button")
                yield Button("📋 Clone URL", id="copy-clone", classes="adaptive-button priority-medium")
                yield Button("⬅️ Back", id="back-button", variant="primary", classes="adaptive-button")

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes with improved performance and functionality."""
        logger.debug(
            f"Repository detail screen responding to layout change: {old_breakpoint} -> {new_breakpoint}")

        # Only refresh if breakpoint actually changed
        if old_breakpoint and old_breakpoint.name == new_breakpoint.name:
            return

        self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        """Apply responsive layout with enhanced adaptability."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes with cleanup
        container = self.query_one("#repo-detail-container")
        for bp_name in ["xs", "sm", "md", "lg", "xl"]:
            container.remove_class(bp_name)
        container.add_class(breakpoint.name)

        # Handle priority-based element visibility
        self._manage_priority_elements(breakpoint)

        # Reorganize layout for different screen sizes
        self._reorganize_layout(breakpoint)

        # Update button layout
        self._update_button_layout(breakpoint)

    def _manage_priority_elements(self, breakpoint) -> None:
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

    def _reorganize_layout(self, breakpoint) -> None:
        """Reorganize layout structure based on screen size."""
        try:
            info_container = self.query_one("#repo-info")
            tabs_container = self.query_one("#repo-tabs")

            if breakpoint.name in ["xs", "sm"]:
                # Compact layout for small screens
                info_container.add_class("vertical-stack", "compact-spacing")
                info_container.remove_class("horizontal-layout")
                tabs_container.add_class("compact-tabs")
            else:
                # Expanded layout for larger screens
                info_container.add_class("horizontal-layout")
                info_container.remove_class(
                    "vertical-stack", "compact-spacing")
                tabs_container.remove_class("compact-tabs")

        except Exception as e:
            logger.warning(f"Error reorganizing layout: {e}")

    def _update_button_layout(self, breakpoint) -> None:
        """Update button layout and visibility based on screen size."""
        try:
            actions_container = self.query_one("#repo-actions")
            buttons = actions_container.query("Button")

            if breakpoint.name == "xs":
                # Minimal buttons for extra small screens
                for button in buttons:
                    if "priority-medium" in button.classes:
                        button.display = False
                    else:
                        button.display = True
                actions_container.add_class("minimal-buttons")
            else:
                # Show all buttons for larger screens
                for button in buttons:
                    button.display = True
                actions_container.remove_class("minimal-buttons")

        except Exception as e:
            logger.warning(f"Error updating button layout: {e}")

    @on(Button.Pressed, "#open-browser")
    async def open_in_browser(self) -> None:
        """Open repository in browser with enhanced error handling."""
        import webbrowser
        import subprocess
        import sys

        try:
            # Try multiple methods to open browser (similar to auth flow)
            url = self.repo.html_url
            browser_opened = False

            # Primary method: Python webbrowser
            if webbrowser.open(url):
                browser_opened = True
                logger.info(
                    f"Opened repository {self.repo.full_name} in browser")
            else:
                # Platform-specific fallbacks
                if sys.platform.startswith('win'):
                    subprocess.run(['cmd', '/c', 'start', url], check=False)
                    browser_opened = True
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', url], check=False)
                    browser_opened = True
                elif sys.platform.startswith('linux'):
                    subprocess.run(['xdg-open', url], check=False)
                    browser_opened = True

            if browser_opened:
                self.notify(
                    f"🌐 Opened {self.repo.name} in browser", severity="information")
            else:
                # Try to copy URL to clipboard as fallback
                try:
                    import pyperclip
                    pyperclip.copy(url)
                    self.notify(
                        f"📋 Copied URL to clipboard: {url}", severity="information")
                except ImportError:
                    self.notify(
                        f"⚠️ Could not open browser. URL: {url}", severity="warning")

        except Exception as e:
            logger.error(f"Failed to open repository in browser: {e}")
            self.notify(f"❌ Failed to open browser: {e}", severity="error")

    @on(Button.Pressed, "#copy-clone")
    async def copy_clone_url(self) -> None:
        """Copy clone URL to clipboard with user feedback."""
        try:
            # Generate clone URL (prefer SSH for authenticated users, HTTPS otherwise)
            if self.repo.private:
                clone_url = f"git@github.com:{self.repo.full_name}.git"
            else:
                clone_url = f"https://github.com/{self.repo.full_name}.git"

            # Try to copy to clipboard
            try:
                import pyperclip
                pyperclip.copy(clone_url)
                self.notify(
                    f"📋 Copied clone URL: {clone_url}", severity="information")
                logger.info(f"Copied clone URL for {self.repo.full_name}")
            except ImportError:
                self.notify(f"📄 Clone URL: {clone_url}",
                            severity="information", timeout=10)
                logger.warning(
                    "pyperclip not available, displayed URL instead")

        except Exception as e:
            logger.error(f"Failed to copy clone URL: {e}")
            self.notify(f"❌ Failed to copy clone URL: {e}", severity="error")

    @on(Button.Pressed, "#copy-clone-url")
    def copy_clone_url_legacy(self) -> None:
        """Legacy copy clone URL handler - replaced by #copy-clone."""
        self.notify("⚠️ Use the 'Clone URL' button instead",
                    severity="warning")

    @on(Button.Pressed, "#refresh-repo")
    async def refresh_repo(self) -> None:
        """Refresh repository data with loading indicator."""
        try:
            self.notify("🔄 Refreshing repository data...",
                        severity="information")
            # TODO: Implement actual refresh logic
            await asyncio.sleep(1)  # Simulate API call
            self.notify("✅ Repository data refreshed", severity="information")
            logger.info(f"Refreshed data for repository {self.repo.full_name}")
        except Exception as e:
            logger.error(f"Failed to refresh repository data: {e}")
            self.notify(f"❌ Refresh failed: {e}", severity="error")

    @on(Button.Pressed, "#close-detail")
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


class RepositoryWidget(Container):
    """Complete repository management widget with adaptive capabilities."""

    def __init__(self, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.client = client
        self.repo_manager = RepositoryManager(client)
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self):
        """Compose the repository widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")

        # Search and filter controls - adaptive horizontal layout
        with Horizontal(id="repo-controls", classes="adaptive-horizontal"):
            yield Input(placeholder="Search repositories...", id="repo-search", classes="adaptive-input")
            yield Button("🔄 Refresh", id="refresh-repos", classes="adaptive-button")
            yield Button("➕ New Repo", id="new-repo", variant="primary", classes="adaptive-button priority-medium")

        # Repository table with adaptive columns
        repo_table = DataTable(
            id="repo-table", classes="repo-table adaptive-table")

        # Add columns with priority for responsive hiding
        repo_table.add_columns("Name", "Description",
                               "Language", "Stats", "Updated")
        yield repo_table

        # Loading indicator
        yield LoadingIndicator(id="repo-loading")

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        repo_table = self.query_one("#repo-table", DataTable)
        loading_indicator = self.query_one("#repo-loading")
        loading_indicator.display = False

        # Apply initial responsive styles if layout manager available
        if self.layout_manager:
            self._apply_responsive_styles()

        # Load repositories
        await self.repo_manager.load_repositories(repo_table)

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_styles()
            self._adapt_table_columns()

    def _apply_responsive_styles(self) -> None:
        """Apply responsive styles based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes
        self.remove_class("xs", "sm", "md", "lg", "xl")
        self.add_class(breakpoint.name)

        # Adapt controls layout for small screens
        try:
            controls = self.query_one("#repo-controls")
            if breakpoint.compact_mode:
                controls.add_class("compact-layout")
                controls.remove_class("full-layout")
            else:
                controls.add_class("full-layout")
                controls.remove_class("compact-layout")
        except Exception:
            pass

    def _adapt_table_columns(self) -> None:
        """Adapt table columns based on breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        try:
            repo_table = self.query_one("#repo-table", DataTable)

            # Hide/show columns based on screen size
            if breakpoint.name in ["xs", "sm"]:
                # Small screens: Show only essential columns
                self._hide_table_columns(
                    repo_table, ["Description", "Language", "Updated"])
            elif breakpoint.name == "md":
                # Medium screens: Hide less important columns
                self._hide_table_columns(repo_table, ["Updated"])
            else:
                # Large screens: Show all columns
                self._show_all_table_columns(repo_table)

        except Exception as e:
            logger.warning(f"Could not adapt table columns: {e}")

    def _hide_table_columns(self, table: DataTable, columns: list[str]) -> None:
        """Hide specified table columns."""
        # Note: Textual DataTable doesn't support column hiding directly
        # This is a placeholder for future enhancement or custom implementation
        # For now, we'll add CSS classes to hide columns
        for col in columns:
            table.add_class(f"hide-{col.lower()}")

    def _show_all_table_columns(self, table: DataTable) -> None:
        """Show all table columns."""
        # Remove all hide classes
        for col in ["description", "language", "stats", "updated"]:
            table.remove_class(f"hide-{col}")

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
        self.notify("New repository creation coming soon",
                    severity="information")

    @on(DataTable.RowSelected, "#repo-table")
    def on_repo_selected(self, event: DataTable.RowSelected) -> None:
        """Handle repository selection."""
        if event.row_key:
            repo = self.repo_manager.get_repository_by_id(
                str(event.row_key.value))
            if repo:
                # Pass layout manager to detail screen if available
                self.app.push_screen(RepositoryDetailScreen(
                    repo, self.client, self.layout_manager))


# Function to replace placeholder in main TUI app
def create_repository_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> Container:
    """Create a repository management widget with responsive capabilities when available."""
    return RepositoryWidget(client, layout_manager)
