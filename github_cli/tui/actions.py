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
    Log, Placeholder, ProgressBar, Static, TabbedContent, TabPane
)
from loguru import logger
from pydantic import BaseModel

from github_cli.api.client import GitHubClient
from github_cli.utils.exceptions import GitHubCLIError
from github_cli.tui.responsive import ResponsiveLayoutManager


class WorkflowRun(BaseModel):
    """GitHub Actions workflow run data model."""
    id: int
    name: str | None = None
    head_branch: str | None = None
    head_sha: str
    status: str  # queued, in_progress, completed
    # success, failure, neutral, cancelled, timed_out, action_required, stale
    conclusion: str | None = None
    workflow_id: int
    check_suite_id: int
    created_at: str
    updated_at: str
    run_started_at: str | None = None
    html_url: str
    jobs_url: str
    logs_url: str
    check_suite_url: str
    artifacts_url: str
    cancel_url: str
    rerun_url: str
    workflow: dict[str, Any] | None = None

    @property
    def display_name(self) -> str:
        """Get display name with status indicators."""
        status_emoji = {
            "queued": "⏳",
            "in_progress": "🔄",
            "completed": self._get_conclusion_emoji()
        }.get(self.status, "❓")

        workflow_name = self.name or (self.workflow.get(
            'name') if self.workflow else 'Unknown')
        return f"{status_emoji} {workflow_name}"

    def _get_conclusion_emoji(self) -> str:
        """Get emoji for workflow conclusion."""
        return {
            "success": "✅",
            "failure": "❌",
            "neutral": "⚪",
            "cancelled": "🚫",
            "timed_out": "⏰",
            "action_required": "⚠️",
            "stale": "🔄"
        }.get(self.conclusion or "", "❓")

    @property
    def branch_info(self) -> str:
        """Get branch and commit info."""
        branch = self.head_branch or "unknown"
        commit = self.head_sha[:7] if self.head_sha else "unknown"
        return f"{branch} ({commit})"

    @property
    def created_date(self) -> str:
        """Get formatted creation date."""
        try:
            dt = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return self.created_at

    @property
    def can_rerun(self) -> bool:
        """Check if workflow can be rerun."""
        return self.status == "completed"

    @property
    def can_cancel(self) -> bool:
        """Check if workflow can be cancelled."""
        return self.status in ["queued", "in_progress"]


class WorkflowJob(BaseModel):
    """GitHub Actions job data model."""
    id: int
    run_id: int
    name: str
    status: str
    conclusion: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    html_url: str

    @property
    def display_name(self) -> str:
        """Get display name with status."""
        status_emoji = {
            "queued": "⏳",
            "in_progress": "🔄",
            "completed": self._get_conclusion_emoji()
        }.get(self.status, "❓")

        return f"{status_emoji} {self.name}"

    def _get_conclusion_emoji(self) -> str:
        """Get emoji for job conclusion."""
        return {
            "success": "✅",
            "failure": "❌",
            "cancelled": "🚫",
            "skipped": "⏭️"
        }.get(self.conclusion or "", "❓")


