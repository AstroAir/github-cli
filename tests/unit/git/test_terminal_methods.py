"""
Unit tests for git-related terminal UI methods.

Tests the git display methods in TerminalUI.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from github_cli.ui.terminal import TerminalUI


@pytest.mark.unit
class TestGitTerminalMethods:
    """Test cases for git-related terminal UI methods."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock TerminalUI instance
        self.mock_client = Mock()
        self.terminal = TerminalUI(self.mock_client)
        # Mock the underlying terminal to avoid actual UI calls
        self.terminal._terminal = Mock()

    def test_display_git_branches_with_branches(self):
        """Test displaying git branches when branches exist."""
        branches = ["main", "develop", "feature/new-feature"]

        # Test that the method calls the console.print with a table
        self.terminal.display_git_branches(branches)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

        # Get the argument passed to console.print
        call_args = self.terminal.console.print.call_args[0]
        assert len(call_args) == 1  # Should be called with one argument (the table)

    def test_display_git_branches_empty(self):
        """Test displaying git branches when no branches exist."""
        branches = []
        
        with patch.object(self.terminal, 'display_info') as mock_display_info:
            self.terminal.display_git_branches(branches)
            
            mock_display_info.assert_called_once_with("No branches found")
            self.terminal.console.print.assert_not_called()

    def test_display_git_status_clean_repo(self):
        """Test displaying git status for clean repository."""
        status = {
            "repository": "owner/repo",
            "branch": "main",
            "clean": True,
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": []
        }

        # Test that the method calls the console.print
        self.terminal.display_git_status(status)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

        # Get the argument passed to console.print
        call_args = self.terminal.console.print.call_args[0]
        assert len(call_args) == 1  # Should be called with one argument (the panel)

    def test_display_git_status_dirty_repo(self):
        """Test displaying git status for dirty repository."""
        status = {
            "repository": "owner/repo",
            "branch": "develop",
            "clean": False,
            "modified": ["file1.py", "file2.py"],
            "added": ["file3.py"],
            "deleted": ["file4.py"],
            "untracked": ["file5.py"]
        }

        # Test that the method calls the console.print
        self.terminal.display_git_status(status)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

        # Get the argument passed to console.print
        call_args = self.terminal.console.print.call_args[0]
        assert len(call_args) == 1  # Should be called with one argument (the panel)

    def test_display_git_status_partial_changes(self):
        """Test displaying git status with only some types of changes."""
        status = {
            "repository": "test/repo",
            "branch": "feature",
            "clean": False,
            "modified": ["file1.py"],
            "added": [],
            "deleted": [],
            "untracked": ["file2.py"]
        }

        # Test that the method calls the console.print
        self.terminal.display_git_status(status)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

    def test_display_git_status_unknown_repo(self):
        """Test displaying git status with unknown repository info."""
        status = {
            "clean": True,
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": []
        }

        # Test that the method calls the console.print
        self.terminal.display_git_status(status)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

    def test_display_git_stashes_with_stashes(self):
        """Test displaying git stashes when stashes exist."""
        stashes = [
            {"index": "stash@{0}", "message": "WIP on main", "date": "2023-12-01"},
            {"index": "stash@{1}", "message": "Feature work", "date": "2023-12-02"}
        ]

        # Test that the method calls the console.print
        self.terminal.display_git_stashes(stashes)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

        # Get the argument passed to console.print
        call_args = self.terminal.console.print.call_args[0]
        assert len(call_args) == 1  # Should be called with one argument (the table)

    def test_display_git_stashes_empty(self):
        """Test displaying git stashes when no stashes exist."""
        stashes = []
        
        with patch.object(self.terminal, 'display_info') as mock_display_info:
            self.terminal.display_git_stashes(stashes)
            
            mock_display_info.assert_called_once_with("No stashes found")
            self.terminal.console.print.assert_not_called()

    def test_display_git_stashes_missing_fields(self):
        """Test displaying git stashes with missing fields."""
        stashes = [
            {"index": "stash@{0}"},  # Missing message and date
            {"message": "WIP", "date": "2023-12-01"}  # Missing index
        ]

        # Test that the method calls the console.print
        self.terminal.display_git_stashes(stashes)

        # Verify console.print was called once
        self.terminal.console.print.assert_called_once()

        # Get the argument passed to console.print
        call_args = self.terminal.console.print.call_args[0]
        assert len(call_args) == 1  # Should be called with one argument (the table)

    def test_methods_added_to_terminal_ui(self):
        """Test that git methods are properly added to TerminalUI class."""
        # Verify methods exist on the class
        assert hasattr(TerminalUI, 'display_git_branches')
        assert hasattr(TerminalUI, 'display_git_status')
        assert hasattr(TerminalUI, 'display_git_stashes')
        
        # Verify they are callable
        assert callable(TerminalUI.display_git_branches)
        assert callable(TerminalUI.display_git_status)
        assert callable(TerminalUI.display_git_stashes)
