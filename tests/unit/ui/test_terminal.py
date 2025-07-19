"""
Unit tests for Terminal UI component.

Tests the TerminalUI class including display methods, formatting,
and Rich console integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console
from rich.table import Table

from github_cli.ui.terminal import TerminalUI
from github_cli.api.client import GitHubClient


@pytest.mark.unit
@pytest.mark.ui
class TestTerminalUI:
    """Test cases for TerminalUI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=GitHubClient)
        
        # Mock console
        self.mock_console = Mock(spec=Console)
        
        with patch('github_cli.ui.terminal.Console', return_value=self.mock_console):
            self.terminal_ui = TerminalUI(self.mock_client)

    def test_terminal_ui_initialization(self):
        """Test TerminalUI initialization."""
        assert self.terminal_ui.client == self.mock_client
        assert self.terminal_ui.console == self.mock_console

    def test_display_success(self):
        """Test displaying success message."""
        message = "Operation completed successfully"
        
        self.terminal_ui.display_success(message)
        
        self.mock_console.print.assert_called_once()
        call_args = self.mock_console.print.call_args[0][0]
        assert "✅" in str(call_args)
        assert message in str(call_args)

    def test_display_error(self):
        """Test displaying error message."""
        message = "An error occurred"
        
        self.terminal_ui.display_error(message)
        
        self.mock_console.print.assert_called_once()
        call_args = self.mock_console.print.call_args[0][0]
        assert "❌" in str(call_args)
        assert message in str(call_args)

    def test_display_warning(self):
        """Test displaying warning message."""
        message = "This is a warning"
        
        self.terminal_ui.display_warning(message)
        
        self.mock_console.print.assert_called_once()
        call_args = self.mock_console.print.call_args[0][0]
        assert "⚠️" in str(call_args)
        assert message in str(call_args)

    def test_display_info(self):
        """Test displaying info message."""
        message = "Information message"
        
        self.terminal_ui.display_info(message)
        
        self.mock_console.print.assert_called_once()
        call_args = self.mock_console.print.call_args[0][0]
        assert "ℹ️" in str(call_args)
        assert message in str(call_args)

    def test_display_repositories(self):
        """Test displaying repositories list."""
        repositories = [
            {
                "name": "repo1",
                "full_name": "user/repo1",
                "description": "First repository",
                "stargazers_count": 10,
                "language": "Python",
                "updated_at": "2023-12-01T00:00:00Z"
            },
            {
                "name": "repo2",
                "full_name": "user/repo2",
                "description": "Second repository",
                "stargazers_count": 25,
                "language": "JavaScript",
                "updated_at": "2023-11-15T00:00:00Z"
            }
        ]
        
        self.terminal_ui.display_repositories(repositories)
        
        # Should call console.print with a table
        self.mock_console.print.assert_called()
        call_args = self.mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_display_repositories_empty(self):
        """Test displaying empty repositories list."""
        repositories = []
        
        self.terminal_ui.display_repositories(repositories)
        
        self.mock_console.print.assert_called()
        # Should display a message about no repositories
        call_args = self.mock_console.print.call_args[0][0]
        assert "No repositories found" in str(call_args)

    def test_display_pull_requests(self):
        """Test displaying pull requests list."""
        pull_requests = [
            {
                "number": 42,
                "title": "Add new feature",
                "state": "open",
                "user": {"login": "contributor1"},
                "created_at": "2023-12-01T00:00:00Z",
                "updated_at": "2023-12-01T12:00:00Z"
            },
            {
                "number": 43,
                "title": "Fix bug",
                "state": "closed",
                "user": {"login": "contributor2"},
                "created_at": "2023-11-30T00:00:00Z",
                "updated_at": "2023-12-01T10:00:00Z"
            }
        ]
        
        self.terminal_ui.display_pull_requests(pull_requests)
        
        # Should call console.print with a table
        self.mock_console.print.assert_called()
        call_args = self.mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_display_pull_requests_empty(self):
        """Test displaying empty pull requests list."""
        pull_requests = []
        
        self.terminal_ui.display_pull_requests(pull_requests)
        
        self.mock_console.print.assert_called()
        call_args = self.mock_console.print.call_args[0][0]
        assert "No pull requests found" in str(call_args)

    def test_display_issues(self):
        """Test displaying issues list."""
        issues = [
            {
                "number": 1,
                "title": "Bug report",
                "state": "open",
                "user": {"login": "reporter1"},
                "labels": [{"name": "bug", "color": "d73a4a"}],
                "created_at": "2023-12-01T00:00:00Z"
            },
            {
                "number": 2,
                "title": "Feature request",
                "state": "closed",
                "user": {"login": "reporter2"},
                "labels": [{"name": "enhancement", "color": "a2eeef"}],
                "created_at": "2023-11-30T00:00:00Z"
            }
        ]
        
        self.terminal_ui.display_issues(issues)
        
        # Should call console.print with a table
        self.mock_console.print.assert_called()
        call_args = self.mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_display_user_info(self):
        """Test displaying user information."""
        user_info = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "bio": "Software developer",
            "company": "Test Company",
            "location": "Test City",
            "public_repos": 10,
            "followers": 100,
            "following": 50,
            "created_at": "2020-01-01T00:00:00Z"
        }
        
        self.terminal_ui.display_user_info(user_info)
        
        # Should call console.print multiple times for different sections
        assert self.mock_console.print.call_count > 1

    def test_display_workflow_runs(self):
        """Test displaying workflow runs."""
        workflow_runs = [
            {
                "id": 123,
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "head_branch": "main",
                "head_sha": "abc123",
                "created_at": "2023-12-01T00:00:00Z",
                "updated_at": "2023-12-01T00:05:00Z"
            },
            {
                "id": 124,
                "name": "Deploy",
                "status": "in_progress",
                "conclusion": None,
                "head_branch": "main",
                "head_sha": "def456",
                "created_at": "2023-12-01T00:10:00Z",
                "updated_at": "2023-12-01T00:12:00Z"
            }
        ]
        
        self.terminal_ui.display_workflow_runs(workflow_runs)
        
        # Should call console.print with a table
        self.mock_console.print.assert_called()
        call_args = self.mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_display_notifications(self):
        """Test displaying notifications."""
        notifications = [
            {
                "id": "1",
                "subject": {
                    "title": "New issue opened",
                    "type": "Issue"
                },
                "repository": {
                    "full_name": "user/repo1"
                },
                "reason": "subscribed",
                "unread": True,
                "updated_at": "2023-12-01T00:00:00Z"
            },
            {
                "id": "2",
                "subject": {
                    "title": "Pull request merged",
                    "type": "PullRequest"
                },
                "repository": {
                    "full_name": "user/repo2"
                },
                "reason": "author",
                "unread": False,
                "updated_at": "2023-11-30T00:00:00Z"
            }
        ]
        
        self.terminal_ui.display_notifications(notifications)
        
        # Should call console.print with a table
        self.mock_console.print.assert_called()
        call_args = self.mock_console.print.call_args[0][0]
        assert isinstance(call_args, Table)

    def test_create_table_basic(self):
        """Test creating basic table."""
        with patch('github_cli.ui.terminal.Table') as mock_table_class:
            mock_table = Mock()
            mock_table_class.return_value = mock_table
            
            table = self.terminal_ui._create_table("Test Title")
            
            assert table == mock_table
            mock_table_class.assert_called_once()
            mock_table.add_column.assert_not_called()  # No columns added yet

    def test_create_table_with_columns(self):
        """Test creating table with columns."""
        with patch('github_cli.ui.terminal.Table') as mock_table_class:
            mock_table = Mock()
            mock_table_class.return_value = mock_table
            
            columns = ["Name", "Description", "Stars"]
            table = self.terminal_ui._create_table("Test Title", columns)
            
            assert table == mock_table
            assert mock_table.add_column.call_count == len(columns)

    def test_format_datetime(self):
        """Test datetime formatting."""
        # Test with ISO format
        iso_datetime = "2023-12-01T12:30:45Z"
        formatted = self.terminal_ui._format_datetime(iso_datetime)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_datetime_invalid(self):
        """Test datetime formatting with invalid input."""
        invalid_datetime = "invalid-date"
        formatted = self.terminal_ui._format_datetime(invalid_datetime)
        
        assert formatted == invalid_datetime

    def test_format_datetime_none(self):
        """Test datetime formatting with None input."""
        formatted = self.terminal_ui._format_datetime(None)
        
        assert formatted == "N/A"

    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "This is a very long text that should be truncated"
        max_length = 20
        
        truncated = self.terminal_ui._truncate_text(long_text, max_length)
        
        assert len(truncated) <= max_length
        if len(long_text) > max_length:
            assert truncated.endswith("...")

    def test_truncate_text_short(self):
        """Test text truncation with short text."""
        short_text = "Short text"
        max_length = 20
        
        truncated = self.terminal_ui._truncate_text(short_text, max_length)
        
        assert truncated == short_text

    def test_get_status_color(self):
        """Test status color mapping."""
        # Test success status
        success_color = self.terminal_ui._get_status_color("success")
        assert success_color == "green"
        
        # Test failure status
        failure_color = self.terminal_ui._get_status_color("failure")
        assert failure_color == "red"
        
        # Test pending status
        pending_color = self.terminal_ui._get_status_color("pending")
        assert pending_color == "yellow"
        
        # Test unknown status
        unknown_color = self.terminal_ui._get_status_color("unknown")
        assert unknown_color == "white"

    def test_format_labels(self):
        """Test label formatting."""
        labels = [
            {"name": "bug", "color": "d73a4a"},
            {"name": "enhancement", "color": "a2eeef"}
        ]
        
        formatted = self.terminal_ui._format_labels(labels)
        
        assert isinstance(formatted, str)
        assert "bug" in formatted
        assert "enhancement" in formatted

    def test_format_labels_empty(self):
        """Test label formatting with empty list."""
        labels = []
        
        formatted = self.terminal_ui._format_labels(labels)
        
        assert formatted == ""

    def test_clear_screen(self):
        """Test clearing screen."""
        self.terminal_ui.clear_screen()
        
        self.mock_console.clear.assert_called_once()

    def test_print_separator(self):
        """Test printing separator."""
        self.terminal_ui.print_separator()
        
        self.mock_console.print.assert_called_once()
        call_args = self.mock_console.print.call_args[0][0]
        assert "─" in str(call_args)

    def test_print_header(self):
        """Test printing header."""
        title = "Test Header"
        
        self.terminal_ui.print_header(title)
        
        # Should print multiple times (header, title, separator)
        assert self.mock_console.print.call_count >= 2

    def test_prompt_user_input(self):
        """Test prompting for user input."""
        prompt_text = "Enter your choice: "
        
        with patch('builtins.input', return_value="test_input") as mock_input:
            result = self.terminal_ui.prompt_user_input(prompt_text)
            
            assert result == "test_input"
            mock_input.assert_called_once_with(prompt_text)

    def test_confirm_action(self):
        """Test confirming user action."""
        message = "Are you sure?"
        
        with patch('builtins.input', return_value="y") as mock_input:
            result = self.terminal_ui.confirm_action(message)
            
            assert result is True
            mock_input.assert_called_once()

    def test_confirm_action_negative(self):
        """Test confirming user action with negative response."""
        message = "Are you sure?"
        
        with patch('builtins.input', return_value="n") as mock_input:
            result = self.terminal_ui.confirm_action(message)
            
            assert result is False
