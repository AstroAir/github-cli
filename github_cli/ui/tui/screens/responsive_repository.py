"""
Responsive repository widget optimized for horizontal screens with limited height.

This module provides repository management widgets that adapt intelligently to
different screen sizes and orientations. It implements multiple layout modes:
- Minimal layout for extremely constrained heights (≤8 lines)
- Compact layout for limited heights (8-12 lines) 
- Normal layout for adequate heights (>12 lines)

The widget automatically switches between full table view (6 columns) and
compact table view (4 columns) based on available space.
"""

from __future__ import annotations

import asyncio
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator,
    Placeholder, Static
)
from loguru import logger

from github_cli.api.client import GitHubClient
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager
from github_cli.ui.tui.screens.repository import Repository, RepositoryManager


class ResponsiveRepositoryWidget(Container):
    """Responsive repository widget optimized for horizontal screens with limited height."""

    def __init__(self, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.client = client
        self.repo_manager = RepositoryManager(client)
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the repository widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")
        
        # Check if we should use compact layout
        if self.layout_manager:
            breakpoint = self.layout_manager.get_current_breakpoint()
            available_height = self.layout_manager._get_available_content_height()
            
            if available_height < 10 or breakpoint.name.startswith("horizontal"):
                yield from self._compose_compact_layout()
            else:
                yield from self._compose_normal_layout()
        else:
            yield from self._compose_normal_layout()

    def _compose_compact_layout(self) -> ComposeResult:
        """Compose compact layout for horizontal screens with limited height."""
        # Single row controls
        with Horizontal(id="repo-controls-compact", classes="compact-controls"):
            yield Input(placeholder="Search...", id="repo-search", classes="compact-input")
            yield Button("🔄", id="refresh-repos", classes="compact-button")
            yield Button("➕", id="new-repo", variant="primary", classes="compact-button")

        # Compact table with fewer columns
        repo_table = DataTable(
            id="repo-table", 
            classes="compact-repo-table",
            show_header=True,
            show_row_labels=False
        )

        # Add minimal columns for compact view
        repo_table.add_columns("Repository", "Language", "★", "Updated")
        yield repo_table

        # Loading indicator
        yield LoadingIndicator(id="repo-loading")

    def _compose_normal_layout(self) -> ComposeResult:
        """Compose normal layout for adequate screen space."""
        # Full controls row
        with Horizontal(id="repo-controls", classes="full-controls"):
            yield Input(placeholder="Search repositories...", id="repo-search", classes="full-input")
            yield Button("🔄 Refresh", id="refresh-repos", classes="full-button")
            yield Button("➕ New Repo", id="new-repo", variant="primary", classes="full-button")

        # Full table with all columns
        repo_table = DataTable(
            id="repo-table", 
            classes="full-repo-table",
            show_header=True,
            show_row_labels=True
        )

        # Add full columns for normal view
        repo_table.add_columns("Name", "Description", "Language", "Stars", "Forks", "Updated")
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
        
        # Update table with responsive data
        await self._update_responsive_table(repo_table)

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_styles()
            self._adapt_table_for_layout(new_breakpoint)

    def _apply_responsive_styles(self) -> None:
        """Apply responsive styles based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes
        self.remove_class("xs", "sm", "md", "lg", "xl", "horizontal_tight", "horizontal_ultra_tight")
        self.add_class(breakpoint.name)

        # Adapt controls layout for small screens
        try:
            controls = self.query_one("#repo-controls, #repo-controls-compact")
            if breakpoint.compact_mode or breakpoint.name.startswith("horizontal"):
                controls.add_class("compact-layout")
                controls.remove_class("full-layout")
            else:
                controls.add_class("full-layout")
                controls.remove_class("compact-layout")
        except Exception:
            pass

    def _adapt_table_for_layout(self, breakpoint) -> None:
        """Adapt table layout based on breakpoint."""
        try:
            repo_table = self.query_one("#repo-table", DataTable)
            
            # Force recreate table if layout changed significantly
            if (breakpoint.name.startswith("horizontal") and 
                not repo_table.has_class("compact-repo-table")):
                asyncio.create_task(self._recreate_table_compact())
            elif (not breakpoint.name.startswith("horizontal") and 
                  repo_table.has_class("compact-repo-table")):
                asyncio.create_task(self._recreate_table_full())
                
        except Exception as e:
            logger.warning(f"Error adapting table layout: {e}")

    async def _recreate_table_compact(self) -> None:
        """Recreate table with compact layout."""
        try:
            repo_table = self.query_one("#repo-table", DataTable)
            repo_table.clear()
            
            # Update classes
            repo_table.remove_class("full-repo-table")
            repo_table.add_class("compact-repo-table")
            
            # Clear and recreate columns
            repo_table.columns.clear()
            repo_table.add_columns("Repository", "Language", "★", "Updated")
            
            # Reload data with compact format
            await self._update_responsive_table(repo_table)
            
        except Exception as e:
            logger.error(f"Error recreating compact table: {e}")

    async def _recreate_table_full(self) -> None:
        """Recreate table with full layout."""
        try:
            repo_table = self.query_one("#repo-table", DataTable)
            repo_table.clear()
            
            # Update classes
            repo_table.remove_class("compact-repo-table")
            repo_table.add_class("full-repo-table")
            
            # Clear and recreate columns
            repo_table.columns.clear()
            repo_table.add_columns("Name", "Description", "Language", "Stars", "Forks", "Updated")
            
            # Reload data with full format
            await self._update_responsive_table(repo_table)
            
        except Exception as e:
            logger.error(f"Error recreating full table: {e}")

    async def _update_responsive_table(self, repo_table: DataTable) -> None:
        """Update the repository table with responsive data format."""
        repo_table.clear()
        
        # Determine if we should use compact format
        compact_mode = False
        if self.layout_manager:
            breakpoint = self.layout_manager.get_current_breakpoint()
            compact_mode = (breakpoint.compact_mode or 
                          breakpoint.name.startswith("horizontal") or
                          self.layout_manager._get_available_content_height() < 10)

        for repo in self.repo_manager.filtered_repos:
            if compact_mode:
                # Compact format for small screens
                repo_table.add_row(
                    repo.name,
                    repo.language or "N/A",
                    str(repo.stargazers_count),
                    repo.last_updated.split(' ')[0],  # Date only
                    key=str(repo.id)
                )
            else:
                # Full format for larger screens
                repo_table.add_row(
                    repo.display_name,
                    repo.description[:40] + "..." if repo.description and len(repo.description) > 40 else repo.description or "",
                    repo.language or "N/A",
                    str(repo.stargazers_count),
                    str(repo.forks_count),
                    repo.last_updated,
                    key=str(repo.id)
                )

    @on(Input.Changed, "#repo-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        repo_table = self.query_one("#repo-table", DataTable)
        self.repo_manager.filter_repositories(event.value, repo_table)
        asyncio.create_task(self._update_responsive_table(repo_table))

    @on(Button.Pressed, "#refresh-repos")
    async def refresh_repositories(self) -> None:
        """Refresh repository list."""
        repo_table = self.query_one("#repo-table", DataTable)
        await self.repo_manager.load_repositories(repo_table)
        await self._update_responsive_table(repo_table)

    @on(Button.Pressed, "#new-repo")
    async def create_new_repository(self) -> None:
        """Create a new repository (placeholder)."""
        self.notify("Create new repository feature coming soon!", severity="information")

    @on(DataTable.RowSelected, "#repo-table")
    def on_repository_selected(self, event: DataTable.RowSelected) -> None:
        """Handle repository selection."""
        if event.row_key and event.row_key.value:
            repo = self.repo_manager.get_repository_by_id(str(event.row_key.value))
            if repo:
                # Open repository detail screen
                detail_screen = ResponsiveRepositoryDetailScreen(repo, self.client, self.layout_manager)
                self.app.push_screen(detail_screen)


class ResponsiveRepositoryDetailScreen(Screen[None]):
    """Responsive repository detail screen optimized for horizontal layouts."""

    def __init__(self, repo: Repository, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.repo = repo
        self.client = client
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the repository detail screen with adaptive layout."""
        if self.layout_manager:
            breakpoint = self.layout_manager.get_current_breakpoint()
            available_height = self.layout_manager._get_available_content_height()
            
            if available_height < 8 or breakpoint.name == "horizontal_ultra_tight":
                yield from self._compose_minimal_layout()
            elif available_height < 12 or breakpoint.name == "horizontal_tight":
                yield from self._compose_compact_layout()
            else:
                yield from self._compose_normal_layout()
        else:
            yield from self._compose_normal_layout()

    def _compose_minimal_layout(self) -> ComposeResult:
        """Minimal layout for extremely constrained height."""
        with Container(id="repo-detail-minimal", classes="minimal-container"):
            # Single line with essential info
            info_text = f"📂 {self.repo.name} | {self.repo.language or 'N/A'} | ⭐{self.repo.stargazers_count} | 🍴{self.repo.forks_count}"
            yield Static(info_text, id="minimal-info")
            
            # Single row of action buttons
            with Horizontal(id="minimal-actions", classes="minimal-actions"):
                yield Button("🌐", id="open-browser", classes="minimal-button")
                yield Button("📋", id="copy-clone", classes="minimal-button")
                yield Button("⬅️", id="back-button", variant="primary", classes="minimal-button")

    def _compose_compact_layout(self) -> ComposeResult:
        """Compact layout for limited height."""
        with Container(id="repo-detail-compact", classes="compact-container"):
            yield Static(self.repo.name, id="compact-title", classes="compact-title")
            
            # Two-column layout for info
            with Horizontal(id="compact-info", classes="compact-info-row"):
                with Vertical(classes="compact-info-col"):
                    yield Label(f"📂 {self.repo.name}")
                    yield Label(f"🔧 {self.repo.language or 'N/A'}")
                    
                with Vertical(classes="compact-info-col"):
                    yield Label(f"⭐ {self.repo.stargazers_count}")
                    yield Label(f"🍴 {self.repo.forks_count}")
            
            # Action buttons in horizontal layout
            with Horizontal(id="compact-actions", classes="compact-actions"):
                yield Button("🌐 Open", id="open-browser", classes="compact-button")
                yield Button("📋 Clone", id="copy-clone", classes="compact-button")
                yield Button("⬅️ Back", id="back-button", variant="primary", classes="compact-button")

    def _compose_normal_layout(self) -> ComposeResult:
        """Normal layout for adequate height."""
        with Container(id="repo-detail-normal", classes="normal-container"):
            yield Static(f"Repository: {self.repo.full_name}", id="normal-title", classes="normal-title")
            
            # Full info layout
            with Horizontal(id="normal-info", classes="normal-info-row"):
                with Vertical(id="basic-info", classes="info-panel"):
                    yield Label(f"Name: {self.repo.name}")
                    yield Label(f"Description: {self.repo.description or 'No description'}")
                    yield Label(f"Language: {self.repo.language or 'Unknown'}")
                    yield Label(f"Private: {'Yes' if self.repo.private else 'No'}")
                    
                with Vertical(id="stats-info", classes="stats-panel"):
                    yield Label(f"⭐ Stars: {self.repo.stargazers_count}")
                    yield Label(f"🍴 Forks: {self.repo.forks_count}")
                    yield Label(f"📅 Updated: {self.repo.last_updated}")
            
            # Action buttons
            with Horizontal(id="normal-actions", classes="normal-actions"):
                yield Button("🌐 Open in Browser", id="open-browser", classes="normal-button")
                yield Button("📋 Copy Clone URL", id="copy-clone", classes="normal-button")
                yield Button("⬅️ Back", id="back-button", variant="primary", classes="normal-button")

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        # Refresh the screen if the layout type changed significantly
        if old_breakpoint and new_breakpoint:
            old_is_horizontal = old_breakpoint.name.startswith("horizontal")
            new_is_horizontal = new_breakpoint.name.startswith("horizontal")
            
            if old_is_horizontal != new_is_horizontal:
                self.refresh()

    @on(Button.Pressed, "#open-browser")
    async def open_in_browser(self) -> None:
        """Open repository in browser."""
        import webbrowser
        try:
            if webbrowser.open(self.repo.html_url):
                self.notify(f"🌐 Opened {self.repo.name} in browser", severity="information")
            else:
                self.notify(f"⚠️ Could not open browser. URL: {self.repo.html_url}", severity="warning")
        except Exception as e:
            self.notify(f"❌ Failed to open browser: {e}", severity="error")

    @on(Button.Pressed, "#copy-clone")
    async def copy_clone_url(self) -> None:
        """Copy clone URL to clipboard."""
        try:
            clone_url = f"https://github.com/{self.repo.full_name}.git"
            try:
                import pyperclip
                pyperclip.copy(clone_url)
                self.notify(f"📋 Copied clone URL: {clone_url}", severity="information")
            except ImportError:
                self.notify(f"📄 Clone URL: {clone_url}", severity="information", timeout=10)
        except Exception as e:
            self.notify(f"❌ Failed to copy clone URL: {e}", severity="error")

    @on(Button.Pressed, "#back-button")
    def close_detail(self) -> None:
        """Close the detail screen."""
        if self.layout_manager:
            self.layout_manager.remove_resize_callback(self._on_responsive_change)
        self.dismiss()


def create_repository_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> ResponsiveRepositoryWidget:
    """Create a responsive repository widget."""
    return ResponsiveRepositoryWidget(client, layout_manager)
