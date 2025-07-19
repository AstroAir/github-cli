# GitHub Actions API

The `ActionsAPI` provides comprehensive GitHub Actions workflow management including workflow listing, run monitoring, job tracking, and log access.

## 🏗️ Class Overview

```python
class ActionsAPI:
    """API for working with GitHub Actions"""
    
    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui
```

## 📚 Core Methods

### Workflow Management

#### List Workflows
```python
async def list_workflows(self, repo: str) -> List[Workflow]
```

**Parameters:**
- `repo`: Repository in format "owner/repo"

**Example:**
```python
actions_api = ActionsAPI(client)

# List all workflows
workflows = await actions_api.list_workflows("owner/repo")

for workflow in workflows:
    print(f"Workflow: {workflow.name}")
    print(f"  ID: {workflow.id}")
    print(f"  Path: {workflow.path}")
    print(f"  State: {workflow.state}")
```

#### Get Workflow
```python
async def get_workflow(self, repo: str, workflow_id: Union[int, str]) -> Workflow
```

**Parameters:**
- `workflow_id`: Workflow ID or filename

**Example:**
```python
# Get workflow by ID
workflow = await actions_api.get_workflow("owner/repo", 12345)

# Get workflow by filename
workflow = await actions_api.get_workflow("owner/repo", "ci.yml")
```

### Workflow Runs

#### List Workflow Runs
```python
async def list_workflow_runs(
    self,
    repo: str,
    workflow_id: Optional[Union[int, str]] = None,
    branch: Optional[str] = None,
    event: Optional[str] = None,
    status: Optional[str] = None
) -> List[WorkflowRun]
```

**Parameters:**
- `workflow_id`: Filter by specific workflow
- `branch`: Filter by branch
- `event`: Filter by trigger event
- `status`: Filter by status (`queued`, `in_progress`, `completed`)

**Example:**
```python
# List all workflow runs
runs = await actions_api.list_workflow_runs("owner/repo")

# List runs for specific workflow
ci_runs = await actions_api.list_workflow_runs("owner/repo", "ci.yml")

# List runs for main branch
main_runs = await actions_api.list_workflow_runs(
    "owner/repo",
    branch="main"
)

# List failed runs
failed_runs = await actions_api.list_workflow_runs(
    "owner/repo",
    status="completed"
)
failed_runs = [r for r in failed_runs if r.conclusion == "failure"]
```

#### Get Workflow Run
```python
async def get_workflow_run(self, repo: str, run_id: int) -> WorkflowRun
```

**Example:**
```python
# Get specific workflow run
run = await actions_api.get_workflow_run("owner/repo", 123456)

print(f"Run #{run.run_number}: {run.name}")
print(f"Status: {run.status}")
print(f"Conclusion: {run.conclusion}")
print(f"Branch: {run.head_branch}")
print(f"Commit: {run.head_sha}")
```

### Workflow Run Control

#### Cancel Workflow Run
```python
async def cancel_workflow_run(self, repo: str, run_id: int) -> bool
```

**Example:**
```python
# Cancel a running workflow
success = await actions_api.cancel_workflow_run("owner/repo", 123456)
if success:
    print("Workflow run cancelled")
```

#### Re-run Workflow
```python
async def rerun_workflow(self, repo: str, run_id: int) -> bool
```

**Example:**
```python
# Re-run a failed workflow
success = await actions_api.rerun_workflow("owner/repo", 123456)
if success:
    print("Workflow re-run initiated")
```

### Workflow Jobs

#### List Workflow Run Jobs
```python
async def list_workflow_run_jobs(self, repo: str, run_id: int) -> List[WorkflowJob]
```

**Example:**
```python
# Get jobs for a workflow run
jobs = await actions_api.list_workflow_run_jobs("owner/repo", 123456)

for job in jobs:
    print(f"Job: {job.name}")
    print(f"  Status: {job.status}")
    print(f"  Conclusion: {job.conclusion}")
    if job.started_date and job.completed_date:
        duration = job.completed_date - job.started_date
        print(f"  Duration: {duration}")
```

#### Get Workflow Job
```python
async def get_workflow_job(self, repo: str, job_id: int) -> WorkflowJob
```

