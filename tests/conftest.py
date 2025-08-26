"""
Pytest configuration and fixtures for GitHub CLI tests.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import json
from datetime import datetime, timezone

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config
from github_cli.git.commands import GitCommands
from github_cli.models.repository import Repository
from github_cli.models.user import User
from github_cli.models.pull_request import PullRequest
from github_cli.models.issue import Issue


# Remove the custom event_loop fixture to use pytest-asyncio's default


@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = Mock(spec=Config)
    config.get.return_value = "test_value"
    return config


@pytest.fixture
def mock_authenticator(mock_config):
    """Mock authenticator object."""
    authenticator = Mock(spec=Authenticator)
    authenticator.config = mock_config
    authenticator.get_token = AsyncMock(return_value="test_token")
    authenticator.is_authenticated = AsyncMock(return_value=True)
    return authenticator


@pytest.fixture
def mock_github_client(mock_authenticator):
    """Mock GitHub API client."""
    client = Mock(spec=GitHubClient)
    client.authenticator = mock_authenticator
    
    # Mock async context manager
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    
    # Mock API methods
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    
    return client


@pytest.fixture
def mock_terminal_ui(mock_github_client):
    """Mock terminal UI object."""
    terminal = Mock(spec=TerminalUI)
    terminal.client = mock_github_client
    
    # Mock display methods
    terminal.display_success = Mock()
    terminal.display_error = Mock()
    terminal.display_info = Mock()
    terminal.display_warning = Mock()
    
    # Mock git display methods (these are added dynamically)
    terminal.display_git_branches = Mock()
    terminal.display_git_status = Mock()
    terminal.display_git_stashes = Mock()
    
    return terminal


@pytest.fixture
def git_commands(mock_github_client, mock_terminal_ui):
    """GitCommands instance with mocked dependencies."""
    return GitCommands(mock_github_client, mock_terminal_ui)


@pytest.fixture
def sample_git_status_output():
    """Sample git status --porcelain output."""
    return """M  modified_file.py
A  added_file.py
D  deleted_file.py
?? untracked_file.py
 M staged_modified.py"""


@pytest.fixture
def sample_git_branch_output():
    """Sample git branch output."""
    return """  feature/new-feature
* main
  develop
  hotfix/urgent-fix"""


@pytest.fixture
def sample_git_remote_branch_output():
    """Sample git branch -r output."""
    return """  origin/main
  origin/develop
  origin/feature/new-feature
  origin/hotfix/urgent-fix"""


@pytest.fixture
def sample_git_log_output():
    """Sample git log output."""
    return """abc123|John Doe|john@example.com|2023-12-01|Initial commit
def456|Jane Smith|jane@example.com|2023-12-02|Add new feature
ghi789|Bob Johnson|bob@example.com|2023-12-03|Fix bug in parser"""


@pytest.fixture
def sample_git_stash_output():
    """Sample git stash list output."""
    return """stash@{0}|WIP on main: abc123 Initial commit|2023-12-01 10:00:00
stash@{1}|On feature: def456 Add new feature|2023-12-02 15:30:00"""


@pytest.fixture
def sample_remote_urls():
    """Sample git remote URLs."""
    return {
        "ssh": "git@github.com:owner/repo.git",
        "https": "https://github.com/owner/repo.git",
        "https_no_git": "https://github.com/owner/repo",
        "non_github": "https://gitlab.com/owner/repo.git"
    }


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for git commands."""
    def _mock_run(returncode=0, stdout="", stderr=""):
        mock = Mock()
        mock.returncode = returncode
        mock.stdout = stdout
        mock.stderr = stderr
        return mock
    return _mock_run


# Additional fixtures for comprehensive testing

