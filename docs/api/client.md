# GitHub API Client

The `GitHubClient` is the core component that handles all HTTP communication with GitHub's REST API. It provides a modern async/await interface with comprehensive error handling, rate limiting, and performance optimizations.

## 🏗️ Class Overview

```python
class GitHubClient:
    """Modern GitHub API client with enhanced error handling and performance."""
    
    API_BASE: str = "https://api.github.com/"
    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
```

## 🔧 Initialization

```python
from github_cli.api.client import GitHubClient
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config

# Initialize with authenticator
config = Config()
authenticator = Authenticator(config)
client = GitHubClient(authenticator)

# Use as async context manager (recommended)
async with GitHubClient(authenticator) as client:
    response = await client.get("/user")
```

## 📡 HTTP Methods

### GET Requests
```python
# Basic GET request
response = await client.get("/user")

# With query parameters
response = await client.get("/user/repos", params={
    "sort": "updated",
    "per_page": 50
})

# With custom headers
response = await client.get("/user", headers={
    "Accept": "application/vnd.github.v3+json"
})
```

### POST Requests
```python
# Create repository
response = await client.post("/user/repos", data={
    "name": "my-repo",
    "description": "My new repository",
    "private": False
})

# With custom headers
response = await client.post("/repos/owner/repo/issues", 
    data={"title": "Bug report", "body": "Description"},
    headers={"Accept": "application/vnd.github.v3+json"}
)
```

### PATCH Requests
```python
# Update repository
response = await client.patch("/repos/owner/repo", data={
    "description": "Updated description",
    "has_issues": True
})
```

### DELETE Requests
```python
# Delete repository
response = await client.delete("/repos/owner/repo")
```

### Generic Request Method
```python
# Any HTTP method
response = await client.request(
    method="PUT",
    endpoint="/repos/owner/repo/subscription",
    data={"subscribed": True}
)
```

## 📊 Response Structure

All methods return an `APIResponse` object:

```python
@dataclass
class APIResponse:
    data: Any                    # Parsed JSON response
    status_code: int            # HTTP status code
    rate_limit: RateLimitInfo   # Rate limit information
    headers: Dict[str, str]     # Response headers

# Usage
response = await client.get("/user")
user_data = response.data
remaining_requests = response.rate_limit.remaining
```

## 🚦 Rate Limiting

The client automatically handles GitHub's rate limits:

### Rate Limit Information
```python
@dataclass
class RateLimitInfo:
    limit: int          # Total requests allowed
    remaining: int      # Requests remaining
    reset_time: int     # Unix timestamp when limit resets
    used: int          # Requests used
```

### Automatic Rate Limit Handling
- **Proactive Throttling**: Slows down requests when approaching limits
- **Automatic Backoff**: Waits for reset when limits are exceeded
- **Smart Retry Logic**: Exponential backoff for rate limit errors

### Rate Limit Configuration
```python
# Configure rate limit behavior
client.rate_limit_buffer = 100  # Reserve 100 requests
client.rate_limit_threshold = 0.1  # Throttle at 10% remaining
```

## 🔄 Retry Logic

The client implements intelligent retry logic for transient failures:

### Retry Configuration
```python
client.max_retries = 3          # Maximum retry attempts
client.retry_delay = 1.0        # Base delay between retries
client.retry_backoff = 2.0      # Exponential backoff multiplier
```

### Retryable Conditions
- Network timeouts
- Rate limit errors (with appropriate delays)
- Server errors (5xx status codes)
- Connection errors

### Non-Retryable Conditions
- Authentication errors (401)
- Authorization errors (403, except rate limits)
- Not found errors (404)
- Client errors (4xx, except rate limits)

## 🔐 Authentication

The client handles authentication through the `Authenticator`:

### Token Management
```python
# Check authentication status
if client.authenticator.is_authenticated():
    response = await client.get("/user")
else:
    await client.authenticator.authenticate()
```

### Token Expiration Handling
- Automatic token refresh when expired
- Graceful handling of token expiration during requests
- User notification for authentication issues

## 🚨 Error Handling

The client provides comprehensive error handling:

