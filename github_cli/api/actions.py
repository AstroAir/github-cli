"""
GitHub Actions API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError
from github_cli.models.workflow import Workflow, WorkflowRun, WorkflowJob
from rich.table import Table
from rich import box


class ActionsAPI:
    """API for working with GitHub Actions"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def list_workflows(self, repo: str) -> List[Workflow]:
        """List workflows for a repository"""
        endpoint = f"repos/{repo}/actions/workflows"

        try:
            response = await self.client.get(endpoint)
            return [Workflow.from_json(wf) for wf in response.get("workflows", [])]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list workflows: {str(e)}")

    async def get_workflow(self, repo: str, workflow_id: Union[int, str]) -> Workflow:
        """Get a workflow by ID or filename"""
        endpoint = f"repos/{repo}/actions/workflows/{workflow_id}"

        try:
            response = await self.client.get(endpoint)
            return Workflow.from_json(response)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get workflow: {str(e)}")

    async def list_workflow_runs(self, repo: str, workflow_id: Optional[Union[int, str]] = None,
                                 branch: Optional[str] = None,
                                 event: Optional[str] = None,
                                 status: Optional[str] = None) -> List[WorkflowRun]:
        """List workflow runs for a repository"""
        if workflow_id:
            endpoint = f"repos/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            endpoint = f"repos/{repo}/actions/runs"

        params = {}
        if branch:
            params["branch"] = branch
        if event:
            params["event"] = event
        if status:
            params["status"] = status

        try:
            response = await self.client.get(endpoint, params=params)
            return [WorkflowRun.from_json(run) for run in response.get("workflow_runs", [])]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list workflow runs: {str(e)}")

    async def get_workflow_run(self, repo: str, run_id: int) -> WorkflowRun:
        """Get a workflow run by ID"""
        endpoint = f"repos/{repo}/actions/runs/{run_id}"

        try:
            response = await self.client.get(endpoint)
            return WorkflowRun.from_json(response)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get workflow run: {str(e)}")

    async def cancel_workflow_run(self, repo: str, run_id: int) -> bool:
        """Cancel a workflow run"""
        endpoint = f"repos/{repo}/actions/runs/{run_id}/cancel"

        try:
            await self.client.post(endpoint)
            return True
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to cancel workflow run: {str(e)}")

    async def rerun_workflow(self, repo: str, run_id: int) -> bool:
        """Re-run a workflow"""
        endpoint = f"repos/{repo}/actions/runs/{run_id}/rerun"

        try:
            await self.client.post(endpoint)
            return True
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to re-run workflow: {str(e)}")

    async def get_workflow_run_logs(self, repo: str, run_id: int) -> str:
        """Get logs for a workflow run"""
        endpoint = f"repos/{repo}/actions/runs/{run_id}/logs"
        headers = {"Accept": "application/vnd.github.v3.raw"}

        try:
            return await self.client._request("GET", endpoint, headers=headers)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get workflow run logs: {str(e)}")

    async def list_workflow_run_jobs(self, repo: str, run_id: int) -> List[WorkflowJob]:
        """List jobs for a workflow run"""
        endpoint = f"repos/{repo}/actions/runs/{run_id}/jobs"

        try:
            response = await self.client.get(endpoint)
            return [WorkflowJob.from_json(job) for job in response.get("jobs", [])]
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list workflow run jobs: {str(e)}")

    async def get_workflow_job(self, repo: str, job_id: int) -> WorkflowJob:
        """Get a workflow job by ID"""
        endpoint = f"repos/{repo}/actions/jobs/{job_id}"

        try:
            response = await self.client.get(endpoint)
            return WorkflowJob.from_json(response)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get workflow job: {str(e)}")

    async def get_workflow_job_logs(self, repo: str, job_id: int) -> str:
        """Get logs for a workflow job"""
        endpoint = f"repos/{repo}/actions/jobs/{job_id}/logs"
        headers = {"Accept": "application/vnd.github.v3.raw"}

        try:
            return await self.client._request("GET", endpoint, headers=headers)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get workflow job logs: {str(e)}")


