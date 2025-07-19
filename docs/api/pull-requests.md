# Pull Requests API

The `PullRequestAPI` provides comprehensive pull request management functionality including creation, reviews, merging, and diff viewing.

## 🏗️ Class Overview

```python
class PullRequestAPI:
    """API for working with GitHub pull requests"""
    
    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui
        self.diff_viewer = DiffViewer(ui.console if ui else None)
```

## 📚 Core Methods

### Pull Request Listing

#### List Pull Requests
```python
async def list_pull_requests(
    self,
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc"
) -> List[PullRequest]
```

**Parameters:**
- `repo`: Repository in format "owner/repo"
- `state`: PR state (`open`, `closed`, `all`)
- `sort`: Sort order (`created`, `updated`, `popularity`)
- `direction`: Sort direction (`asc`, `desc`)

**Example:**
```python
pr_api = PullRequestAPI(client)

# List open pull requests
open_prs = await pr_api.list_pull_requests("owner/repo")

# List all pull requests sorted by update time
all_prs = await pr_api.list_pull_requests(
    "owner/repo",
    state="all",
    sort="updated"
)

# List closed pull requests
closed_prs = await pr_api.list_pull_requests("owner/repo", state="closed")
```

### Pull Request Details

#### Get Pull Request
```python
async def get_pull_request(self, repo: str, pr_number: int) -> PullRequest
```

**Example:**
```python
# Get specific pull request
pr = await pr_api.get_pull_request("owner/repo", 123)
print(f"PR #{pr.number}: {pr.title}")
print(f"State: {pr.state}")
print(f"Author: {pr.user.login}")
```

### Pull Request Creation

#### Create Pull Request
```python
async def create_pull_request(
    self,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: Optional[str] = None,
    draft: bool = False
) -> PullRequest
```

**Parameters:**
- `repo`: Repository in format "owner/repo"
- `title`: Pull request title
- `head`: Source branch
- `base`: Target branch
- `body`: Pull request description
- `draft`: Create as draft PR

**Example:**
```python
# Create pull request
pr = await pr_api.create_pull_request(
    repo="owner/repo",
    title="Add new feature",
    head="feature-branch",
    base="main",
    body="This PR adds a new feature that...",
    draft=False
)

print(f"Created PR #{pr.number}: {pr.html_url}")
```

### Pull Request Updates

#### Update Pull Request
```python
async def update_pull_request(
    self,
    repo: str,
    pr_number: int,
    **kwargs
) -> PullRequest
```

**Updatable Fields:**
- `title`: PR title
- `body`: PR description
- `state`: PR state (`open`, `closed`)
- `base`: Target branch

**Example:**
```python
# Update pull request
updated_pr = await pr_api.update_pull_request(
    "owner/repo",
    123,
    title="Updated: Add new feature",
    body="Updated description with more details"
)
```

### Pull Request Files

#### Get Pull Request Files
```python
async def get_pull_request_files(
    self,
    repo: str,
    pr_number: int
) -> List[Dict[str, Any]]
```

**Example:**
```python
# Get changed files
files = await pr_api.get_pull_request_files("owner/repo", 123)

for file in files:
    print(f"File: {file['filename']}")
    print(f"Status: {file['status']}")
    print(f"Changes: +{file['additions']} -{file['deletions']}")
```

#### Get Pull Request Diff
```python
async def get_pull_request_diff(
    self,
    repo: str,
    pr_number: int,
    format: str = "diff"
) -> str
```

**Parameters:**
- `format`: Diff format (`diff`, `patch`)

**Example:**
```python
# Get diff
diff = await pr_api.get_pull_request_diff("owner/repo", 123)
print(diff)

# Display formatted diff (if UI is available)
if pr_api.ui:
    pr_api.diff_viewer.display_diff(diff)
```

### Pull Request Commits

#### Get Pull Request Commits
```python
async def get_pull_request_commits(
    self,
    repo: str,
    pr_number: int
) -> List[Dict[str, Any]]
```

**Example:**
```python
# Get commits
commits = await pr_api.get_pull_request_commits("owner/repo", 123)

for commit in commits:
    print(f"Commit: {commit['sha'][:8]}")
    print(f"Message: {commit['commit']['message']}")
    print(f"Author: {commit['commit']['author']['name']}")
```

### Pull Request Reviews

#### List Pull Request Reviews
```python
async def get_pull_request_reviews(
    self,
    repo: str,
    pr_number: int
) -> List[Dict[str, Any]]
```

#### Create Review
```python
async def create_review(
    self,
    repo: str,
    pr_number: int,
    event: str,
    body: Optional[str] = None,
    comments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `event`: Review event (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`)
- `body`: Review summary
- `comments`: Line-specific comments

**Example:**
```python
# Approve pull request
review = await pr_api.create_review(
    "owner/repo",
    123,
    event="APPROVE",
    body="Looks good to me!"
)

# Request changes with comments
review = await pr_api.create_review(
    "owner/repo",
    123,
    event="REQUEST_CHANGES",
    body="Please address the following issues:",
    comments=[
        {
            "path": "src/main.py",
            "line": 42,
            "body": "This function needs error handling"
        }
    ]
)
```

#### Submit Review
```python
async def submit_review(
    self,
    repo: str,
    pr_number: int,
    review_id: int,
    event: str,
    body: Optional[str] = None
) -> Dict[str, Any]
```

### Pull Request Merging

