from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
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


class PullRequest(BaseModel):
    """Pull request data model for TUI display."""
    id: int
    number: int
    title: str
    body: str | None = None
    state: str  # open, closed, merged
    draft: bool = False
    user: dict[str, Any]
    head: dict[str, Any]
    base: dict[str, Any]
    created_at: str
    updated_at: str
    merged_at: str | None = None
    html_url: str
    comments: int = 0
    review_comments: int = 0
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    
    @property
    def display_title(self) -> str:
        """Get display title with status indicators."""
        status_emoji = {
            "open": "🟢",
            "closed": "🔴", 
            "merged": "🟣"
        }.get(self.state, "⚪")
        
        draft_indicator = " [DRAFT]" if self.draft else ""
        return f"{status_emoji} #{self.number} {self.title}{draft_indicator}"
    
    @property
    def author(self) -> str:
        """Get author username."""
        return self.user.get('login', 'Unknown')
    
    @property
    def branch_info(self) -> str:
        """Get branch information."""
        head_branch = self.head.get('ref', 'unknown')
        base_branch = self.base.get('ref', 'unknown')
        return f"{head_branch} �{base_branch}"
    
    @property
    def stats(self) -> str:
        """Get formatted statistics."""
        return f"💬 {self.comments} 📝 {self.review_comments} 📊 +{self.additions}/-{self.deletions}"
    
    @property
    def created_date(self) -> str:
        """Get formatted creation date."""
        try:
            dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return self.created_at
    
    @property
    def is_mergeable(self) -> bool:
        """Check if PR can be merged."""
        return self.state == "open" and not self.draft