# Handler function for CLI commands
async def handle_actions_command(args: Dict[str, Any], client: GitHubClient, ui: TerminalUI) -> None:
    """Handle GitHub Actions commands from the CLI"""
    actions_api = ActionsAPI(client, ui)

    action = args.get("action")
    repo = args.get("repo")

    if not repo:
        ui.display_error("Repository name required (format: owner/repo)")
        return

    if action == "list":
        ui.display_info(f"Fetching workflows for {repo}...")
        try:
            workflows = await actions_api.list_workflows(repo)
            _display_workflows(workflows, ui)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "runs":
        workflow_id = args.get("workflow")
        branch = args.get("branch")
        status = args.get("status")

        try:
            ui.display_info(f"Fetching workflow runs for {repo}...")
            runs = await actions_api.list_workflow_runs(repo, workflow_id, branch, status=status)
            _display_workflow_runs(runs, ui)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "view-run":
        run_id = args.get("id")
        if not run_id:
            ui.display_error("Run ID required")
            return

        try:
            run_id = int(run_id)
        except ValueError:
            ui.display_error("Run ID must be a valid integer")
            return

        try:
            ui.display_info(f"Fetching workflow run #{run_id} for {repo}...")
            run = await actions_api.get_workflow_run(repo, run_id)
            _display_workflow_run_details(run, ui)

            # Get jobs
            jobs = await actions_api.list_workflow_run_jobs(repo, run_id)
            ui.display_heading("Jobs")
            _display_workflow_jobs(jobs, ui)

            # Ask if user wants to see logs
            if ui.confirm("View logs", default=False):
                job_id = None
                if len(jobs) > 1:
                    # Ask which job's logs to view
                    choices = [f"{job.id} - {job.name}" for job in jobs]
                    choice = ui.prompt(
                        "Which job logs to view", choices=choices)
                    if choice:
                        job_id = int(choice.split(" - ")[0])
                else:
                    job_id = jobs[0].id if jobs else None

                if job_id:
                    ui.display_info(f"Fetching logs for job #{job_id}...")
                    logs = await actions_api.get_workflow_job_logs(repo, job_id)
                    ui.display_heading(f"Logs for Job #{job_id}")
                    ui.console.print(logs)

        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "cancel":
        run_id = args.get("id")
        if not run_id:
            ui.display_error("Run ID required")
            return

        try:
            run_id = int(run_id)
        except ValueError:
            ui.display_error("Run ID must be a valid integer")
            return

        # Confirm cancellation
        confirmed = ui.confirm(
            f"Are you sure you want to cancel workflow run #{run_id}", default=False)
        if not confirmed:
            ui.display_info("Cancellation aborted")
            return

        try:
            ui.display_info(f"Cancelling workflow run #{run_id}...")
            success = await actions_api.cancel_workflow_run(repo, run_id)
            if success:
                ui.display_success(f"Workflow run #{run_id} cancelled")
            else:
                ui.display_error("Failed to cancel workflow run")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "rerun":
        run_id = args.get("id")
        if not run_id:
            ui.display_error("Run ID required")
            return

        try:
            run_id = int(run_id)
        except ValueError:
            ui.display_error("Run ID must be a valid integer")
            return

        try:
            ui.display_info(f"Re-running workflow run #{run_id}...")
            success = await actions_api.rerun_workflow(repo, run_id)
            if success:
                ui.display_success(f"Workflow run #{run_id} re-run initiated")
            else:
                ui.display_error("Failed to re-run workflow")
        except GitHubCLIError as e:
            ui.display_error(str(e))

    else:
        ui.display_error(f"Unknown GitHub Actions command: {action}")
        ui.display_info(
            "Available actions: list, runs, view-run, cancel, rerun")