**Example:**
```python
# Get specific job details
job = await actions_api.get_workflow_job("owner/repo", 789012)

print(f"Job: {job.name}")
print(f"Runner: {job.runner_name}")
print(f"Steps: {len(job.steps)}")

for step in job.steps:
    print(f"  Step: {step['name']} - {step['conclusion']}")
```

### Logs

#### Get Workflow Run Logs
```python
async def get_workflow_run_logs(self, repo: str, run_id: int) -> str
```

**Example:**
```python
# Download all logs for a workflow run
logs = await actions_api.get_workflow_run_logs("owner/repo", 123456)
print("Complete workflow logs:")
print(logs)
```

#### Get Workflow Job Logs
```python
async def get_workflow_job_logs(self, repo: str, job_id: int) -> str
```

**Example:**
```python
# Get logs for specific job
job_logs = await actions_api.get_workflow_job_logs("owner/repo", 789012)
print("Job logs:")
print(job_logs)
```

## 🎯 CLI Command Handler

```python
async def handle_actions_command(
    args: Dict[str, Any], 
    client: GitHubClient, 
    ui: TerminalUI
) -> None
```

### Supported Commands

#### List Workflows
```bash
github-cli actions list --repo OWNER/REPO
```

#### List Workflow Runs
```bash
github-cli actions runs --repo OWNER/REPO [--workflow WORKFLOW] [--branch BRANCH] [--status STATUS]
```

#### View Workflow Run
```bash
github-cli actions view-run --repo OWNER/REPO --id RUN_ID
```

#### Cancel Workflow Run
```bash
github-cli actions cancel --repo OWNER/REPO --id RUN_ID
```

#### Re-run Workflow
```bash
github-cli actions rerun --repo OWNER/REPO --id RUN_ID
```

## 📊 Data Models

### Workflow Model
```python
@dataclass
class Workflow:
    id: int
    name: str
    path: str
    state: str
    created_at: datetime
    updated_at: datetime
    url: str
    html_url: str
    badge_url: str
```

### WorkflowRun Model
```python
@dataclass
class WorkflowRun:
    id: int
    name: Optional[str]
    workflow_id: int
    run_number: int
    status: str
    conclusion: Optional[str]
    head_branch: str
    head_sha: str
    event: str
    created_date: datetime
    updated_date: datetime
    html_url: str
    jobs_url: str
    logs_url: str
```

### WorkflowJob Model
```python
@dataclass
class WorkflowJob:
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    started_date: Optional[datetime]
    completed_date: Optional[datetime]
    runner_id: Optional[int]
    runner_name: Optional[str]
    runner_group_id: Optional[int]
    runner_group_name: Optional[str]
    steps: List[Dict[str, Any]]
    html_url: str
```

## 🎨 Display Functions

The module includes rich display functions for terminal output:

### Display Workflows
```python
def _display_workflows(workflows: List[Workflow], ui: TerminalUI) -> None
```

### Display Workflow Runs
```python
def _display_workflow_runs(runs: List[WorkflowRun], ui: TerminalUI) -> None
```

### Display Workflow Run Details
```python
def _display_workflow_run_details(run: WorkflowRun, ui: TerminalUI) -> None
```

### Display Workflow Jobs
```python
def _display_workflow_jobs(jobs: List[WorkflowJob], ui: TerminalUI) -> None
```

## 🚨 Error Handling

```python
try:
    workflows = await actions_api.list_workflows("owner/repo")
except NotFoundError:
    print("Repository not found")
except ForbiddenError:
    print("No access to Actions for this repository")
except GitHubCLIError as e:
    print(f"API error: {e}")
```

## 📝 Usage Examples

### Monitor Workflow Status
```python
async def monitor_workflow_status(repo: str, workflow_name: str):
    actions_api = ActionsAPI(client)
    
    # Get workflow by name
    workflows = await actions_api.list_workflows(repo)
    workflow = next((w for w in workflows if w.name == workflow_name), None)
    
    if not workflow:
        print(f"Workflow '{workflow_name}' not found")
        return
    
    # Get recent runs
    runs = await actions_api.list_workflow_runs(repo, workflow.id)
    recent_runs = runs[:5]  # Last 5 runs
    
    print(f"Recent runs for {workflow_name}:")
    for run in recent_runs:
        status_icon = "✅" if run.conclusion == "success" else "❌" if run.conclusion == "failure" else "⏳"
        print(f"{status_icon} Run #{run.run_number}: {run.status} ({run.conclusion})")
        print(f"   Branch: {run.head_branch}")
        print(f"   Commit: {run.head_sha[:8]}")
        print(f"   Created: {run.created_date}")
```