class PullRequestDetailScreen(Screen[None]):
    """Detailed view for a single pull request."""
    
    def __init__(self, pr: PullRequest, client: GitHubClient, repo_name: str) -> None:
        super().__init__()
        self.pr = pr
        self.client = client
        self.repo_name = repo_name
        self.loading = False
    
    def compose(self):
        """Compose the pull request detail screen."""
        with Container(id="pr-detail-container"):
            yield Static(f"Pull Request #{self.pr.number}: {self.pr.title}", id="pr-title")
            
            with Horizontal(id="pr-info"):
                with Vertical(id="pr-basic-info"):
                    yield Label(f"Author: {self.pr.author}")
                    yield Label(f"State: {self.pr.state.upper()}")
                    yield Label(f"Branch: {self.pr.branch_info}")
                    yield Label(f"Created: {self.pr.created_date}")
                    if self.pr.draft:
                        yield Label("⚠️ Draft PR")
                
                with Vertical(id="pr-stats"):
                    yield Label(f"💬 Comments: {self.pr.comments}")
                    yield Label(f"📝 Review Comments: {self.pr.review_comments}")
                    yield Label(f"📊 Changes: +{self.pr.additions}/-{self.pr.deletions}")
                    yield Label(f"📁 Files Changed: {self.pr.changed_files}")
                    yield Label(f"🔗 Commits: {getattr(self.pr, 'commits', 0)}")
            
            with TabbedContent(id="pr-tabs"):
                with TabPane("Description", id="description-tab"):
                    if self.pr.body:
                        yield Markdown(self.pr.body, id="pr-description")
                    else:
                        yield Static("No description provided", id="pr-no-description")
                
                with TabPane("Files Changed", id="files-tab"):
                    yield Placeholder("File diff viewer coming soon")
                
                with TabPane("Commits", id="commits-tab"):
                    yield Placeholder("Commit history coming soon")
                
                with TabPane("Checks", id="checks-tab"):
                    yield Placeholder("Status checks coming soon")
                
                with TabPane("Reviews", id="reviews-tab"):
                    yield Placeholder("Code reviews coming soon")
            
            with Horizontal(id="pr-actions"):
                if self.pr.is_mergeable:
                    yield Button("🔀 Merge", id="merge-pr", variant="primary")
                    yield Button("🗳�Request Review", id="request-review")
                
                yield Button("🌐 Open in Browser", id="open-browser")
                yield Button("📋 Copy URL", id="copy-url")
                yield Button("🔄 Refresh", id="refresh-pr")
                yield Button("�Close", id="close-detail", variant="error")
            
            yield LoadingIndicator(id="pr-detail-loading")
    
    async def on_mount(self) -> None:
        """Initialize the detail screen."""
        loading_indicator = self.query_one("#pr-detail-loading")
        loading_indicator.display = False
    
    @on(Button.Pressed, "#merge-pr")
    async def merge_pr(self) -> None:
        """Merge the pull request."""
        if not self.pr.is_mergeable:
            self.notify("Pull request cannot be merged", severity="error")
            return
        
        loading_indicator = self.query_one("#pr-detail-loading")
        # Show confirmation dialog (simplified for now)
        try:
            self.loading = True
            loading_indicator.display = True
            
            # Perform merge
            await self.client.put(f"/repos/{self.repo_name}/pulls/{self.pr.number}/merge", {
                "commit_title": f"Merge pull request #{self.pr.number}",
                "merge_method": "merge"
            })
            
            self.notify("Pull request merged successfully!", severity="information")
            logger.info(f"Merged PR #{self.pr.number} in {self.repo_name}")
            
            # Refresh the PR data
            await self.refresh_pr()
            
        except GitHubCLIError as e:
            logger.error(f"Failed to merge PR: {e}")
            self.notify(f"Failed to merge: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False
    
    @on(Button.Pressed, "#request-review")
    def request_review(self) -> None:
        """Request review for the pull request."""
        self.notify("Review request functionality coming soon")
    
    @on(Button.Pressed, "#open-browser")
    def open_in_browser(self) -> None:
        """Open pull request in browser."""
        import webbrowser
        try:
            webbrowser.open(self.pr.html_url)
            self.notify("Opened in browser", severity="information")
        except Exception as e:
            self.notify(f"Failed to open browser: {e}", severity="error")
    
    @on(Button.Pressed, "#copy-url")
    def copy_url(self) -> None:
        """Copy PR URL to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(self.pr.html_url)
            self.notify("URL copied to clipboard", severity="information")
        except ImportError:
            self.notify("pyperclip not available - install for clipboard support", severity="warning")
        except Exception as e:
            self.notify(f"Failed to copy URL: {e}", severity="error")
    
    @on(Button.Pressed, "#refresh-pr")
    async def refresh_pr(self) -> None:
        """Refresh pull request data."""
        loading_indicator = self.query_one("#pr-detail-loading")
        try:
            self.loading = True
            loading_indicator.display = True
            
            # Fetch updated PR data
            response = await self.client.get(f"/repos/{self.repo_name}/pulls/{self.pr.number}")
            
            pr_data = response.data if hasattr(response, 'data') else response
            if isinstance(pr_data, dict):
                updated_pr = PullRequest(
                    id=int(pr_data.get("id", 0)),
                    number=int(pr_data.get("number", 0)),
                    title=str(pr_data.get("title", "")),
                    body=pr_data.get("body"),
                    state=str(pr_data.get("state", "open")),
                    draft=bool(pr_data.get("draft", False)),
                    user=pr_data.get("user", {}),
                    head=pr_data.get("head", {}),
                    base=pr_data.get("base", {}),
                    created_at=str(pr_data.get("created_at", "")),
                    updated_at=str(pr_data.get("updated_at", "")),
                    merged_at=pr_data.get("merged_at"),
                    html_url=str(pr_data.get("html_url", "")),
                    comments=int(pr_data.get("comments", 0)),
                    review_comments=int(pr_data.get("review_comments", 0)),
                    commits=int(pr_data.get("commits", 0)),
                    additions=int(pr_data.get("additions", 0)),
                    deletions=int(pr_data.get("deletions", 0)),
                    changed_files=int(pr_data.get("changed_files", 0))
                )
                # Update the PR object (in a real app, you'd want to refresh the UI)
                self.pr = updated_pr
            
            self.notify("Pull request refreshed", severity="information")
            
        except GitHubCLIError as e:
            logger.error(f"Failed to refresh PR: {e}")
            self.notify(f"Failed to refresh: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False
    
    @on(Button.Pressed, "#close-detail")
    def close_detail(self) -> None:
        """Close the detail screen."""
        self.dismiss()


class PullRequestManager:
    """Pull request management for the TUI."""
    
    def __init__(self, client: GitHubClient) -> None:
        self.client = client
        self.pull_requests: list[PullRequest] = []
        self.filtered_prs: list[PullRequest] = []
        self.current_repo: str | None = None
        self.loading = False
    
    async def load_pull_requests(self, pr_table: DataTable, repo_name: str | None = None) -> None:
        """Load pull requests from GitHub API."""
        if self.loading:
            return
        
        self.loading = True
        loading_indicator = pr_table.app.query_one("#pr-loading")
        loading_indicator.display = True
        
        try:
            logger.info(f"Loading pull requests for repo: {repo_name or 'all'}")
            
            if repo_name:
                # Load PRs for specific repository
                self.current_repo = repo_name
                response = await self.client.get(f"/repos/{repo_name}/pulls", params={
                    "state": "all",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 100
                })
            else:
                # Load PRs across all repositories (search)
                response = await self.client.get("/search/issues", params={
                    "q": "is:pr author:@me",
                    "sort": "updated",
                    "order": "desc",
                    "per_page": 100
                })
                
                # Extract items from search response
                if hasattr(response, 'data') and 'items' in response.data:
                    prs_data = response.data['items']
                else:
                    prs_data = response.get('items', []) if isinstance(response, dict) else []
            
            prs_data = response.data if hasattr(response, 'data') else response
            if isinstance(prs_data, dict) and 'items' in prs_data:
                prs_data = prs_data['items']
            
            self.pull_requests = []
            for pr_data in prs_data:
                if isinstance(pr_data, dict):
                    try:
                        # Use the from_json method for proper construction
                        pr = PullRequest(
                            id=int(pr_data.get("id", 0)),
                            number=int(pr_data.get("number", 0)),
                            title=str(pr_data.get("title", "")),
                            body=pr_data.get("body"),
                            state=str(pr_data.get("state", "open")),
                            draft=bool(pr_data.get("draft", False)),
                            user=pr_data.get("user", {}),
                            head=pr_data.get("head", {}),
                            base=pr_data.get("base", {}),
                            created_at=str(pr_data.get("created_at", "")),
                            updated_at=str(pr_data.get("updated_at", "")),
                            merged_at=pr_data.get("merged_at"),
                            html_url=str(pr_data.get("html_url", "")),
                            comments=int(pr_data.get("comments", 0)),
                            review_comments=int(pr_data.get("review_comments", 0)),
                            commits=int(pr_data.get("commits", 0)),
                            additions=int(pr_data.get("additions", 0)),
                            deletions=int(pr_data.get("deletions", 0)),
                            changed_files=int(pr_data.get("changed_files", 0))
                        )
                        self.pull_requests.append(pr)
                    except (KeyError, TypeError) as e:
                        logger.warning(f"Skipping PR due to data error: {e}")
                        continue
            self.filtered_prs = self.pull_requests.copy()
            
            # Update table
            await self._update_table(pr_table)
            
            logger.info(f"Loaded {len(self.pull_requests)} pull requests")
            pr_table.app.notify(f"Loaded {len(self.pull_requests)} pull requests", severity="information")
            
        except GitHubCLIError as e:
            logger.error(f"Failed to load pull requests: {e}")
            pr_table.app.notify(f"Failed to load pull requests: {e}", severity="error")
        except Exception as e:
            logger.error(f"Unexpected error loading pull requests: {e}")
            pr_table.app.notify(f"Unexpected error: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False
    
    async def _update_table(self, pr_table: DataTable) -> None:
        """Update the pull request table with current data."""
        pr_table.clear()
        
        for pr in self.filtered_prs:
            pr_table.add_row(
                pr.display_title,
                pr.author,
                pr.branch_info,
                pr.stats,
                pr.created_date,
                key=str(pr.id)
            )
    
    def filter_pull_requests(self, search_term: str, pr_table: DataTable) -> None:
        """Filter pull requests based on search term."""
        if not search_term:
            self.filtered_prs = self.pull_requests.copy()
        else:
            search_lower = search_term.lower()
            self.filtered_prs = [
                pr for pr in self.pull_requests
                if search_lower in pr.title.lower() or 
                   search_lower in pr.author.lower() or
                   search_lower in str(pr.number)
            ]
        
        asyncio.create_task(self._update_table(pr_table))
    
    def get_pull_request_by_id(self, pr_id: str) -> PullRequest | None:
        """Get pull request by ID."""
        for pr in self.pull_requests:
            if str(pr.id) == pr_id:
                return pr
        return None


class PullRequestWidget(Container):
    """Complete pull request management widget."""
    
    def __init__(self, client: GitHubClient) -> None:
        super().__init__()
        self.client = client
        self.pr_manager = PullRequestManager(client)
    
    def compose(self):
        """Compose the pull request widget."""
        # Search and filter controls
        with Horizontal(id="pr-controls"):
            yield Input(placeholder="Search pull requests...", id="pr-search")
            yield Input(placeholder="Repository (owner/repo)", id="repo-filter")
            yield Button("🔄 Refresh", id="refresh-prs")
            yield Button("�New PR", id="new-pr", variant="primary")
        
        # Pull request table
        pr_table = DataTable(id="pr-table", classes="pr-table")
        pr_table.add_columns("Title", "Author", "Branch", "Stats", "Created")
        yield pr_table
        
        # Loading indicator
        yield LoadingIndicator(id="pr-loading")
    
    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        pr_table = self.query_one("#pr-table", DataTable)
        loading_indicator = self.query_one("#pr-loading")
        loading_indicator.display = False
        
        # Load pull requests (all repositories by default)
        await self.pr_manager.load_pull_requests(pr_table)
    
    @on(Input.Changed, "#pr-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        pr_table = self.query_one("#pr-table", DataTable)
        self.pr_manager.filter_pull_requests(event.value, pr_table)
    
    @on(Input.Submitted, "#repo-filter")
    async def on_repo_filter_submitted(self, event: Input.Submitted) -> None:
        """Handle repository filter submission."""
        pr_table = self.query_one("#pr-table", DataTable)
        repo_name = event.value.strip() if event.value else None
        await self.pr_manager.load_pull_requests(pr_table, repo_name)
    
    @on(Button.Pressed, "#refresh-prs")
    async def on_refresh_prs(self) -> None:
        """Handle refresh button press."""
        pr_table = self.query_one("#pr-table", DataTable)
        repo_filter = self.query_one("#repo-filter", Input)
        repo_name = repo_filter.value.strip() if repo_filter.value else None
        await self.pr_manager.load_pull_requests(pr_table, repo_name)
    
    @on(Button.Pressed, "#new-pr")
    def on_new_pr(self) -> None:
        """Handle new pull request button press."""
        self.notify("New pull request creation coming soon", severity="information")
    
    @on(DataTable.RowSelected, "#pr-table")
    def on_pr_selected(self, event: DataTable.RowSelected) -> None:
        """Handle pull request selection."""
        if event.row_key:
            pr = self.pr_manager.get_pull_request_by_id(str(event.row_key.value))
            if pr:
                repo_name = self.pr_manager.current_repo or "unknown/repo"
                self.app.push_screen(PullRequestDetailScreen(pr, self.client, repo_name))


# Function to replace placeholder in main TUI app
def create_pull_request_widget(client: GitHubClient) -> PullRequestWidget:
    """Create a pull request management widget."""
    return PullRequestWidget(client)
