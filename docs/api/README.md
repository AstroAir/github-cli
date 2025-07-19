# API Documentation

The GitHub CLI API module provides a comprehensive interface to the GitHub REST API with modern async/await patterns, robust error handling, and intelligent rate limiting.

## 🏗️ Architecture Overview

The API system is built with a modular architecture:

```
github_cli/api/
├── client.py           # Core API client with rate limiting
├── repositories.py     # Repository management
├── pull_requests.py    # Pull request operations
├── actions.py          # GitHub Actions workflows
├── issues.py           # Issue management
├── gists.py           # Gist operations
├── search.py          # Search functionality
├── users.py           # User and organization management
├── notifications.py   # Notification handling
├── releases.py        # Release management
├── projects.py        # Project boards
├── organizations.py   # Organization management
└── statistics.py      # Repository statistics
```

## 🔧 Core Components

### GitHubClient

The central API client that handles all HTTP communication with GitHub's REST API.

**Key Features:**
- Automatic token management and refresh
- Rate limiting with intelligent backoff
- Request retries with exponential backoff
- Comprehensive error handling
- Response caching for performance
- Request/response logging

**Usage:**
```python
from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator

authenticator = Authenticator(config)
async with GitHubClient(authenticator) as client:
    response = await client.get("/user")
```

### API Response Structure

All API methods return an `APIResponse` object with:

```python
@dataclass
class APIResponse:
    data: Any                    # Response data (JSON parsed)
    status_code: int            # HTTP status code
    rate_limit: RateLimitInfo   # Rate limit information
    headers: Dict[str, str]     # Response headers
```

### Rate Limiting

The client automatically handles GitHub's rate limits:

- **Primary Rate Limit**: 5,000 requests/hour for authenticated users
- **Secondary Rate Limits**: Abuse detection and concurrent request limits
- **Automatic Backoff**: Exponential backoff when limits are approached
- **Rate Limit Headers**: Tracks remaining requests and reset times

## 📚 API Modules

### [Client](client.md)
Core HTTP client with authentication, rate limiting, and error handling.

### [Repositories](repositories.md)
Complete repository management including creation, updates, statistics, and metadata.

### [Pull Requests](pull-requests.md)
Full pull request lifecycle from creation to merge, including reviews and diffs.

### [Actions](actions.md)
GitHub Actions workflow management, run monitoring, and log access.

### [Issues](issues.md)
Issue creation, management, comments, and labels.

### [Search](search.md)
Comprehensive search across repositories, code, users, issues, and commits.

### [Gists](gists.md)
Gist creation, management, and sharing.

### [Users](users.md)
User profiles, organizations, and team management.

### [Notifications](notifications.md)
GitHub notification management and filtering.

### [Releases](releases.md)
Release creation, asset management, and publishing.

## 🔐 Authentication

All API modules require authentication through the `Authenticator` class:

```python
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config

config = Config()
authenticator = Authenticator(config)

# Authenticate if needed
if not authenticator.is_authenticated():
    await authenticator.authenticate()
```

## 🚨 Error Handling

The API uses a comprehensive error hierarchy:

```python
GitHubCLIError                 # Base exception
├── AuthenticationError        # Authentication failures
├── NetworkError              # Network connectivity issues
├── RateLimitError           # Rate limit exceeded
├── ValidationError          # Input validation errors
└── APIError                 # GitHub API errors
    ├── NotFoundError        # 404 errors
    ├── ForbiddenError       # 403 errors
    └── ServerError          # 5xx errors
```

## 📊 Performance Features

### Caching
- Response caching for frequently accessed data
- Configurable cache TTL per endpoint
- Memory-efficient LRU cache implementation

### Pagination
- Automatic pagination handling
- Configurable page sizes
- Lazy loading for large datasets

### Concurrent Requests
- Async/await for non-blocking operations
- Connection pooling for efficiency
- Request batching for bulk operations

## 🔧 Configuration

API behavior can be configured through environment variables or config files:

```python
# Rate limiting
GITHUB_CLI_RATE_LIMIT_BUFFER = 100  # Reserve requests
GITHUB_CLI_MAX_RETRIES = 3          # Retry attempts
GITHUB_CLI_RETRY_DELAY = 1.0        # Base retry delay

# Timeouts
GITHUB_CLI_REQUEST_TIMEOUT = 30     # Request timeout (seconds)
GITHUB_CLI_CONNECT_TIMEOUT = 10     # Connection timeout

# Caching
GITHUB_CLI_CACHE_TTL = 300          # Cache TTL (seconds)
GITHUB_CLI_CACHE_SIZE = 1000        # Max cache entries
```

## 📝 Usage Examples

### Basic Repository Operations
```python
from github_cli.api.repositories import RepositoryAPI

repo_api = RepositoryAPI(client)

# List user repositories
repos = await repo_api.list_user_repos()

# Get repository details
repo = await repo_api.get_repo("owner/repo")

# Create repository
new_repo = await repo_api.create_repo(
    name="my-repo",
    description="My new repository",
    private=False
)
```

### Pull Request Workflow
```python
from github_cli.api.pull_requests import PullRequestAPI

pr_api = PullRequestAPI(client)

# Create pull request
pr = await pr_api.create_pull_request(
    repo="owner/repo",
    title="Add new feature",
    head="feature-branch",
    base="main",
    body="Description of changes"
)

# Review pull request
await pr_api.create_review(
    repo="owner/repo",
    pr_number=pr.number,
    event="APPROVE",
    body="Looks good!"
)

# Merge pull request
await pr_api.merge_pull_request(
    repo="owner/repo",
    pr_number=pr.number,
    merge_method="squash"
)
```

### GitHub Actions Management
```python
from github_cli.api.actions import ActionsAPI

actions_api = ActionsAPI(client)

# List workflows
workflows = await actions_api.list_workflows("owner/repo")

# Get workflow runs
runs = await actions_api.list_workflow_runs(
    repo="owner/repo",
    workflow_id=workflows[0].id
)

# Re-run failed workflow
await actions_api.rerun_workflow("owner/repo", runs[0].id)
```

## 🧪 Testing

The API modules include comprehensive test coverage:

```bash
# Run API tests
pytest tests/api/

# Run with coverage
pytest tests/api/ --cov=github_cli.api

# Run specific module tests
pytest tests/api/test_repositories.py
```

## 📖 Further Reading

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Rate Limiting Best Practices](https://docs.github.com/en/rest/guides/best-practices-for-integrators)
- [Authentication Guide](../auth/README.md)
- [Error Handling Guide](../utils/exceptions.md)
