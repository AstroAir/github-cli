from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from textual import on, work
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


class WorkflowRun(BaseModel):
    """GitHub Actions workflow run data model."""
    id: int
    name: str | None = None
    head_branch: str | None = None
    head_sha: str
    status: str  # queued, in_progress, completed
    conclusion: str | None = None  # success, failure, neutral, cancelled, timed_out, action_required, stale
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
        
        workflow_name = self.name or (self.workflow.get('name') if self.workflow else 'Unknown')
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
    """Detailed view for a workflow run."""
    
    def __init__(self, run: WorkflowRun, client: GitHubClient, repo_name: str) -> None:
        super().__init__()
        self.run = run
        self.client = client
        self.repo_name = repo_name
        self.jobs: list[WorkflowJob] = []
        self.loading = False
    
    def compose(self):
        """Compose the workflow run detail screen."""
        with Container(id="workflow-detail-container"):
            yield Static(f"Workflow Run #{self.run.id}: {self.run.display_name}", id="workflow-title")
            
            with Horizontal(id="workflow-info"):
                with Vertical(id="workflow-basic-info"):
                    yield Label(f"Status: {self.run.status.upper()}")
                    if self.run.conclusion:
                        yield Label(f"Conclusion: {self.run.conclusion.upper()}")
                    yield Label(f"Branch: {self.run.branch_info}")
                    yield Label(f"Created: {self.run.created_date}")
                
                with Vertical(id="workflow-progress"):
                    if self.run.status == "in_progress":
                        yield ProgressBar(id="workflow-progress-bar")
                        yield Label("Workflow in progress...")
                    elif self.run.status == "completed":
                        yield Label(f"�Completed: {self.run.conclusion or 'Unknown'}")
                    else:
                        yield Label(f"�Status: {self.run.status}")
            
            with TabbedContent(id="workflow-tabs"):
                with TabPane("Jobs", id="jobs-tab"):
                    jobs_table = DataTable(id="jobs-table")
                    jobs_table.add_columns("Job", "Status", "Started", "Duration")
                    yield jobs_table
                
                with TabPane("Logs", id="logs-tab"):
                    yield Log(id="workflow-logs")
                
                with TabPane("Artifacts", id="artifacts-tab"):
                    yield Placeholder("Artifacts viewer coming soon")
            
            with Horizontal(id="workflow-actions"):
                if self.run.can_rerun:
                    yield Button("🔄 Re-run", id="rerun-workflow")
                if self.run.can_cancel:
                    yield Button("🚫 Cancel", id="cancel-workflow", variant="error")
                
                yield Button("🌐 Open in Browser", id="open-browser")
                yield Button("📋 Copy URL", id="copy-url")
                yield Button("🔄 Refresh", id="refresh-workflow")
                yield Button("�Close", id="close-detail", variant="error")
            
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
            
            jobs_data = response.data if hasattr(response, 'data') else response
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
            
            logger.info(f"Loaded {len(self.jobs)} jobs for workflow run {self.run.id}")
            
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
                    started_dt = datetime.fromisoformat(job.started_at.replace('Z', '+00:00'))
                    started_time = started_dt.strftime('%H:%M:%S')
                    
                    if job.completed_at:
                        completed_dt = datetime.fromisoformat(job.completed_at.replace('Z', '+00:00'))
                        duration_seconds = (completed_dt - started_dt).total_seconds()
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
    
    @on(Button.Pressed, "#cancel-workflow")
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
            self.notify("pyperclip not available - install for clipboard support", severity="warning")
        except Exception as e:
            self.notify(f"Failed to copy URL: {e}", severity="error")
    
    @on(Button.Pressed, "#refresh-workflow")
    async def refresh_workflow(self) -> None:
        """Refresh workflow run data."""
        self.load_jobs()
        self.notify("Workflow refreshed", severity="information")
    
    @on(Button.Pressed, "#close-detail")
    def close_detail(self) -> None:
        """Close the detail screen."""
        self.dismiss()


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
            logger.info(f"Loading workflow runs for repo: {repo_name or 'all'}")
            
            if repo_name:
                # Load runs for specific repository
                self.current_repo = repo_name
                response = await self.client.get(f"/repos/{repo_name}/actions/runs", params={
                    "per_page": 100
                })
            else:
                # For now, we need a specific repo - GitHub doesn't have a global runs endpoint
                runs_table.app.notify("Please specify a repository to view workflow runs", severity="warning")
                return
            
            runs_data = response.data if hasattr(response, 'data') else response
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
                            check_suite_url=run_data.get('check_suite_url', ''),
                            artifacts_url=run_data.get('artifacts_url', ''),
                            cancel_url=run_data.get('cancel_url', ''),
                            rerun_url=run_data.get('rerun_url', ''),
                            workflow=run_data.get('workflow')
                        )
                        self.workflow_runs.append(run)
                    except Exception as e:
                        logger.warning(f"Failed to parse workflow run data: {e}")
            else:
                self.workflow_runs = []
            self.filtered_runs = self.workflow_runs.copy()
            
            # Update table
            await self._update_table(runs_table)
            
            logger.info(f"Loaded {len(self.workflow_runs)} workflow runs")
            runs_table.app.notify(f"Loaded {len(self.workflow_runs)} workflow runs", severity="information")
            
        except GitHubCLIError as e:
            logger.error(f"Failed to load workflow runs: {e}")
            runs_table.app.notify(f"Failed to load workflow runs: {e}", severity="error")
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
    """Complete GitHub Actions management widget."""
    
    def __init__(self, client: GitHubClient) -> None:
        super().__init__()
        self.client = client
        self.actions_manager = ActionsManager(client)
    
    def compose(self):
        """Compose the Actions widget."""
        # Search and filter controls
        with Horizontal(id="actions-controls"):
            yield Input(placeholder="Search workflows...", id="actions-search")
            yield Input(placeholder="Repository (owner/repo)", id="actions-repo-filter")
            yield Button("🔄 Refresh", id="refresh-actions")
            yield Button("⚙️ Workflows", id="view-workflows")
        
        # Workflow runs table
        runs_table = DataTable(id="actions-table", classes="workflow-table")
        runs_table.add_columns("Workflow", "Status", "Branch", "Created")
        yield runs_table
        
        # Loading indicator
        yield LoadingIndicator(id="actions-loading")
    
    async def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        runs_table = self.query_one("#actions-table", DataTable)
        loading_indicator = self.query_one("#actions-loading")
        loading_indicator.display = False
        
        # Note: We need a repository to load runs
        self.notify("Enter a repository name to view workflow runs", timeout=5)
    
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
            self.notify("Please enter a repository name (owner/repo)", severity="warning")
    
    @on(Button.Pressed, "#refresh-actions")
    async def on_refresh_actions(self) -> None:
        """Handle refresh button press."""
        runs_table = self.query_one("#actions-table", DataTable)
        repo_filter = self.query_one("#actions-repo-filter", Input)
        repo_name = repo_filter.value.strip() if repo_filter.value else None
        
        if repo_name:
            await self.actions_manager.load_workflow_runs(runs_table, repo_name)
        else:
            self.notify("Please enter a repository name first", severity="warning")
    
    @on(Button.Pressed, "#view-workflows")
    def on_view_workflows(self) -> None:
        """Handle view workflows button press."""
        self.notify("Workflow definitions viewer coming soon", severity="information")
    
    @on(DataTable.RowSelected, "#actions-table")
    def on_run_selected(self, event: DataTable.RowSelected) -> None:
        """Handle workflow run selection."""
        if event.row_key:
            run = self.actions_manager.get_workflow_run_by_id(str(event.row_key.value))
            if run:
                repo_name = self.actions_manager.current_repo or "unknown/repo"
                self.app.push_screen(WorkflowRunDetailScreen(run, self.client, repo_name))


# Function to replace placeholder in main TUI app
def create_actions_widget(client: GitHubClient) -> ActionsWidget:
    """Create a GitHub Actions management widget."""
    return ActionsWidget(client)