@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing."""
    return {
        "id": 123456789,
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "description": "A test repository",
        "private": False,
        "fork": False,
        "html_url": "https://github.com/testuser/test-repo",
        "clone_url": "https://github.com/testuser/test-repo.git",
        "ssh_url": "git@github.com:testuser/test-repo.git",
        "homepage": "https://example.com",
        "stargazers_count": 42,
        "watchers_count": 42,
        "forks_count": 5,
        "open_issues_count": 3,
        "size": 1024,
        "language": "Python",
        "topics": ["python", "cli", "github"],
        "license": {"key": "mit", "name": "MIT License"},
        "default_branch": "main",
        "visibility": "public",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "pushed_at": "2023-12-01T12:00:00Z",
        "archived": False,
        "disabled": False,
        "owner": {
            "id": 987654321,
            "login": "testuser",
            "type": "User",
            "site_admin": False
        },
        # Additional field required by Repository model
        "url": "https://api.github.com/repos/testuser/test-repo"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 987654321,
        "login": "testuser",
        "node_id": "MDQ6VXNlcjk4NzY1NDMyMQ==",
        "type": "User",
        "site_admin": False,
        "name": "Test User",
        "email": "test@example.com",
        "bio": "A test user for GitHub CLI",
        "company": "Test Company",
        "location": "Test City",
        "blog": "https://testuser.dev",
        "twitter_username": "testuser",
        "avatar_url": "https://avatars.githubusercontent.com/u/987654321",
        "gravatar_id": "",
        "html_url": "https://github.com/testuser",
        "url": "https://api.github.com/users/testuser",
        "followers_url": "https://api.github.com/users/testuser/followers",
        "following_url": "https://api.github.com/users/testuser/following{/other_user}",
        "gists_url": "https://api.github.com/users/testuser/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/testuser/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/testuser/subscriptions",
        "organizations_url": "https://api.github.com/users/testuser/orgs",
        "repos_url": "https://api.github.com/users/testuser/repos",
        "events_url": "https://api.github.com/users/testuser/events{/privacy}",
        "received_events_url": "https://api.github.com/users/testuser/received_events",
        "public_repos": 10,
        "public_gists": 5,
        "followers": 100,
        "following": 50,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z"
    }


@pytest.fixture
def sample_pull_request_data():
    """Sample pull request data for testing."""
    return {
        "id": 555666777,
        "number": 42,
        "title": "Add new feature",
        "body": "This PR adds a new feature to the application.",
        "state": "open",
        "draft": False,
        "locked": False,
        "html_url": "https://github.com/testuser/test-repo/pull/42",
        "diff_url": "https://github.com/testuser/test-repo/pull/42.diff",
        "patch_url": "https://github.com/testuser/test-repo/pull/42.patch",
        "created_at": "2023-11-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "closed_at": None,
        "merged_at": None,
        "merge_commit_sha": None,
        "assignees": [],
        "requested_reviewers": [],
        "labels": [{"name": "enhancement", "color": "a2eeef"}],
        "milestone": None,
        "head": {
            "ref": "feature-branch",
            "sha": "abc123def456",
            "repo": {"name": "test-repo", "full_name": "testuser/test-repo"}
        },
        "base": {
            "ref": "main",
            "sha": "def456abc123",
            "repo": {"name": "test-repo", "full_name": "testuser/test-repo"}
        },
        "user": {
            "id": 987654321,
            "login": "testuser",
            "type": "User"
        },
        "mergeable": True,
        "mergeable_state": "clean",
        "merged": False,
        "comments": 2,
        "review_comments": 1,
        "commits": 3,
        "additions": 50,
        "deletions": 10,
        "changed_files": 5,
        # Additional fields required by Issue model
        "author_association": "OWNER",
        "url": "https://api.github.com/repos/testuser/test-repo/pulls/42",
        "repository_url": "https://api.github.com/repos/testuser/test-repo"
    }


@pytest.fixture
def sample_issue_data():
    """Sample issue data for testing."""
    return {
        "id": 444555666,
        "number": 42,
        "title": "Test Issue",
        "body": "This is a test issue for the GitHub CLI.",
        "state": "open",
        "locked": False,
        "html_url": "https://github.com/testuser/test-repo/issues/42",
        "created_at": "2023-11-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "closed_at": None,
        "assignees": [
            {
                "id": 987654321,
                "login": "testuser",
                "type": "User"
            }
        ],
        "labels": [
            {"name": "bug", "color": "d73a4a"},
            {"name": "enhancement", "color": "a2eeef"}
        ],
        "milestone": {
            "id": 123456,
            "number": 1,
            "title": "v1.0.0",
            "state": "open"
        },
        "user": {
            "id": 987654321,
            "login": "testuser",
            "type": "User"
        },
        "comments": 3,
        "author_association": "OWNER",
        "url": "https://api.github.com/repos/testuser/test-repo/issues/42",
        "repository_url": "https://api.github.com/repos/testuser/test-repo"
    }


@pytest.fixture
def sample_gist_data():
    """Sample gist data for testing."""
    return {
        "id": "abc123def456789",
        "description": "Test gist for GitHub CLI",
        "public": True,
        "html_url": "https://gist.github.com/abc123def456789",
        "git_pull_url": "https://gist.github.com/abc123def456789.git",
        "git_push_url": "https://gist.github.com/abc123def456789.git",
        "created_at": "2023-11-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "comments": 2,
        "comments_url": "https://api.github.com/gists/abc123def456789/comments",
        "owner": {
            "id": 987654321,
            "login": "testuser",
            "type": "User",
            "avatar_url": "https://github.com/images/error/testuser_happy.gif",
            "html_url": "https://github.com/testuser"
        },
        "files": {
            "test.py": {
                "filename": "test.py",
                "type": "application/x-python",
                "language": "Python",
                "raw_url": "https://gist.githubusercontent.com/testuser/abc123def456789/raw/test.py",
                "size": 25,
                "content": "print('Hello, World!')"
            },
            "README.md": {
                "filename": "README.md",
                "type": "text/markdown",
                "language": "Markdown",
                "raw_url": "https://gist.githubusercontent.com/testuser/abc123def456789/raw/README.md",
                "size": 45,
                "content": "# Test Gist\n\nThis is a test gist for the GitHub CLI."
            }
        },
        "truncated": False
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "id": 123456,
        "node_id": "W_kwDOABCDEF4ABCDEF",
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "state": "active",
        "created_at": "2023-11-01T00:00:00Z",
        "updated_at": "2023-12-01T00:00:00Z",
        "url": "https://api.github.com/repos/testuser/test-repo/actions/workflows/123456",
        "html_url": "https://github.com/testuser/test-repo/actions/workflows/ci.yml",
        "badge_url": "https://github.com/testuser/test-repo/workflows/CI/badge.svg"
    }


@pytest.fixture
def sample_workflow_run_data():
    """Sample workflow run data for testing."""
    return {
        "id": 789012,
        "name": "CI",
        "node_id": "WFR_kwDOABCDEF4ABCDEF",
        "head_branch": "main",
        "head_sha": "abc123def456",
        "path": ".github/workflows/ci.yml",
        "display_title": "Update README",
        "run_number": 42,
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "workflow_id": 123456,
        "check_suite_id": 456789,
        "check_suite_node_id": "CS_kwDOABCDEF4ABCDEF",
        "url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012",
        "html_url": "https://github.com/testuser/test-repo/actions/runs/789012",
        "created_at": "2023-12-01T00:00:00Z",
        "updated_at": "2023-12-01T00:05:00Z",
        "run_started_at": "2023-12-01T00:00:30Z",
        "jobs_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012/jobs",
        "logs_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012/logs",
        "check_suite_url": "https://api.github.com/repos/testuser/test-repo/check-suites/456789",
        "artifacts_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012/artifacts",
        "cancel_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012/cancel",
        "rerun_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012/rerun",
        "previous_attempt_url": None,
        "workflow_url": "https://api.github.com/repos/testuser/test-repo/actions/workflows/123456",
        "head_commit": {
            "id": "abc123def456",
            "tree_id": "def456abc123",
            "message": "Update README",
            "timestamp": "2023-12-01T00:00:00Z",
            "author": {
                "name": "Test User",
                "email": "test@example.com"
            },
            "committer": {
                "name": "Test User",
                "email": "test@example.com"
            }
        },
        "repository": {
            "id": 111222333,
            "node_id": "R_kwDOABCDEF",
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "private": False,
            "owner": {
                "login": "testuser",
                "id": 987654321,
                "type": "User"
            }
        },
        "head_repository": {
            "id": 111222333,
            "node_id": "R_kwDOABCDEF",
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "private": False,
            "owner": {
                "login": "testuser",
                "id": 987654321,
                "type": "User"
            }
        }
    }


@pytest.fixture
def sample_workflow_job_data():
    """Sample workflow job data for testing."""
    return {
        "id": 345678,
        "run_id": 789012,
        "workflow_name": "CI",
        "head_branch": "main",
        "run_url": "https://api.github.com/repos/testuser/test-repo/actions/runs/789012",
        "run_attempt": 1,
        "node_id": "J_kwDOABCDEF4ABCDEF",
        "head_sha": "abc123def456",
        "url": "https://api.github.com/repos/testuser/test-repo/actions/jobs/345678",
        "html_url": "https://github.com/testuser/test-repo/actions/runs/789012/job/345678",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2023-12-01T00:00:30Z",
        "started_at": "2023-12-01T00:01:00Z",
        "completed_at": "2023-12-01T00:04:30Z",
        "name": "test",
        "steps": [
            {
                "name": "Set up job",
                "status": "completed",
                "conclusion": "success",
                "number": 1,
                "started_at": "2023-12-01T00:01:00Z",
                "completed_at": "2023-12-01T00:01:30Z"
            },
            {
                "name": "Run tests",
                "status": "completed",
                "conclusion": "success",
                "number": 2,
                "started_at": "2023-12-01T00:01:30Z",
                "completed_at": "2023-12-01T00:04:00Z"
            },
            {
                "name": "Complete job",
                "status": "completed",
                "conclusion": "success",
                "number": 3,
                "started_at": "2023-12-01T00:04:00Z",
                "completed_at": "2023-12-01T00:04:30Z"
            }
        ],
        "check_run_url": "https://api.github.com/repos/testuser/test-repo/check-runs/345678",
        "labels": ["ubuntu-latest"],
        "runner_id": 1,
        "runner_name": "GitHub Actions 1",
        "runner_group_id": 1,
        "runner_group_name": "GitHub Actions"
    }


@pytest.fixture
def mock_http_response():
    """Mock HTTP response for API testing."""
    def _create_response(status_code=200, json_data=None, headers=None):
        response = Mock()
        response.status_code = status_code
        response.headers = headers or {"content-type": "application/json"}
        response.json = Mock(return_value=json_data or {})
        response.text = json.dumps(json_data or {})
        response.raise_for_status = Mock()
        if status_code >= 400:
            response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        return response
    return _create_response


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for async HTTP testing."""
    session = Mock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.get = AsyncMock()
    session.post = AsyncMock()
    session.put = AsyncMock()
    session.delete = AsyncMock()
    session.patch = AsyncMock()
    session.request = AsyncMock()
    return session


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, external deps)"
    )
    config.addinivalue_line(
        "markers", "git: marks tests that require git to be installed"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that test API client functionality"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests that test authentication functionality"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests that test UI components"
    )
    config.addinivalue_line(
        "markers", "tui: marks tests that test TUI components"
    )
    config.addinivalue_line(
        "markers", "models: marks tests that test data models"
    )
    config.addinivalue_line(
        "markers", "utils: marks tests for utility modules"
    )