### Workflow Debugging
```python
async def debug_failed_workflow(repo: str, run_id: int):
    actions_api = ActionsAPI(client)
    
    # Get workflow run details
    run = await actions_api.get_workflow_run(repo, run_id)
    print(f"Debugging workflow run #{run.run_number}")
    print(f"Status: {run.status}, Conclusion: {run.conclusion}")
    
    # Get failed jobs
    jobs = await actions_api.list_workflow_run_jobs(repo, run_id)
    failed_jobs = [j for j in jobs if j.conclusion == "failure"]
    
    print(f"Failed jobs: {len(failed_jobs)}")
    
    for job in failed_jobs:
        print(f"\nJob: {job.name}")
        print(f"Runner: {job.runner_name}")
        
        # Get job logs
        logs = await actions_api.get_workflow_job_logs(repo, job.id)
        
        # Extract error lines (simplified)
        error_lines = [line for line in logs.split('\n') 
                      if 'error' in line.lower() or 'failed' in line.lower()]
        
        if error_lines:
            print("Error lines:")
            for line in error_lines[-5:]:  # Last 5 error lines
                print(f"  {line}")
```

### Workflow Management
```python
async def manage_workflows(repo: str):
    actions_api = ActionsAPI(client)
    
    # List all workflows
    workflows = await actions_api.list_workflows(repo)
    print(f"Repository has {len(workflows)} workflows:")
    
    for workflow in workflows:
        print(f"\n{workflow.name} ({workflow.state})")
        
        # Get recent runs
        runs = await actions_api.list_workflow_runs(repo, workflow.id)
        recent_runs = runs[:3]
        
        if recent_runs:
            print("  Recent runs:")
            for run in recent_runs:
                print(f"    #{run.run_number}: {run.conclusion} ({run.head_branch})")
        
        # Check for stuck runs
        stuck_runs = [r for r in runs if r.status == "in_progress"]
        if stuck_runs:
            print(f"  Warning: {len(stuck_runs)} runs appear stuck")
            
            # Optionally cancel old stuck runs
            for run in stuck_runs:
                age = datetime.now() - run.created_date
                if age.total_seconds() > 3600:  # Older than 1 hour
                    print(f"    Cancelling stuck run #{run.run_number}")
                    await actions_api.cancel_workflow_run(repo, run.id)
```

### Workflow Analytics
```python
async def workflow_analytics(repo: str, days: int = 30):
    actions_api = ActionsAPI(client)
    
    # Get all recent runs
    workflows = await actions_api.list_workflows(repo)
    all_runs = []
    
    for workflow in workflows:
        runs = await actions_api.list_workflow_runs(repo, workflow.id)
        all_runs.extend(runs)
    
    # Filter by date
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_runs = [r for r in all_runs if r.created_date > cutoff_date]
    
    # Calculate statistics
    total_runs = len(recent_runs)
    successful_runs = len([r for r in recent_runs if r.conclusion == "success"])
    failed_runs = len([r for r in recent_runs if r.conclusion == "failure"])
    
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    print(f"Workflow Analytics (last {days} days):")
    print(f"  Total runs: {total_runs}")
    print(f"  Successful: {successful_runs}")
    print(f"  Failed: {failed_runs}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    # Most active workflows
    workflow_counts = {}
    for run in recent_runs:
        workflow_counts[run.workflow_id] = workflow_counts.get(run.workflow_id, 0) + 1
    
    print("\nMost active workflows:")
    for workflow_id, count in sorted(workflow_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        workflow = next((w for w in workflows if w.id == workflow_id), None)
        if workflow:
            print(f"  {workflow.name}: {count} runs")
```

## 🔗 Related Documentation

- [GitHub Actions API](https://docs.github.com/en/rest/actions)
- [Workflow Models](../models/workflow.md)
- [API Client](client.md)
- [Error Handling](../utils/exceptions.md)
