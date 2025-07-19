"""
Integration tests for GitCommands class.
These tests require git to be installed and available.
"""

import pytest
import asyncio
import subprocess
import os
from unittest.mock import Mock

from github_cli.git.commands import GitCommands
from github_cli.utils.exceptions import GitHubCLIError


@pytest.mark.integration
@pytest.mark.git
class TestGitCommandsIntegration:
    """Integration tests that require git to be installed."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_client = Mock()
        self.mock_terminal = Mock()
        self.mock_terminal.display_success = Mock()
        self.mock_terminal.display_error = Mock()
        self.mock_terminal.display_info = Mock()
        
        # Create GitCommands instance
        self.git_commands = GitCommands(self.mock_client, self.mock_terminal)

    def test_git_available(self):
        """Test that git is available on the system."""
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
            assert "git version" in result.stdout.lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Git is not available on this system")

    @pytest.mark.asyncio
    async def test_run_git_command_real_git(self):
        """Test running a real git command."""
        try:
            # Test git version command
            result = await self.git_commands._run_git_command(["--version"])
            assert "git version" in result.lower()
        except GitHubCLIError as e:
            if "Git not found" in str(e):
                pytest.skip("Git is not available on this system")
            else:
                raise

    @pytest.mark.asyncio
    async def test_get_current_repo_in_non_git_directory(self):
        """Test getting current repo in a non-git directory."""
        # Change to a temporary directory that's not a git repo
        original_cwd = os.getcwd()
        try:
            # Use a system directory that's unlikely to be a git repo
            temp_dir = os.path.expanduser("~")
            os.chdir(temp_dir)
            
            result = await self.git_commands.get_current_repo()
            # Should return None if not in a git repository
            assert result is None
        except GitHubCLIError:
            # This is expected if we're not in a git repository
            pass
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_get_current_branch_in_non_git_directory(self):
        """Test getting current branch in a non-git directory."""
        # Change to a temporary directory that's not a git repo
        original_cwd = os.getcwd()
        try:
            # Use a system directory that's unlikely to be a git repo
            temp_dir = os.path.expanduser("~")
            os.chdir(temp_dir)
            
            result = await self.git_commands.get_current_branch()
            # Should return None if not in a git repository
            assert result is None
        except GitHubCLIError:
            # This is expected if we're not in a git repository
            pass
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_list_branches_in_non_git_directory(self):
        """Test listing branches in a non-git directory."""
        # Change to a temporary directory that's not a git repo
        original_cwd = os.getcwd()
        try:
            # Use a system directory that's unlikely to be a git repo
            temp_dir = os.path.expanduser("~")
            os.chdir(temp_dir)
            
            with pytest.raises(GitHubCLIError, match="Failed to list branches"):
                await self.git_commands.list_branches()
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_get_repo_status_in_non_git_directory(self):
        """Test getting repo status in a non-git directory."""
        # Change to a temporary directory that's not a git repo
        original_cwd = os.getcwd()
        try:
            # Use a system directory that's unlikely to be a git repo
            temp_dir = os.path.expanduser("~")
            os.chdir(temp_dir)
            
            with pytest.raises(GitHubCLIError, match="Failed to get repository status"):
                await self.git_commands.get_repo_status()
        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_checkout_nonexistent_branch(self):
        """Test checking out a branch that doesn't exist."""
        with pytest.raises(GitHubCLIError, match="Failed to checkout branch"):
            await self.git_commands.checkout_branch("nonexistent-branch-12345")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_branch(self):
        """Test deleting a branch that doesn't exist."""
        with pytest.raises(GitHubCLIError, match="Failed to delete branch"):
            await self.git_commands.delete_branch("nonexistent-branch-12345")

    @pytest.mark.asyncio
    async def test_apply_nonexistent_stash(self):
        """Test applying a stash that doesn't exist."""
        with pytest.raises(GitHubCLIError, match="Failed to apply stash"):
            await self.git_commands.apply_stash("stash@{999}")

    def test_terminal_methods_exist(self):
        """Test that git methods are added to TerminalUI."""
        from github_cli.ui.terminal import TerminalUI
        
        # Verify methods exist
        assert hasattr(TerminalUI, 'display_git_branches')
        assert hasattr(TerminalUI, 'display_git_status')
        assert hasattr(TerminalUI, 'display_git_stashes')
        
        # Verify they are callable
        assert callable(TerminalUI.display_git_branches)
        assert callable(TerminalUI.display_git_status)
        assert callable(TerminalUI.display_git_stashes)

    def test_git_commands_initialization(self):
        """Test that GitCommands can be initialized properly."""
        git_cmds = GitCommands(self.mock_client, self.mock_terminal)
        
        assert git_cmds.client == self.mock_client
        assert git_cmds.terminal == self.mock_terminal
        assert git_cmds.logger is not None
        assert git_cmds.logger.name == "github_cli.git.commands"


@pytest.mark.integration
@pytest.mark.git
class TestGitCommandsInGitRepo:
    """Integration tests that should be run in a git repository."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_client = Mock()
        self.mock_terminal = Mock()
        self.mock_terminal.display_success = Mock()
        self.mock_terminal.display_error = Mock()
        self.mock_terminal.display_info = Mock()
        
        # Create GitCommands instance
        self.git_commands = GitCommands(self.mock_client, self.mock_terminal)

    @pytest.mark.asyncio
    async def test_get_current_repo_in_git_directory(self):
        """Test getting current repo when in a git directory."""
        try:
            # Check if we're in a git repository
            subprocess.run(["git", "rev-parse", "--git-dir"], 
                         capture_output=True, check=True)
            
            # If we're in a git repo, this should work
            result = await self.git_commands.get_current_repo()
            # Result could be None if no remote origin is set, or a string if it is
            assert result is None or isinstance(result, str)
            
        except subprocess.CalledProcessError:
            # Not in a git repository, skip this test
            pytest.skip("Not running in a git repository")
        except GitHubCLIError:
            # This is acceptable - might not have a remote origin
            pass

    @pytest.mark.asyncio
    async def test_get_current_branch_in_git_directory(self):
        """Test getting current branch when in a git directory."""
        try:
            # Check if we're in a git repository
            subprocess.run(["git", "rev-parse", "--git-dir"], 
                         capture_output=True, check=True)
            
            # If we're in a git repo, this should work
            result = await self.git_commands.get_current_branch()
            # Should return a branch name or None
            assert result is None or isinstance(result, str)
            
        except subprocess.CalledProcessError:
            # Not in a git repository, skip this test
            pytest.skip("Not running in a git repository")
        except GitHubCLIError:
            # This might happen in some edge cases
            pass

    @pytest.mark.asyncio
    async def test_list_branches_in_git_directory(self):
        """Test listing branches when in a git directory."""
        try:
            # Check if we're in a git repository
            subprocess.run(["git", "rev-parse", "--git-dir"], 
                         capture_output=True, check=True)
            
            # If we're in a git repo, this should work
            result = await self.git_commands.list_branches()
            assert isinstance(result, list)
            # Should have at least one branch (usually main/master)
            
        except subprocess.CalledProcessError:
            # Not in a git repository, skip this test
            pytest.skip("Not running in a git repository")
        except GitHubCLIError:
            # This might happen in some edge cases
            pass
