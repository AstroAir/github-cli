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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
        }
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
        "html_url": "https://github.com/testuser",
        "url": "https://api.github.com/users/testuser",
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
        "changed_files": 5
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