### Exception Hierarchy
```python
GitHubCLIError                 # Base exception
├── AuthenticationError        # 401 errors
├── NetworkError              # Connection issues
├── RateLimitError           # Rate limit exceeded
└── APIError                 # GitHub API errors
    ├── NotFoundError        # 404 errors
    ├── ForbiddenError       # 403 errors
    └── ServerError          # 5xx errors
```

### Error Context
```python
try:
    response = await client.get("/repos/owner/nonexistent")
except NotFoundError as e:
    print(f"Repository not found: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response}")
```

## 📝 Logging

The client provides detailed logging for debugging:

### Log Configuration
```python
# Logs are written to logs/github_cli.log
# Configure log level
import logging
logging.getLogger("github_cli.api.client").setLevel(logging.DEBUG)
```

### Log Information
- Request details (method, URL, headers)
- Response information (status, headers, timing)
- Rate limit status
- Retry attempts
- Error details

## ⚡ Performance Features

### Connection Pooling
- Reuses HTTP connections for efficiency
- Configurable connection pool size
- Automatic connection cleanup

### Request Timeouts
```python
# Configure timeouts
client.timeout = 30             # Total request timeout
client.connect_timeout = 10     # Connection timeout
```

### Compression
- Automatic gzip compression for responses
- Reduces bandwidth usage
- Improves response times

## 🔧 Advanced Configuration

### Custom Headers
```python
# Set default headers for all requests
client.default_headers = {
    "User-Agent": "MyApp/1.0",
    "Accept": "application/vnd.github.v3+json"
}
```

### Base URL Override
```python
# Use GitHub Enterprise
client.api_base = "https://github.company.com/api/v3/"
```

### Session Configuration
```python
# Configure aiohttp session
import aiohttp

connector = aiohttp.TCPConnector(
    limit=100,              # Connection pool size
    limit_per_host=30,      # Connections per host
    ttl_dns_cache=300,      # DNS cache TTL
    use_dns_cache=True      # Enable DNS caching
)

client.session_kwargs = {
    "connector": connector,
    "timeout": aiohttp.ClientTimeout(total=30)
}
```

## 📊 Monitoring and Metrics

### Request Metrics
```python
# Access request statistics
stats = client.get_stats()
print(f"Total requests: {stats.total_requests}")
print(f"Failed requests: {stats.failed_requests}")
print(f"Average response time: {stats.avg_response_time}")
```

### Rate Limit Monitoring
```python
# Monitor rate limit status
rate_limit = client.rate_limit_info
print(f"Remaining: {rate_limit.remaining}/{rate_limit.limit}")
print(f"Reset time: {rate_limit.reset_time}")
```

## 🧪 Testing

### Mock Client for Testing
```python
from github_cli.api.client import MockGitHubClient

# Use mock client in tests
mock_client = MockGitHubClient()
mock_client.add_response("/user", {"login": "testuser"})

response = await mock_client.get("/user")
assert response.data["login"] == "testuser"
```

### Integration Testing
```python
# Test with real API (requires authentication)
import pytest

@pytest.mark.integration
async def test_user_endpoint():
    async with GitHubClient(authenticator) as client:
        response = await client.get("/user")
        assert response.status_code == 200
        assert "login" in response.data
```

## 📖 Examples

### Basic Usage
```python
async def get_user_info():
    async with GitHubClient(authenticator) as client:
        response = await client.get("/user")
        return response.data

user = await get_user_info()
print(f"Hello, {user['login']}!")
```

### Error Handling
```python
async def safe_api_call():
    try:
        async with GitHubClient(authenticator) as client:
            response = await client.get("/user/repos")
            return response.data
    except RateLimitError:
        print("Rate limit exceeded, please try again later")
    except AuthenticationError:
        print("Authentication failed, please login again")
    except NetworkError:
        print("Network error, please check your connection")
    except GitHubCLIError as e:
        print(f"API error: {e}")
```

### Pagination
```python
async def get_all_repos():
    repos = []
    page = 1
    
    async with GitHubClient(authenticator) as client:
        while True:
            response = await client.get("/user/repos", params={
                "page": page,
                "per_page": 100
            })
            
            if not response.data:
                break
                
            repos.extend(response.data)
            page += 1
    
    return repos
```