def _display_workflows(workflows: List[Workflow], ui: TerminalUI) -> None:
    """Display list of workflows"""
    if not workflows:
        ui.display_info("No workflows found")
        return

    table = Table(title="GitHub Workflows", box=box.ROUNDED)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Path", style="blue")
    table.add_column("State", style="yellow")

    for wf in workflows:
        state_style = "green" if wf.state == "active" else "red"
        table.add_row(
            str(wf.id),
            wf.name,
            wf.path,
            f"[{state_style}]{wf.state}[/{state_style}]"
        )

    ui.console.print(table)


def _display_workflow_runs(runs: List[WorkflowRun], ui: TerminalUI) -> None:
    """Display list of workflow runs"""
    if not runs:
        ui.display_info("No workflow runs found")
        return

    table = Table(title="Workflow Runs", box=box.ROUNDED)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Workflow", style="green")
    table.add_column("Branch", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Conclusion", style="magenta")
    table.add_column("Created", style="green")

    for run in runs:
        # Style status and conclusion
        status_style = "yellow"
        if run.status == "completed":
            status_style = "green"

        conclusion_style = "yellow"
        if run.conclusion == "success":
            conclusion_style = "green"
        elif run.conclusion == "failure":
            conclusion_style = "red"

        created = run.created_date.strftime("%Y-%m-%d %H:%M")

        table.add_row(
            str(run.id),
            run.name or f"Workflow #{run.workflow_id}",
            run.head_branch,
            f"[{status_style}]{run.status}[/{status_style}]",
            f"[{conclusion_style}]{run.conclusion or 'pending'}[/{conclusion_style}]",
            created
        )

    ui.console.print(table)


def _display_workflow_run_details(run: WorkflowRun, ui: TerminalUI) -> None:
    """Display detailed information about a workflow run"""
    ui.display_heading(f"Workflow Run: {run.name or f'Run #{run.id}'}")

    table = Table(box=box.SIMPLE)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    # Style status and conclusion
    status_style = "yellow"
    if run.status == "completed":
        status_style = "green"

    conclusion_style = "yellow"
    if run.conclusion == "success":
        conclusion_style = "green"
    elif run.conclusion == "failure":
        conclusion_style = "red"

    table.add_row("ID", str(run.id))
    table.add_row("Workflow ID", str(run.workflow_id))
    table.add_row("Run Number", str(run.run_number))
    table.add_row("Status", f"[{status_style}]{run.status}[/{status_style}]")
    table.add_row(
        "Conclusion", f"[{conclusion_style}]{run.conclusion or 'pending'}[/{conclusion_style}]")
    table.add_row("Branch", run.head_branch)
    table.add_row("Commit", run.head_sha)
    table.add_row("Event", run.event)
    table.add_row("Created", run.created_date.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Updated", run.updated_date.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("URL", run.html_url)

    ui.console.print(table)


def _display_workflow_jobs(jobs: List[WorkflowJob], ui: TerminalUI) -> None:
    """Display jobs for a workflow run"""
    if not jobs:
        ui.display_info("No jobs found for this workflow run")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Conclusion", style="magenta")
    table.add_column("Started", style="blue")
    table.add_column("Duration", style="green", justify="right")

    for job in jobs:
        # Style status and conclusion
        status_style = "yellow"
        if job.status == "completed":
            status_style = "green"

        conclusion_style = "yellow"
        if job.conclusion == "success":
            conclusion_style = "green"
        elif job.conclusion == "failure":
            conclusion_style = "red"

        # Format times
        started = "Not started"
        duration = "N/A"

        if job.started_date:
            started = job.started_date.strftime("%Y-%m-%d %H:%M")

            if job.completed_date:
                delta = job.completed_date - job.started_date
                minutes, seconds = divmod(delta.total_seconds(), 60)
                duration = f"{int(minutes)}m {int(seconds)}s"

        table.add_row(
            str(job.id),
            job.name,
            f"[{status_style}]{job.status}[/{status_style}]",
            f"[{conclusion_style}]{job.conclusion or 'pending'}[/{conclusion_style}]",
            started,
            duration
        )

    ui.console.print(table)
