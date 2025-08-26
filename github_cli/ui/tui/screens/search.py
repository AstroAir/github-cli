from __future__ import annotations

import asyncio
from typing import Any, Literal, cast

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, DataTable, Input, Label, LoadingIndicator,
    Markdown, Select, Static, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
from github_cli.ui.tui.core.responsive import ResponsiveLayoutManager


SearchType = Literal["repositories", "code",
                     "commits", "issues", "users", "topics"]


class SearchResult(BaseModel):
    """Generic search result data model."""
    id: int | str
    title: str
    description: str | None = None
    url: str
    score: float | None = None
    type: str
    extra_data: dict[str, Any] = {}

    @property
    def display_title(self) -> str:
        """Get display title with type indicator."""
        type_emoji = {
            "repository": "📂",
            "user": "👤",
            "issue": "🐛",
            "pull_request": "🔄",
            "code": "📝",
            "commit": "💾",
            "topic": "🏷️"
        }.get(self.type, "📄")

        return f"{type_emoji} {self.title}"

    @property
    def subtitle(self) -> str:
        """Get subtitle with additional information."""
        if self.description:
            return self.description[:100] + "..." if len(self.description) > 100 else self.description
        return ""


class RepositorySearchResult(SearchResult):
    """Repository-specific search result."""
    type: str = "repository"

    @property
    def subtitle(self) -> str:
        """Get repository-specific subtitle."""
        extra = self.extra_data
        language = extra.get('language', '')
        stars = extra.get('stargazers_count', 0)
        forks = extra.get('forks_count', 0)

        parts = []
        if language:
            parts.append(f"🔤 {language}")
        if stars:
            parts.append(f"�{stars}")
        if forks:
            parts.append(f"🍴 {forks}")

        result = " | ".join(parts)
        if self.description and result:
            return f"{self.description[:50]}{'...' if len(self.description) > 50 else ''} | {result}"
        elif self.description:
            return self.description[:100] + "..." if len(self.description) > 100 else self.description
        return result


class UserSearchResult(SearchResult):
    """User-specific search result."""
    type: str = "user"

    @property
    def subtitle(self) -> str:
        """Get user-specific subtitle."""
        extra = self.extra_data
        user_type = extra.get('type', 'User')
        followers = extra.get('followers', 0)

        parts = [f"👥 {user_type}"]
        if followers:
            parts.append(f"Followers: {followers}")

        result = " | ".join(parts)
        if self.description and result:
            return f"{self.description} | {result}"
        elif self.description:
            return self.description
        return result


class IssueSearchResult(SearchResult):
    """Issue/PR-specific search result."""
    type: str = "issue"

    @property
    def subtitle(self) -> str:
        """Get issue-specific subtitle."""
        extra = self.extra_data
        state = extra.get('state', 'unknown')
        user = extra.get('user', {}).get('login', 'Unknown')
        repo = extra.get('repository_url', '').split(
            '/')[-1] if extra.get('repository_url') else 'Unknown'

        return f"{state.upper()} by {user} in {repo}"


class CodeSearchResult(SearchResult):
    """Code-specific search result."""
    type: str = "code"

    @property
    def subtitle(self) -> str:
        """Get code-specific subtitle."""
        extra = self.extra_data
        path = extra.get('path', '')
        repo = extra.get('repository', {}).get('full_name', 'Unknown')

        return f"{path} in {repo}"


