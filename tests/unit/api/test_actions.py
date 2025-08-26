"""
Unit tests for GitHub Actions API module.

Tests the ActionsAPI class and its methods for managing GitHub Actions workflows.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from github_cli.api.actions import ActionsAPI
from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
from github_cli.ui.terminal import TerminalUI
from github_cli.models.workflow import Workflow, WorkflowRun, WorkflowJob
from github_cli.utils.exceptions import GitHubCLIError


@pytest.mark.unit
@pytest.mark.api
class TestActionsAPI:
    """Test cases for ActionsAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        self.mock_ui = Mock(spec=TerminalUI)
        self.actions_api = ActionsAPI(self.mock_client, self.mock_ui)

    def test_actions_api_initialization(self):
        """Test ActionsAPI initialization."""
        assert self.actions_api.client == self.mock_client
        assert self.actions_api.ui == self.mock_ui

    def test_actions_api_initialization_without_ui(self):
        """Test ActionsAPI initialization without UI."""
        api = ActionsAPI(self.mock_client)
        assert api.client == self.mock_client
        assert api.ui is None

    @pytest.mark.asyncio
    async def test_list_workflows_success(self, sample_workflow_data):
        """Test successful workflow listing."""
        repo = "testuser/test-repo"
        workflows_data = {"workflows": [sample_workflow_data]}
        
        mock_response = APIResponse(
            status_code=200,
            data=workflows_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.list_workflows(repo)
        
        assert len(result) == 1
        assert isinstance(result[0], Workflow)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/workflows")

    @pytest.mark.asyncio
    async def test_list_workflows_empty(self):
        """Test listing workflows when none exist."""
        repo = "testuser/test-repo"
        workflows_data = {"workflows": []}
        
        mock_response = APIResponse(
            status_code=200,
            data=workflows_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.list_workflows(repo)
        
        assert len(result) == 0
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/workflows")

    @pytest.mark.asyncio
    async def test_get_workflow_success(self, sample_workflow_data):
        """Test successful workflow retrieval."""
        repo = "testuser/test-repo"
        workflow_id = 123456
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_workflow_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.get_workflow(repo, workflow_id)
        
        assert isinstance(result, Workflow)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/workflows/{workflow_id}")

    @pytest.mark.asyncio
    async def test_get_workflow_by_filename(self, sample_workflow_data):
        """Test getting workflow by filename."""
        repo = "testuser/test-repo"
        workflow_filename = "ci.yml"
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_workflow_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.get_workflow(repo, workflow_filename)
        
        assert isinstance(result, Workflow)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/workflows/{workflow_filename}")

    @pytest.mark.asyncio
    async def test_list_workflow_runs_all(self, sample_workflow_run_data):
        """Test listing all workflow runs for a repository."""
        repo = "testuser/test-repo"
        runs_data = {"workflow_runs": [sample_workflow_run_data]}
        
        mock_response = APIResponse(
            status_code=200,
            data=runs_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.list_workflow_runs(repo)
        
        assert len(result) == 1
        assert isinstance(result[0], WorkflowRun)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/runs", params={})

    @pytest.mark.asyncio
    async def test_list_workflow_runs_specific_workflow(self, sample_workflow_run_data):
        """Test listing workflow runs for a specific workflow."""
        repo = "testuser/test-repo"
        workflow_id = 123456
        runs_data = {"workflow_runs": [sample_workflow_run_data]}
        
        mock_response = APIResponse(
            status_code=200,
            data=runs_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.list_workflow_runs(repo, workflow_id)
        
        assert len(result) == 1
        assert isinstance(result[0], WorkflowRun)
        self.mock_client.get.assert_called_once_with(
            f"repos/{repo}/actions/workflows/{workflow_id}/runs", 
            params={}
        )

    @pytest.mark.asyncio
    async def test_list_workflow_runs_with_filters(self, sample_workflow_run_data):
        """Test listing workflow runs with filters."""
        repo = "testuser/test-repo"
        branch = "main"
        event = "push"
        status = "completed"
        runs_data = {"workflow_runs": [sample_workflow_run_data]}
        
        mock_response = APIResponse(
            status_code=200,
            data=runs_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.list_workflow_runs(
            repo, branch=branch, event=event, status=status
        )
        
        assert len(result) == 1
        self.mock_client.get.assert_called_once_with(
            f"repos/{repo}/actions/runs",
            params={"branch": branch, "event": event, "status": status}
        )

    @pytest.mark.asyncio
    async def test_get_workflow_run_success(self, sample_workflow_run_data):
        """Test successful workflow run retrieval."""
        repo = "testuser/test-repo"
        run_id = 789012
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_workflow_run_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.get_workflow_run(repo, run_id)
        
        assert isinstance(result, WorkflowRun)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/runs/{run_id}")

    @pytest.mark.asyncio
    async def test_cancel_workflow_run_success(self):
        """Test successful workflow run cancellation."""
        repo = "testuser/test-repo"
        run_id = 789012
        
        mock_response = APIResponse(
            status_code=202,
            data={},
            headers={},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.actions_api.cancel_workflow_run(repo, run_id)
        
        assert result is True
        self.mock_client.post.assert_called_once_with(f"repos/{repo}/actions/runs/{run_id}/cancel")

    @pytest.mark.asyncio
    async def test_rerun_workflow_success(self):
        """Test successful workflow re-run."""
        repo = "testuser/test-repo"
        run_id = 789012
        
        mock_response = APIResponse(
            status_code=201,
            data={},
            headers={},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.post.return_value = mock_response
        
        result = await self.actions_api.rerun_workflow(repo, run_id)
        
        assert result is True
        self.mock_client.post.assert_called_once_with(f"repos/{repo}/actions/runs/{run_id}/rerun")

    @pytest.mark.asyncio
    async def test_get_workflow_run_logs_success(self):
        """Test successful workflow run logs retrieval."""
        repo = "testuser/test-repo"
        run_id = 789012
        expected_logs = "2023-12-01T00:00:00.000Z [INFO] Starting workflow...\n2023-12-01T00:01:00.000Z [INFO] Workflow completed successfully."
        
        mock_response = APIResponse(
            status_code=200,
            data=expected_logs,
            headers={"content-type": "application/zip"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client._request.return_value = mock_response
        
        result = await self.actions_api.get_workflow_run_logs(repo, run_id)

        assert result == mock_response.data
        self.mock_client._request.assert_called_once_with(
            "GET", 
            f"repos/{repo}/actions/runs/{run_id}/logs",
            headers={"Accept": "application/vnd.github.v3.raw"}
        )

    @pytest.mark.asyncio
    async def test_list_workflow_run_jobs_success(self, sample_workflow_job_data):
        """Test successful workflow run jobs listing."""
        repo = "testuser/test-repo"
        run_id = 789012
        jobs_data = {"jobs": [sample_workflow_job_data]}
        
        mock_response = APIResponse(
            status_code=200,
            data=jobs_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.list_workflow_run_jobs(repo, run_id)
        
        assert len(result) == 1
        assert isinstance(result[0], WorkflowJob)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/runs/{run_id}/jobs")

    @pytest.mark.asyncio
    async def test_get_workflow_job_success(self, sample_workflow_job_data):
        """Test successful workflow job retrieval."""
        repo = "testuser/test-repo"
        job_id = 345678
        
        mock_response = APIResponse(
            status_code=200,
            data=sample_workflow_job_data,
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client.get.return_value = mock_response
        
        result = await self.actions_api.get_workflow_job(repo, job_id)
        
        assert isinstance(result, WorkflowJob)
        self.mock_client.get.assert_called_once_with(f"repos/{repo}/actions/jobs/{job_id}")

    @pytest.mark.asyncio
    async def test_get_workflow_job_logs_success(self):
        """Test successful workflow job logs retrieval."""
        repo = "testuser/test-repo"
        job_id = 345678
        expected_logs = "2023-12-01T00:00:00.000Z [INFO] Starting job...\n2023-12-01T00:01:00.000Z [INFO] Job completed successfully."
        
        mock_response = APIResponse(
            status_code=200,
            data=expected_logs,
            headers={"content-type": "text/plain"},
            rate_limit=RateLimitInfo()
        )
        
        self.mock_client._request.return_value = mock_response
        
        result = await self.actions_api.get_workflow_job_logs(repo, job_id)

        assert result == mock_response.data
        self.mock_client._request.assert_called_once_with(
            "GET",
            f"repos/{repo}/actions/jobs/{job_id}/logs",
            headers={"Accept": "application/vnd.github.v3.raw"}
        )

    @pytest.mark.asyncio
    async def test_list_workflows_api_error(self):
        """Test handling API error during workflow listing."""
        repo = "testuser/test-repo"
        
        self.mock_client.get.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to list workflows: API Error"):
            await self.actions_api.list_workflows(repo)

    @pytest.mark.asyncio
    async def test_cancel_workflow_run_api_error(self):
        """Test handling API error during workflow run cancellation."""
        repo = "testuser/test-repo"
        run_id = 789012
        
        self.mock_client.post.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to cancel workflow run: API Error"):
            await self.actions_api.cancel_workflow_run(repo, run_id)

    @pytest.mark.asyncio
    async def test_get_workflow_run_logs_api_error(self):
        """Test handling API error during workflow run logs retrieval."""
        repo = "testuser/test-repo"
        run_id = 789012
        
        self.mock_client._request.side_effect = GitHubCLIError("API Error")
        
        with pytest.raises(GitHubCLIError, match="Failed to get workflow run logs: API Error"):
            await self.actions_api.get_workflow_run_logs(repo, run_id)