#### Check Merge Status
```python
async def get_merge_status(self, repo: str, pr_number: int) -> Dict[str, Any]
```

#### Merge Pull Request
```python
async def merge_pull_request(
    self,
    repo: str,
    pr_number: int,
    commit_title: Optional[str] = None,
    commit_message: Optional[str] = None,
    merge_method: str = "merge"
) -> Dict[str, Any]
```

**Parameters:**
- `merge_method`: Merge method (`merge`, `squash`, `rebase`)
- `commit_title`: Custom merge commit title
- `commit_message`: Custom merge commit message

**Example:**
```python
# Check if PR can be merged
merge_status = await pr_api.get_merge_status("owner/repo", 123)
if merge_status["mergeable"]:
    # Merge with squash
    result = await pr_api.merge_pull_request(
        "owner/repo",
        123,
        merge_method="squash",
        commit_title="Add new feature (#123)"
    )
    print(f"Merged: {result['sha']}")
else:
    print("PR cannot be merged - conflicts exist")
```

## 🎯 CLI Command Handler

```python
async def handle_pr_command(
    args: Dict[str, Any], 
    client: GitHubClient, 
    ui: TerminalUI
) -> None
```

### Supported Commands

#### List Pull Requests
```bash
github-cli pr list --repo OWNER/REPO [--state STATE]
```

#### View Pull Request
```bash
github-cli pr view --repo OWNER/REPO --number NUMBER
```

#### Create Pull Request
```bash
github-cli pr create --repo OWNER/REPO --title TITLE --head HEAD --base BASE [--body BODY] [--draft]
```

#### Review Pull Request
```bash
github-cli pr review --repo OWNER/REPO --number NUMBER --event EVENT [--body BODY]
```

#### Merge Pull Request
```bash
github-cli pr merge --repo OWNER/REPO --number NUMBER [--method METHOD]
```

## 📊 Pull Request Model

```python
@dataclass
class PullRequest:
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    draft: bool
    html_url: str
    diff_url: str
    patch_url: str
    head: Dict[str, Any]
    base: Dict[str, Any]
    user: Dict[str, Any]
    assignees: List[Dict[str, Any]]
    reviewers: List[Dict[str, Any]]
    labels: List[Dict[str, Any]]
    milestone: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    merged_at: Optional[datetime]
    merge_commit_sha: Optional[str]
    mergeable: Optional[bool]
    mergeable_state: str
    merged: bool
    comments: int
    review_comments: int
    commits: int
    additions: int
    deletions: int
    changed_files: int
```

## 🔍 Diff Viewer Integration

The API includes a sophisticated diff viewer for displaying changes:

```python
# Display diff with syntax highlighting
diff = await pr_api.get_pull_request_diff("owner/repo", 123)
pr_api.diff_viewer.display_diff(diff)

# Display side-by-side diff
pr_api.diff_viewer.display_side_by_side_diff(diff)

# Display file-by-file changes
files = await pr_api.get_pull_request_files("owner/repo", 123)
for file in files:
    pr_api.diff_viewer.display_file_diff(file)
```

## 🚨 Error Handling

```python
try:
    pr = await pr_api.create_pull_request(
        "owner/repo", "New feature", "feature", "main"
    )
except ValidationError as e:
    print(f"Invalid input: {e}")
except ForbiddenError:
    print("No permission to create pull request")
except GitHubCLIError as e:
    print(f"API error: {e}")
```

## 📝 Usage Examples

### Complete PR Workflow
```python
async def pr_workflow():
    pr_api = PullRequestAPI(client)
    
    # Create pull request
    pr = await pr_api.create_pull_request(
        repo="owner/repo",
        title="Add new feature",
        head="feature-branch",
        base="main",
        body="This PR adds a new feature..."
    )
    
    # Get and display diff
    diff = await pr_api.get_pull_request_diff("owner/repo", pr.number)
    print("Changes:")
    print(diff)
    
    # Review the PR
    await pr_api.create_review(
        "owner/repo",
        pr.number,
        event="APPROVE",
        body="LGTM!"
    )
    
    # Merge the PR
    merge_result = await pr_api.merge_pull_request(
        "owner/repo",
        pr.number,
        merge_method="squash"
    )
    
    print(f"PR merged: {merge_result['sha']}")
```

### PR Review Process
```python
async def review_pr(repo: str, pr_number: int):
    pr_api = PullRequestAPI(client)
    
    # Get PR details
    pr = await pr_api.get_pull_request(repo, pr_number)
    print(f"Reviewing PR #{pr.number}: {pr.title}")
    
    # Get changed files
    files = await pr_api.get_pull_request_files(repo, pr_number)
    print(f"Files changed: {len(files)}")
    
    # Get commits
    commits = await pr_api.get_pull_request_commits(repo, pr_number)
    print(f"Commits: {len(commits)}")
    
    # Check existing reviews
    reviews = await pr_api.get_pull_request_reviews(repo, pr_number)
    approved = any(r["state"] == "APPROVED" for r in reviews)
    
    if not approved:
        # Add review
        await pr_api.create_review(
            repo,
            pr_number,
            event="APPROVE",
            body="Code looks good!"
        )
        print("Review submitted")
```

## 🔗 Related Documentation

- [GitHub Pull Requests API](https://docs.github.com/en/rest/pulls/pulls)
- [Pull Request Model](../models/pull_request.md)
- [Diff Viewer](../ui/diff_viewer.md)
- [API Client](client.md)
