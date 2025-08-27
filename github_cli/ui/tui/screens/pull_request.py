from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, Collapsible, DataTable, Input, Label, LoadingIndicator,
    Markdown, Placeholder, Rule, SelectionList, Static, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager
from github_cli.ui.tui.widgets import (
    create_enhanced_static, create_visual_separator, create_enhanced_button
)


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
        return str(self.user.get('login', 'Unknown'))

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
    """Detailed view for a single pull request with adaptive layout."""

    def __init__(self, pr: PullRequest, client: GitHubClient, repo_name: str, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.pr = pr
        self.client = client
        self.repo_name = repo_name
        self.loading = False
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the pull request detail screen with modern widgets and SelectionList."""
        with Container(id="pr-detail-container", classes="adaptive-container"):
            # Enhanced title
            yield create_enhanced_static(
                f"[bold cyan]Pull Request #{self.pr.number}:[/bold cyan] {self.pr.title}",
                static_id="pr-title",
                markup=True
            )

            # Visual separator
            yield create_visual_separator("heavy", "horizontal", "title-separator")

            # Basic Information Collapsible Section
            with Collapsible(
                title="📋 Pull Request Information",
                collapsed=False,
                id="pr-info-collapsible",
                classes="adaptive-panel priority-high"
            ):
                yield create_enhanced_static(
                    f"[bold yellow]Author:[/bold yellow] {self.pr.author}",
                    static_id="pr-author",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold yellow]State:[/bold yellow] {self.pr.state.upper()}",
                    static_id="pr-state",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold yellow]Branch:[/bold yellow] {self.pr.branch_info}",
                    static_id="pr-branch",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold yellow]Created:[/bold yellow] {self.pr.created_date}",
                    static_id="pr-created",
                    markup=True
                )
                if self.pr.draft:
                    yield create_enhanced_static(
                        "[bold red]⚠️ Draft PR[/bold red]",
                        static_id="pr-draft",
                        markup=True
                    )

            # Statistics Collapsible Section
            with Collapsible(
                title="📊 Statistics & Changes",
                collapsed=False,
                id="pr-stats-collapsible",
                classes="adaptive-panel priority-medium"
            ):
                yield create_enhanced_static(
                    f"[bold blue]💬 Comments:[/bold blue] {self.pr.comments}",
                    static_id="pr-comments",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold blue]📝 Review Comments:[/bold blue] {self.pr.review_comments}",
                    static_id="pr-review-comments",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold blue]📊 Changes:[/bold blue] [green]+{self.pr.additions}[/green]/[red]-{self.pr.deletions}[/red]",
                    static_id="pr-changes",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold blue]📁 Files Changed:[/bold blue] {self.pr.changed_files}",
                    static_id="pr-files",
                    markup=True
                )
                yield create_enhanced_static(
                    f"[bold blue]🔗 Commits:[/bold blue] {getattr(self.pr, 'commits', 0)}",
                    static_id="pr-commits",
                    markup=True
                )

            # Reviewers Selection Section (using SelectionList)
            with Collapsible(
                title="👥 Reviewers & Assignees",
                collapsed=True,
                id="pr-reviewers-collapsible",
                classes="adaptive-panel priority-medium"
            ):
                # SelectionList for managing reviewers
                reviewer_options = [
                    ("reviewer1", "👤 John Doe"),
                    ("reviewer2", "👤 Jane Smith"),
                    ("reviewer3", "👤 Bob Johnson"),
                    ("reviewer4", "👤 Alice Brown"),
                ]
                yield SelectionList(
                    *reviewer_options,
                    id="reviewers-selection",
                    classes="reviewers-list"
                )

                yield create_visual_separator("dashed", "horizontal", "reviewers-separator")

                # SelectionList for managing assignees
                assignee_options = [
                    ("assignee1", "🎯 John Doe"),
                    ("assignee2", "🎯 Jane Smith"),
                    ("assignee3", "🎯 Bob Johnson"),
                ]
                yield SelectionList(
                    *assignee_options,
                    id="assignees-selection",
                    classes="assignees-list"
                )

            # Labels Selection Section (using SelectionList)
            with Collapsible(
                title="🏷️ Labels & Categories",
                collapsed=True,
                id="pr-labels-collapsible",
                classes="adaptive-panel priority-low"
            ):
                # SelectionList for managing labels
                label_options = [
                    ("bug", "🐛 Bug"),
                    ("feature", "✨ Feature"),
                    ("enhancement", "🚀 Enhancement"),
                    ("documentation", "📚 Documentation"),
                    ("testing", "🧪 Testing"),
                    ("refactor", "♻️ Refactor"),
                    ("performance", "⚡ Performance"),
                    ("security", "🔒 Security"),
                ]
                yield SelectionList(
                    *label_options,
                    id="labels-selection",
                    classes="labels-list"
                )

            # Visual separator before tabs
            yield create_visual_separator("solid", "horizontal", "tabs-separator")

            # Enhanced tabs with modern content organization
            with TabbedContent(id="pr-tabs", classes="adaptive-tabs modern-tabs"):
                with TabPane("📄 Description", id="description-tab"):
                    if self.pr.body:
                        yield Markdown(self.pr.body, id="pr-description")
                    else:
                        yield create_enhanced_static(
                            "[dim]No description provided[/dim]",
                            static_id="pr-no-description",
                            markup=True
                        )

                with TabPane("📁 Files Changed", id="files-tab"):
                    with Collapsible(
                        title="🗂️ File Selection",
                        collapsed=False,
                        id="files-selection-collapsible"
                    ):
                        # SelectionList for file selection/filtering
                        file_options = [
                            ("file1", "📄 src/main.py"),
                            ("file2", "📄 src/utils.py"),
                            ("file3", "📄 tests/test_main.py"),
                            ("file4", "📄 README.md"),
                            ("file5", "📄 requirements.txt"),
                        ]
                        yield SelectionList(
                            *file_options,
                            id="files-selection",
                            classes="files-list"
                        )

                    yield create_enhanced_static(
                        "[dim]File diff viewer coming soon...[/dim]",
                        static_id="files-placeholder",
                        markup=True
                    )

                with TabPane("🔗 Commits", id="commits-tab"):
                    with Collapsible(
                        title="📋 Commit Selection",
                        collapsed=False,
                        id="commits-selection-collapsible"
                    ):
                        # SelectionList for commit selection
                        commit_options = [
                            ("commit1", "🔸 feat: Add new feature"),
                            ("commit2", "🔸 fix: Fix critical bug"),
                            ("commit3", "🔸 docs: Update documentation"),
                            ("commit4", "🔸 test: Add unit tests"),
                        ]
                        yield SelectionList(
                            *commit_options,
                            id="commits-selection",
                            classes="commits-list"
                        )

                    yield create_enhanced_static(
                        "[dim]Commit history details coming soon...[/dim]",
                        static_id="commits-placeholder",
                        markup=True
                    )

                with TabPane("✅ Checks", id="checks-tab"):
                    with Collapsible(
                        title="🔍 Check Selection",
                        collapsed=False,
                        id="checks-selection-collapsible"
                    ):
                        # SelectionList for status checks
                        check_options = [
                            ("check1", "✅ CI/CD Pipeline"),
                            ("check2", "✅ Code Quality"),
                            ("check3", "❌ Security Scan"),
                            ("check4", "⏳ Performance Tests"),
                        ]
                        yield SelectionList(
                            *check_options,
                            id="checks-selection",
                            classes="checks-list"
                        )

                    yield create_enhanced_static(
                        "[dim]Status checks details coming soon...[/dim]",
                        static_id="checks-placeholder",
                        markup=True
                    )

                with TabPane("👥 Reviews", id="reviews-tab"):
                    with Collapsible(
                        title="📝 Review Management",
                        collapsed=False,
                        id="reviews-management-collapsible"
                    ):
                        # SelectionList for review actions
                        review_options = [
                            ("approve", "✅ Approve"),
                            ("request_changes", "❌ Request Changes"),
                            ("comment", "💬 Comment Only"),
                            ("dismiss", "🚫 Dismiss Review"),
                        ]
                        yield SelectionList(
                            *review_options,
                            id="review-actions-selection",
                            classes="review-actions-list"
                        )

                    yield create_enhanced_static(
                        "[dim]Code reviews interface coming soon...[/dim]",
                        static_id="reviews-placeholder",
                        markup=True
                    )

            # Visual separator before actions
            yield create_visual_separator("heavy", "horizontal", "actions-separator")

            # Enhanced action buttons with modern styling
            with Horizontal(id="pr-actions", classes="adaptive-horizontal modern-actions"):
                if self.pr.is_mergeable:
                    yield create_enhanced_button(
                        "🔀 Merge",
                        "merge-pr",
                        variant="primary",
                        tooltip="Merge this pull request"
                    )
                    yield create_enhanced_button(
                        "🗳️ Request Review",
                        "request-review",
                        variant="default",
                        tooltip="Request review from selected reviewers"
                    )

                yield create_enhanced_button(
                    "🌐 Open in Browser",
                    "open-browser",
                    variant="default",
                    tooltip="Open pull request in web browser"
                )
                yield create_enhanced_button(
                    "📋 Copy URL",
                    "copy-url",
                    variant="default",
                    tooltip="Copy pull request URL to clipboard"
                )
                yield create_enhanced_button(
                    "🔄 Refresh",
                    "refresh-pr",
                    variant="default",
                    tooltip="Refresh pull request data"
                )
                yield create_enhanced_button(
                    "❌ Close",
                    "close-detail",
                    variant="error",
                    tooltip="Close this detail view"
                )

            yield LoadingIndicator(id="pr-detail-loading")

    def _on_responsive_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        """Apply responsive layout based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()

        # Apply breakpoint-specific classes
        container = self.query_one("#pr-detail-container")
        container.remove_class("xs", "sm", "md", "lg", "xl")
        container.add_class(breakpoint.name)

        # Reorganize layout for small screens
        try:
            info_container = self.query_one("#pr-info")
            if breakpoint.name in ["xs", "sm"]:
                # Stack vertically on small screens
                info_container.add_class("vertical-stack")
                info_container.remove_class("horizontal-layout")
            else:
                # Side by side on larger screens
                info_container.add_class("horizontal-layout")
                info_container.remove_class("vertical-stack")
        except Exception:
            pass

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

            self.notify("Pull request merged successfully!",
                        severity="information")
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
            self.notify(
                "pyperclip not available - install for clipboard support", severity="warning")
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

    # SelectionList event handlers for enhanced functionality
    @on(SelectionList.SelectedChanged, "#reviewers-selection")
    def on_reviewers_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle reviewer selection changes."""
        selected_reviewers = [str(item) for item in event.selection_list.selected]
        if selected_reviewers:
            self.notify(f"Selected reviewers: {', '.join(selected_reviewers)}", severity="information")
        else:
            self.notify("No reviewers selected", severity="information")

    @on(SelectionList.SelectedChanged, "#assignees-selection")
    def on_assignees_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle assignee selection changes."""
        selected_assignees = [str(item) for item in event.selection_list.selected]
        if selected_assignees:
            self.notify(f"Selected assignees: {', '.join(selected_assignees)}", severity="information")
        else:
            self.notify("No assignees selected", severity="information")

    @on(SelectionList.SelectedChanged, "#labels-selection")
    def on_labels_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle label selection changes."""
        selected_labels = [str(item) for item in event.selection_list.selected]
        if selected_labels:
            self.notify(f"Selected labels: {', '.join(selected_labels)}", severity="information")
        else:
            self.notify("No labels selected", severity="information")

    @on(SelectionList.SelectedChanged, "#files-selection")
    def on_files_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle file selection changes for diff viewing."""
        selected_files = [str(item) for item in event.selection_list.selected]
        if selected_files:
            self.notify(f"Viewing files: {', '.join(selected_files)}", severity="information")
            # In a real implementation, this would filter the diff view

    @on(SelectionList.SelectedChanged, "#commits-selection")
    def on_commits_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle commit selection changes."""
        selected_commits = [str(item) for item in event.selection_list.selected]
        if selected_commits:
            self.notify(f"Selected commits: {', '.join(selected_commits)}", severity="information")
            # In a real implementation, this would show commit details

    @on(SelectionList.SelectedChanged, "#checks-selection")
    def on_checks_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle status check selection changes."""
        selected_checks = [str(item) for item in event.selection_list.selected]
        if selected_checks:
            self.notify(f"Viewing checks: {', '.join(selected_checks)}", severity="information")
            # In a real implementation, this would show check details

    @on(SelectionList.SelectedChanged, "#review-actions-selection")
    def on_review_actions_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle review action selection changes."""
        selected_actions = [str(item) for item in event.selection_list.selected]
        if selected_actions:
            self.notify(f"Review actions: {', '.join(selected_actions)}", severity="information")
            # In a real implementation, this would trigger review actions


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
            logger.info(
                f"Loading pull requests for repo: {repo_name or 'all'}")

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
                    prs_data = response.get('items', []) if isinstance(
                        response, dict) else []  # type: ignore[unreachable]

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
                            review_comments=int(
                                pr_data.get("review_comments", 0)),
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
            pr_table.app.notify(
                f"Loaded {len(self.pull_requests)} pull requests", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to load pull requests: {e}")
            pr_table.app.notify(
                f"Failed to load pull requests: {e}", severity="error")
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
    """Complete pull request management widget with adaptive capabilities."""

    def __init__(self, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.client = client
        self.pr_manager = PullRequestManager(client)
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the pull request widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")

        # Search and filter controls - adaptive horizontal layout
        with Horizontal(id="pr-controls", classes="adaptive-horizontal"):
            yield Input(placeholder="Search pull requests...", id="pr-search", classes="adaptive-input")
            yield Input(placeholder="Repository (owner/repo)", id="repo-filter", classes="adaptive-input priority-medium")
            yield Button("🔄 Refresh", id="refresh-prs", classes="adaptive-button")
            yield Button("➕ New PR", id="new-pr", variant="primary", classes="adaptive-button priority-medium")

        # Pull request table with adaptive columns
        pr_table: DataTable = DataTable(
            id="pr-table", classes="pr-table adaptive-table")
        pr_table.add_columns("Title", "Author", "Branch", "Stats", "Created")
        yield pr_table

        # Loading indicator
        yield LoadingIndicator(id="pr-loading")

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        pr_table = self.query_one("#pr-table", DataTable)
        loading_indicator = self.query_one("#pr-loading")
        loading_indicator.display = False

        # Apply initial responsive styles if layout manager available
        if self.layout_manager:
            self._apply_responsive_styles()

        # Load pull requests (all repositories by default)
        await self.pr_manager.load_pull_requests(pr_table)

    def _on_responsive_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_styles()
            self._adapt_table_columns()

    def _apply_responsive_styles(self) -> None:
        """Apply responsive styles based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()

        # Apply breakpoint-specific classes
        self.remove_class("xs", "sm", "md", "lg", "xl")
        self.add_class(breakpoint.name)

        # Adapt controls layout for small screens
        try:
            controls = self.query_one("#pr-controls")
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

        try:
            pr_table = self.query_one("#pr-table", DataTable)

            # Hide/show columns based on screen size
            if breakpoint.name in ["xs", "sm"]:
                # Small screens: Show only essential columns
                self._hide_table_columns(
                    pr_table, ["Author", "Branch", "Created"])
            elif breakpoint.name == "md":
                # Medium screens: Hide less important columns
                self._hide_table_columns(pr_table, ["Created"])
            else:
                # Large screens: Show all columns
                self._show_all_table_columns(pr_table)

        except Exception as e:
            logger.warning(f"Could not adapt table columns: {e}")

    def _hide_table_columns(self, table: DataTable, columns: list[str]) -> None:
        """Hide specified table columns."""
        for col in columns:
            table.add_class(f"hide-{col.lower()}")

    def _show_all_table_columns(self, table: DataTable) -> None:
        """Show all table columns."""
        for col in ["author", "branch", "stats", "created"]:
            table.remove_class(f"hide-{col}")

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
        self.notify("New pull request creation coming soon",
                    severity="information")

    @on(DataTable.RowSelected, "#pr-table")
    def on_pr_selected(self, event: DataTable.RowSelected) -> None:
        """Handle pull request selection."""
        if event.row_key:
            pr = self.pr_manager.get_pull_request_by_id(
                str(event.row_key.value))
            if pr:
                repo_name = self.pr_manager.current_repo or "unknown/repo"
                # Pass layout manager to detail screen if available
                self.app.push_screen(PullRequestDetailScreen(
                    pr, self.client, repo_name, self.layout_manager))


# Function to replace placeholder in main TUI app
def create_pull_request_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> PullRequestWidget:
    """Create a pull request management widget with responsive capabilities."""
    return PullRequestWidget(client, layout_manager)