class SearchManager:
    """Search management for the TUI."""

    def __init__(self, client: GitHubClient) -> None:
        self.client = client
        self.search_results: list[SearchResult] = []
        self.current_query: str = ""
        self.current_type: SearchType = "repositories"
        self.loading = False

    async def search(self, query: str, search_type: SearchType, results_table: DataTable) -> None:
        """Perform search using GitHub API."""
        if self.loading or not query.strip():
            return

        self.loading = True
        self.current_query = query
        self.current_type = search_type

        loading_indicator = results_table.app.query_one("#search-loading")
        loading_indicator.display = True

        try:
            logger.info(f"Searching for '{query}' in {search_type}")

            # Build search endpoint and parameters
            endpoint, params = self._build_search_params(query, search_type)

            response = await self.client.get(endpoint, params=params)

            search_data = response.data if hasattr(
                response, 'data') else response

            # Extract results from response
            items = search_data.get('items', []) if isinstance(
                search_data, dict) else []

            # Convert to SearchResult objects
            self.search_results = self._convert_to_search_results(
                items, search_type)

            # Update table
            await self._update_table(results_table)

            total_count = search_data.get('total_count', len(
                items)) if isinstance(search_data, dict) else len(items)
            logger.info(
                f"Found {len(self.search_results)} results (total: {total_count})")
            results_table.app.notify(
                f"Found {len(self.search_results)} results", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Search failed: {e}")
            results_table.app.notify(f"Search failed: {e}", severity="error")
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            results_table.app.notify(
                f"Unexpected error: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False

    def _build_search_params(self, query: str, search_type: SearchType) -> tuple[str, dict[str, Any]]:
        """Build search endpoint and parameters."""
        base_params = {
            "q": query,
            "per_page": 50,
            "sort": "updated",
            "order": "desc"
        }

        match search_type:
            case "repositories":
                return "/search/repositories", base_params
            case "code":
                return "/search/code", base_params
            case "commits":
                return "/search/commits", base_params
            case "issues":
                return "/search/issues", base_params
            case "users":
                return "/search/users", base_params
            case "topics":
                return "/search/topics", {**base_params, "sort": "created"}
            case _:
                # type: ignore[unreachable]
                return "/search/repositories", base_params

    def _convert_to_search_results(self, items: list[dict[str, Any]], search_type: SearchType) -> list[SearchResult]:
        """Convert API response items to SearchResult objects."""
        results: list[SearchResult] = []

        for item in items:
            try:
                result: SearchResult
                match search_type:
                    case "repositories":
                        result = RepositorySearchResult(
                            id=item.get('id', 0),
                            title=item.get('full_name', 'Unknown'),
                            description=item.get('description'),
                            url=item.get('html_url', ''),
                            score=item.get('score'),
                            extra_data={
                                'language': item.get('language'),
                                'stargazers_count': item.get('stargazers_count', 0),
                                'forks_count': item.get('forks_count', 0),
                                'private': item.get('private', False)
                            }
                        )

                    case "users":
                        result = UserSearchResult(
                            id=item.get('id', 0),
                            title=item.get('login', 'Unknown'),
                            description=item.get('bio'),
                            url=item.get('html_url', ''),
                            score=item.get('score'),
                            extra_data={
                                'type': item.get('type', 'User'),
                                'followers': item.get('followers', 0),
                                'public_repos': item.get('public_repos', 0)
                            }
                        )

                    case "issues":
                        result = IssueSearchResult(
                            id=item.get('id', 0),
                            title=item.get('title', 'Unknown'),
                            description=item.get('body', '')[
                                :200] if item.get('body') else None,
                            url=item.get('html_url', ''),
                            score=item.get('score'),
                            extra_data={
                                'state': item.get('state', 'unknown'),
                                'user': item.get('user', {}),
                                'repository_url': item.get('repository_url', ''),
                                'number': item.get('number', 0)
                            }
                        )

                    case "code":
                        result = CodeSearchResult(
                            id=item.get('sha', 'unknown'),
                            title=item.get('name', 'Unknown'),
                            description=None,
                            url=item.get('html_url', ''),
                            score=item.get('score'),
                            extra_data={
                                'path': item.get('path', ''),
                                'repository': item.get('repository', {})
                            }
                        )

                    case "commits":
                        commit_info = item.get('commit', {})
                        result = SearchResult(
                            id=item.get('sha', 'unknown'),
                            title=commit_info.get(
                                'message', 'No message')[:100],
                            description=f"by {commit_info.get('author', {}).get('name', 'Unknown')}",
                            url=item.get('html_url', ''),
                            score=item.get('score'),
                            type="commit",
                            extra_data={
                                'sha': item.get('sha', ''),
                                'author': commit_info.get('author', {}),
                                'repository': item.get('repository', {})
                            }
                        )

                    case "topics":
                        result = SearchResult(
                            id=item.get('name', 'unknown'),
                            title=item.get(
                                'display_name', item.get('name', 'Unknown')),
                            description=item.get('short_description'),
                            url=f"https://github.com/topics/{item.get('name', '')}",
                            score=item.get('score'),
                            type="topic",
                            extra_data={
                                'featured': item.get('featured', False),
                                'curated': item.get('curated', False)
                            }
                        )

                results.append(result)

            except Exception as e:
                logger.warning(f"Failed to convert search result: {e}")
                continue

        return results

    async def _update_table(self, results_table: DataTable) -> None:
        """Update the search results table."""
        results_table.clear()

        for result in self.search_results:
            results_table.add_row(
                result.display_title,
                result.subtitle,
                f"{result.score:.2f}" if result.score else "N/A",
                key=str(result.id)
            )

    def get_result_by_id(self, result_id: str) -> SearchResult | None:
        """Get search result by ID."""
        for result in self.search_results:
            if str(result.id) == result_id:
                return result
        return None


class SearchResultDetailScreen:
    """Detailed view for a search result."""

    def __init__(self, result: SearchResult, client: GitHubClient) -> None:
        self.result = result
        self.client = client

    def compose(self) -> ComposeResult:
        """Compose the search result detail screen."""
        with Container(id="search-result-detail"):
            yield Static(f"Search Result: {self.result.title}", id="result-title")

            with Vertical(id="result-info"):
                yield Label(f"Type: {self.result.type.title()}")
                yield Label(f"Score: {self.result.score or 'N/A'}")
                if self.result.description:
                    yield Markdown(self.result.description)

                # Show type-specific information
                if self.result.extra_data:
                    yield Static("Additional Information:", classes="section-title")
                    for key, value in self.result.extra_data.items():
                        if isinstance(value, (str, int, float, bool)) and value:
                            yield Label(f"{key.replace('_', ' ').title()}: {value}")

            with Horizontal(id="result-actions"):
                yield Button("🌐 Open in Browser", id="open-browser")
                yield Button("📋 Copy URL", id="copy-url")
                yield Button("�Close", id="close-detail", variant="error")


class SearchWidget(Container):
    """Complete search functionality widget with adaptive capabilities."""

    def __init__(self, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.client = client
        self.search_manager = SearchManager(client)
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the search widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")

        # Search controls - adaptive horizontal layout
        with Horizontal(id="search-controls", classes="adaptive-horizontal"):
            yield Input(placeholder="Enter search query...", id="search-input", classes="adaptive-input")
            yield Select(
                options=[
                    ("Repositories", "repositories"),
                    ("Code", "code"),
                    ("Issues & PRs", "issues"),
                    ("Users", "users"),
                    ("Commits", "commits"),
                    ("Topics", "topics")
                ],
                value="repositories",
                id="search-type-select",
                classes="adaptive-select"
            )
            yield Button("🔍 Search", id="search-button", variant="primary", classes="adaptive-button")
            yield Button("🗑️ Clear", id="clear-button", classes="adaptive-button priority-medium")

        # Search help - collapsible on small screens
        with Container(id="search-help", classes="adaptive-panel priority-low"):
            yield Static("Search Tips:", classes="help-title")
            yield Static("💡 Use quotes for exact phrases: \"exact phrase\"", classes="help-item priority-high")
            yield Static("🏷️ Filter by language: language:python", classes="help-item priority-medium")
            yield Static("👤 Filter by user: user:username", classes="help-item priority-medium")
            yield Static("📂 Filter by repo: repo:owner/name", classes="help-item priority-low")
            yield Static("🔧 Combine filters: language:python user:octocat", classes="help-item priority-low")

        # Search results with adaptive layout
        with TabbedContent(id="search-results-tabs", classes="adaptive-tabs"):
            with TabPane("Results", id="results-tab"):
                results_table: DataTable = DataTable(
                    id="search-results-table", classes="search-results adaptive-table")
                results_table.add_columns("Title", "Description", "Score")
                yield results_table

            with TabPane("Advanced", id="advanced-tab"):
                yield Container(id="advanced-search", classes="adaptive-content")

        # Loading indicator
        yield LoadingIndicator(id="search-loading")

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        results_table = self.query_one("#search-results-table", DataTable)
        loading_indicator = self.query_one("#search-loading")
        loading_indicator.display = False

        # Apply initial responsive styles if layout manager available
        if self.layout_manager:
            self._apply_responsive_styles()

    def _on_responsive_change(self, old_breakpoint: Any, new_breakpoint: Any) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_styles()
            self._adapt_layout()

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
            controls = self.query_one("#search-controls")
            if breakpoint.compact_mode:
                controls.add_class("compact-layout")
                controls.remove_class("full-layout")
            else:
                controls.add_class("full-layout")
                controls.remove_class("compact-layout")
        except Exception:
            pass

    def _adapt_layout(self) -> None:
        """Adapt layout based on breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()

        try:
            # Hide/show help section based on screen size
            help_section = self.query_one("#search-help")
            if breakpoint.name in ["xs", "sm"]:
                # Hide help on small screens to save space
                help_section.add_class("hidden")
            else:
                help_section.remove_class("hidden")
        except Exception as e:
            logger.warning(f"Could not adapt search layout: {e}")

    @on(Input.Submitted, "#search-input")
    async def on_search_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        await self._perform_search()

    @on(Button.Pressed, "#search-button")
    async def on_search_button(self) -> None:
        """Handle search button press."""
        await self._perform_search()

    @on(Button.Pressed, "#clear-button")
    def on_clear_button(self) -> None:
        """Handle clear button press."""
        search_input = self.query_one("#search-input", Input)
        results_table = self.query_one("#search-results-table", DataTable)
        search_help = self.query_one("#search-help")

        search_input.value = ""
        results_table.clear()
        search_help.display = True

        self.search_manager.search_results.clear()

    async def _perform_search(self) -> None:
        """Perform the search operation."""
        search_input = self.query_one("#search-input", Input)
        search_type_select = self.query_one("#search-type-select", Select)
        results_table = self.query_one("#search-results-table", DataTable)
        search_help = self.query_one("#search-help")

        query = search_input.value.strip()
        if not query:
            self.notify("Please enter a search query", severity="warning")
            return

        search_type = search_type_select.value
        if search_type_select.is_blank():
            search_type = "repositories"  # Default to repositories

        # Ensure we have a valid search type
        if search_type not in ["repositories", "code", "commits", "issues", "users", "topics"]:
            search_type = "repositories"

        # Hide help and show results
        search_help.display = False

        await self.search_manager.search(query, cast(SearchType, search_type), results_table)

    @on(DataTable.RowSelected, "#search-results-table")
    def on_result_selected(self, event: DataTable.RowSelected) -> None:
        """Handle search result selection."""
        if event.row_key:
            result = self.search_manager.get_result_by_id(
                str(event.row_key.value))
            if result:
                # Open in browser for now (could implement detailed view)
                import webbrowser
                try:
                    webbrowser.open(result.url)
                    self.notify("Opened in browser", severity="information")
                except Exception as e:
                    self.notify(
                        f"Failed to open browser: {e}", severity="error")


# Function to replace placeholder in main TUI app
def create_search_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> SearchWidget:
    """Create a search widget with responsive capabilities."""
    return SearchWidget(client, layout_manager)