class WorkflowRunDetailScreen(Screen[None]):
    """Detailed view for a workflow run with adaptive layout."""

    def __init__(self, run: WorkflowRun, client: GitHubClient, repo_name: str, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.run = run
        self.client = client
        self.repo_name = repo_name
        self.jobs: list[WorkflowJob] = []
        self.loading = False
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the workflow run detail screen with adaptive layout."""
        with Container(id="workflow-detail-container", classes="adaptive-container"):
            yield Static(f"Workflow Run #{self.run.id}: {self.run.display_name}", id="workflow-title", classes="adaptive-title")

            with Container(id="workflow-info", classes="adaptive-layout"):
                with Vertical(id="workflow-basic-info", classes="adaptive-panel priority-high"):
                    yield Label(f"Status: {self.run.status.upper()}", classes="info-item")
                    if self.run.conclusion:
                        yield Label(f"Conclusion: {self.run.conclusion.upper()}", classes="info-item")
                    yield Label(f"Branch: {self.run.branch_info}", classes="info-item")
                    yield Label(f"Created: {self.run.created_at}", classes="info-item priority-medium")
                    yield Label(f"Status: {self.run.status.upper()}", classes="info-item priority-low")

                with Vertical(id="workflow-actions-panel", classes="adaptive-panel priority-medium"):
                    if self.run.status in ["queued", "in_progress"]:
                        yield Button("🛑 Cancel Run", id="cancel-run", variant="error", classes="adaptive-button")
                    elif self.run.conclusion in ["failure", "cancelled"]:
                        yield Button("🔄 Re-run", id="rerun-workflow", variant="primary", classes="adaptive-button")

                    yield Button("🌐 Open in Browser", id="open-browser", classes="adaptive-button priority-medium")
                    yield Button("📋 Copy URL", id="copy-url", classes="adaptive-button priority-low")
                    yield Button("⬅️ Back", id="back-button", variant="primary", classes="adaptive-button")

            with TabbedContent(id="workflow-tabs", classes="adaptive-tabs"):
                with TabPane("Jobs", id="jobs-tab"):
                    jobs_table = DataTable(
                        id="jobs-table", classes="jobs-table adaptive-table")
                    jobs_table.add_columns(
                        "Job", "Status", "Started", "Duration")
                    yield jobs_table

                with TabPane("Logs", id="logs-tab"):
                    yield Log(id="workflow-logs", classes="workflow-logs")
                    yield Button("📄 Download Logs", id="download-logs", classes="adaptive-button priority-low")

                with TabPane("Artifacts", id="artifacts-tab"):
                    yield Placeholder("Artifacts viewer coming soon")

            yield LoadingIndicator(id="workflow-detail-loading")

    async def on_mount(self) -> None:
        """Initialize the detail screen."""
        loading_indicator = self.query_one("#workflow-detail-loading")
        loading_indicator.display = False

        # Load jobs for this workflow run
        self.load_jobs()

    @work(exclusive=True)
    async def load_jobs(self) -> None:
        """Load jobs for the workflow run."""
        loading_indicator = self.query_one("#workflow-detail-loading")
        try:
            self.loading = True
            loading_indicator.display = True

            # Fetch jobs for this run
            response = await self.client.get(f"/repos/{self.repo_name}/actions/runs/{self.run.id}/jobs")

            jobs_data = response.data if hasattr(
                response, 'data') else response
            if isinstance(jobs_data, dict) and 'jobs' in jobs_data:
                jobs_data = jobs_data['jobs']

            if isinstance(jobs_data, list):
                self.jobs = []
                for job_data in jobs_data:
                    try:
                        job = WorkflowJob(
                            id=job_data.get('id', 0),
                            run_id=job_data.get('run_id', 0),
                            name=job_data.get('name', ''),
                            status=job_data.get('status', ''),
                            conclusion=job_data.get('conclusion'),
                            created_at=job_data.get('created_at', ''),
                            started_at=job_data.get('started_at'),
                            completed_at=job_data.get('completed_at'),
                            html_url=job_data.get('html_url', '')
                        )
                        self.jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Failed to parse job data: {e}")
            else:
                self.jobs = []

            # Update jobs table
            await self._update_jobs_table()

            logger.info(
                f"Loaded {len(self.jobs)} jobs for workflow run {self.run.id}")

        except GitHubCLIError as e:
            logger.error(f"Failed to load jobs: {e}")
            self.notify(f"Failed to load jobs: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False

    async def _update_jobs_table(self) -> None:
        """Update the jobs table."""
        jobs_table = self.query_one("#jobs-table", DataTable)
        jobs_table.clear()

        for job in self.jobs:
            started_time = ""
            duration = ""

            if job.started_at:
                try:
                    started_dt = datetime.fromisoformat(
                        job.started_at.replace('Z', '+00:00'))
                    started_time = started_dt.strftime('%H:%M:%S')

                    if job.completed_at:
                        completed_dt = datetime.fromisoformat(
                            job.completed_at.replace('Z', '+00:00'))
                        duration_seconds = (
                            completed_dt - started_dt).total_seconds()
                        duration = f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s"
                    elif job.status == "in_progress":
                        duration = "Running..."
                except Exception:
                    started_time = job.started_at

            jobs_table.add_row(
                job.display_name,
                job.status,
                started_time,
                duration,
                key=str(job.id)
            )

    @on(Button.Pressed, "#rerun-workflow")
    async def rerun_workflow(self) -> None:
        """Re-run the workflow."""
        loading_indicator = self.query_one("#workflow-detail-loading")
        try:
            self.loading = True
            loading_indicator.display = True

            await self.client.post(f"/repos/{self.repo_name}/actions/runs/{self.run.id}/rerun")

            self.notify("Workflow re-run initiated", severity="information")
            logger.info(f"Re-ran workflow run {self.run.id}")

            # Refresh the workflow data
            await self.refresh_workflow()

        except GitHubCLIError as e:
            logger.error(f"Failed to re-run workflow: {e}")
            self.notify(f"Failed to re-run: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False

    @on(Button.Pressed, "#cancel-run")
    async def cancel_workflow(self) -> None:
        """Cancel the workflow run."""
        loading_indicator = self.query_one("#workflow-detail-loading")
        try:
            self.loading = True
            loading_indicator.display = True

            await self.client.post(f"/repos/{self.repo_name}/actions/runs/{self.run.id}/cancel")

            self.notify("Workflow cancelled", severity="information")
            logger.info(f"Cancelled workflow run {self.run.id}")

            # Refresh the workflow data
            await self.refresh_workflow()

        except GitHubCLIError as e:
            logger.error(f"Failed to cancel workflow: {e}")
            self.notify(f"Failed to cancel: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False

    @on(Button.Pressed, "#open-browser")
    def open_in_browser(self) -> None:
        """Open workflow run in browser."""
        import webbrowser
        try:
            webbrowser.open(self.run.html_url)
            self.notify("Opened in browser", severity="information")
        except Exception as e:
            self.notify(f"Failed to open browser: {e}", severity="error")

    @on(Button.Pressed, "#copy-url")
    def copy_url(self) -> None:
        """Copy workflow URL to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(self.run.html_url)
            self.notify("URL copied to clipboard", severity="information")
        except ImportError:
            self.notify(
                "pyperclip not available - install for clipboard support", severity="warning")
        except Exception as e:
            self.notify(f"Failed to copy URL: {e}", severity="error")

    @on(Button.Pressed, "#download-logs")
    async def download_logs(self) -> None:
        """Download workflow logs."""
        import webbrowser
        try:
            # Open logs URL in browser for download
            logs_url = self.run.logs_url
            if logs_url:
                webbrowser.open(logs_url)
                self.notify("Opening logs for download...",
                            severity="information")
            else:
                self.notify("Logs URL not available", severity="warning")
        except Exception as e:
            self.notify(f"Failed to download logs: {e}", severity="error")

    @on(Button.Pressed, "#refresh-workflow")
    async def refresh_workflow(self) -> None:
        """Refresh workflow run data."""
        self.load_jobs()
        self.notify("Workflow refreshed", severity="information")

    @on(Button.Pressed, "#back-button")
    def close_detail(self) -> None:
        """Close the detail screen."""
        self.dismiss()

    @on(DataTable.RowSelected, "#jobs-table")
    def on_job_selected(self, event: DataTable.RowSelected) -> None:
        """Handle job selection to show job details."""
        if event.row_key:
            job_id = str(event.row_key.value)
            job = next((j for j in self.jobs if str(j.id) == job_id), None)
            if job:
                import webbrowser
                try:
                    webbrowser.open(job.html_url)
                    self.notify("Opened job in browser",
                                severity="information")
                except Exception as e:
                    self.notify(f"Failed to open job: {e}", severity="error")

    def _on_responsive_change(self, old_breakpoint, new_breakpoint) -> None:
        """Handle responsive layout changes."""
        if new_breakpoint:
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        """Apply responsive layout based on current breakpoint."""
        if not self.layout_manager:
            return

        breakpoint = self.layout_manager.get_current_breakpoint()
        if not breakpoint:
            return

        # Apply breakpoint-specific classes
        container = self.query_one("#workflow-detail-container")
        container.remove_class("xs", "sm", "md", "lg", "xl")
        container.add_class(breakpoint.name)

        # Reorganize layout for small screens
        try:
            info_container = self.query_one("#workflow-info")
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


class ActionsManager:
    """GitHub Actions management for the TUI."""

    def __init__(self, client: GitHubClient) -> None:
        self.client = client
        self.workflow_runs: list[WorkflowRun] = []
        self.filtered_runs: list[WorkflowRun] = []
        self.current_repo: str | None = None
        self.loading = False

    async def load_workflow_runs(self, runs_table: DataTable, repo_name: str | None = None) -> None:
        """Load workflow runs from GitHub API."""
        if self.loading:
            return

        self.loading = True
        loading_indicator = runs_table.app.query_one("#actions-loading")
        loading_indicator.display = True

        try:
            logger.info(
                f"Loading workflow runs for repo: {repo_name or 'all'}")

            if repo_name:
                # Load runs for specific repository
                self.current_repo = repo_name
                response = await self.client.get(f"/repos/{repo_name}/actions/runs", params={
                    "per_page": 100
                })
            else:
                # For now, we need a specific repo - GitHub doesn't have a global runs endpoint
                runs_table.app.notify(
                    "Please specify a repository to view workflow runs", severity="warning")
                return

            runs_data = response.data if hasattr(
                response, 'data') else response
            if isinstance(runs_data, dict) and 'workflow_runs' in runs_data:
                runs_data = runs_data['workflow_runs']

            if isinstance(runs_data, list):
                self.workflow_runs = []
                for run_data in runs_data:
                    try:
                        run = WorkflowRun(
                            id=run_data.get('id', 0),
                            name=run_data.get('name'),
                            head_branch=run_data.get('head_branch'),
                            head_sha=run_data.get('head_sha', ''),
                            status=run_data.get('status', ''),
                            conclusion=run_data.get('conclusion'),
                            workflow_id=run_data.get('workflow_id', 0),
                            check_suite_id=run_data.get('check_suite_id', 0),
                            created_at=run_data.get('created_at', ''),
                            updated_at=run_data.get('updated_at', ''),
                            run_started_at=run_data.get('run_started_at'),
                            html_url=run_data.get('html_url', ''),
                            jobs_url=run_data.get('jobs_url', ''),
                            logs_url=run_data.get('logs_url', ''),
                            check_suite_url=run_data.get(
                                'check_suite_url', ''),
                            artifacts_url=run_data.get('artifacts_url', ''),
                            cancel_url=run_data.get('cancel_url', ''),
                            rerun_url=run_data.get('rerun_url', ''),
                            workflow=run_data.get('workflow')
                        )
                        self.workflow_runs.append(run)
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse workflow run data: {e}")
            else:
                self.workflow_runs = []
            self.filtered_runs = self.workflow_runs.copy()

            # Update table
            await self._update_table(runs_table)

            logger.info(f"Loaded {len(self.workflow_runs)} workflow runs")
            runs_table.app.notify(
                f"Loaded {len(self.workflow_runs)} workflow runs", severity="information")

        except GitHubCLIError as e:
            logger.error(f"Failed to load workflow runs: {e}")
            runs_table.app.notify(
                f"Failed to load workflow runs: {e}", severity="error")
        except Exception as e:
            logger.error(f"Unexpected error loading workflow runs: {e}")
            runs_table.app.notify(f"Unexpected error: {e}", severity="error")
        finally:
            self.loading = False
            loading_indicator.display = False

    async def _update_table(self, runs_table: DataTable) -> None:
        """Update the workflow runs table with current data."""
        runs_table.clear()

        for run in self.filtered_runs:
            runs_table.add_row(
                run.display_name,
                run.status.upper(),
                run.branch_info,
                run.created_date,
                key=str(run.id)
            )

    def filter_workflow_runs(self, search_term: str, runs_table: DataTable) -> None:
        """Filter workflow runs based on search term."""
        if not search_term:
            self.filtered_runs = self.workflow_runs.copy()
        else:
            search_lower = search_term.lower()
            self.filtered_runs = [
                run for run in self.workflow_runs
                if search_lower in (run.name or "").lower() or
                search_lower in (run.head_branch or "").lower() or
                search_lower in run.status.lower()
            ]

        asyncio.create_task(self._update_table(runs_table))

    def get_workflow_run_by_id(self, run_id: str) -> WorkflowRun | None:
        """Get workflow run by ID."""
        for run in self.workflow_runs:
            if str(run.id) == run_id:
                return run
        return None


class ActionsWidget(Container):
    """Complete GitHub Actions management widget with adaptive capabilities."""

    def __init__(self, client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> None:
        super().__init__()
        self.client = client
        self.actions_manager = ActionsManager(client)
        self.layout_manager = layout_manager
        if self.layout_manager:
            self.layout_manager.add_resize_callback(self._on_responsive_change)

    def compose(self) -> ComposeResult:
        """Compose the Actions widget with adaptive layout."""
        # Use adaptive container class
        self.add_class("adaptive-container")

        # Search and filter controls - adaptive horizontal layout
        with Horizontal(id="actions-controls", classes="adaptive-horizontal"):
            yield Input(placeholder="Search workflows...", id="actions-search", classes="adaptive-input")
            yield Input(placeholder="Repository (owner/repo)", id="actions-repo-filter", classes="adaptive-input priority-medium")
            yield Button("🔄 Refresh", id="refresh-actions", classes="adaptive-button")
            yield Button("⚙️ Workflows", id="view-workflows", classes="adaptive-button priority-medium")

        # Workflow runs table with adaptive columns
        runs_table = DataTable(
            id="actions-table", classes="workflow-table adaptive-table")
        runs_table.add_columns("Workflow", "Status", "Branch", "Created")
        yield runs_table

        # Loading indicator
        yield LoadingIndicator(id="actions-loading")

    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        runs_table = self.query_one("#actions-table", DataTable)
        loading_indicator = self.query_one("#actions-loading")
        loading_indicator.display = False

        # Apply initial responsive styles if layout manager available
        if self.layout_manager:
            self._apply_responsive_styles()

        # Note: We need a repository to load runs
        self.notify("Enter a repository name to view workflow runs", timeout=5)

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
            controls = self.query_one("#actions-controls")
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
            runs_table = self.query_one("#actions-table", DataTable)

            # Hide/show columns based on screen size
            if breakpoint.name in ["xs", "sm"]:
                # Small screens: Show only essential columns
                self._hide_table_columns(runs_table, ["Branch", "Created"])
            elif breakpoint.name == "md":
                # Medium screens: Hide less important columns
                self._hide_table_columns(runs_table, ["Created"])
            else:
                # Large screens: Show all columns
                self._show_all_table_columns(runs_table)

        except Exception as e:
            logger.warning(f"Could not adapt table columns: {e}")

    def _hide_table_columns(self, table: DataTable, columns: list[str]) -> None:
        """Hide specified table columns."""
        for col in columns:
            table.add_class(f"hide-{col.lower()}")

    def _show_all_table_columns(self, table: DataTable) -> None:
        """Show all table columns."""
        for col in ["branch", "created"]:
            table.remove_class(f"hide-{col}")

    @on(Input.Changed, "#actions-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        runs_table = self.query_one("#actions-table", DataTable)
        self.actions_manager.filter_workflow_runs(event.value, runs_table)

    @on(Input.Submitted, "#actions-repo-filter")
    async def on_repo_filter_submitted(self, event: Input.Submitted) -> None:
        """Handle repository filter submission."""
        runs_table = self.query_one("#actions-table", DataTable)
        repo_name = event.value.strip() if event.value else None

        if repo_name:
            await self.actions_manager.load_workflow_runs(runs_table, repo_name)
        else:
            self.notify(
                "Please enter a repository name (owner/repo)", severity="warning")

    @on(Button.Pressed, "#refresh-actions")
    async def on_refresh_actions(self) -> None:
        """Handle refresh button press."""
        runs_table = self.query_one("#actions-table", DataTable)
        repo_filter = self.query_one("#actions-repo-filter", Input)
        repo_name = repo_filter.value.strip() if repo_filter.value else None

        if repo_name:
            await self.actions_manager.load_workflow_runs(runs_table, repo_name)
        else:
            self.notify("Please enter a repository name first",
                        severity="warning")

    @on(Button.Pressed, "#view-workflows")
    def on_view_workflows(self) -> None:
        """Handle view workflows button press."""
        self.notify("Workflow definitions viewer coming soon",
                    severity="information")

    @on(DataTable.RowSelected, "#actions-table")
    def on_run_selected(self, event: DataTable.RowSelected) -> None:
        """Handle workflow run selection."""
        if event.row_key:
            run = self.actions_manager.get_workflow_run_by_id(
                str(event.row_key.value))
            if run:
                repo_name = self.actions_manager.current_repo or "unknown/repo"
                # Pass layout manager to detail screen if available
                self.app.push_screen(WorkflowRunDetailScreen(
                    run, self.client, repo_name, self.layout_manager))


# Function to replace placeholder in main TUI app
def create_actions_widget(client: GitHubClient, layout_manager: ResponsiveLayoutManager | None = None) -> ActionsWidget:
    """Create a GitHub Actions management widget with responsive capabilities."""
    return ActionsWidget(client, layout_manager)
