"""
Unit tests for GitCommands class.
"""

import pytest
import asyncio
import subprocess
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from github_cli.git.commands import GitCommands, handle_git_command
from github_cli.utils.exceptions import GitHubCLIError


@pytest.mark.unit
class TestGitCommands:
    """Test cases for GitCommands class."""

    def test_init(self, mock_github_client, mock_terminal_ui):
        """Test GitCommands initialization."""
        git_cmds = GitCommands(mock_github_client, mock_terminal_ui)
        
        assert git_cmds.client == mock_github_client
        assert git_cmds.terminal == mock_terminal_ui
        assert git_cmds.logger is not None

    @pytest.mark.asyncio
    async def test_run_git_command_success(self, git_commands, mock_subprocess_run):
        """Test successful git command execution."""
        mock_result = mock_subprocess_run(returncode=0, stdout="test output")
        
        with patch('subprocess.run', return_value=mock_result):
            result = await git_commands._run_git_command(["status"])
            
        assert result == "test output"

    @pytest.mark.asyncio
    async def test_run_git_command_failure(self, git_commands, mock_subprocess_run):
        """Test git command execution failure."""
        mock_result = mock_subprocess_run(returncode=1, stderr="error message")
        
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, "git", stderr="error message")):
            with pytest.raises(GitHubCLIError, match="Git command failed: error message"):
                await git_commands._run_git_command(["status"])

    @pytest.mark.asyncio
    async def test_run_git_command_not_found(self, git_commands):
        """Test git command when git is not installed."""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            with pytest.raises(GitHubCLIError, match="Git not found. Please install Git."):
                await git_commands._run_git_command(["status"])

    @pytest.mark.asyncio
    async def test_get_current_repo_ssh_url(self, git_commands, sample_remote_urls):
        """Test parsing SSH GitHub URL."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_remote_urls["ssh"]):
            result = await git_commands.get_current_repo()
            
        assert result == "owner/repo"

    @pytest.mark.asyncio
    async def test_get_current_repo_https_url(self, git_commands, sample_remote_urls):
        """Test parsing HTTPS GitHub URL."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_remote_urls["https"]):
            result = await git_commands.get_current_repo()
            
        assert result == "owner/repo"

    @pytest.mark.asyncio
    async def test_get_current_repo_https_no_git(self, git_commands, sample_remote_urls):
        """Test parsing HTTPS GitHub URL without .git extension."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_remote_urls["https_no_git"]):
            result = await git_commands.get_current_repo()
            
        assert result == "owner/repo"

    @pytest.mark.asyncio
    async def test_get_current_repo_non_github(self, git_commands, sample_remote_urls):
        """Test non-GitHub URL returns None."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_remote_urls["non_github"]):
            result = await git_commands.get_current_repo()
            
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_repo_git_error(self, git_commands):
        """Test get_current_repo when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            result = await git_commands.get_current_repo()
            
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_branch_success(self, git_commands):
        """Test getting current branch successfully."""
        with patch.object(git_commands, '_run_git_command', return_value="main"):
            result = await git_commands.get_current_branch()
            
        assert result == "main"

    @pytest.mark.asyncio
    async def test_get_current_branch_error(self, git_commands):
        """Test get_current_branch when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            result = await git_commands.get_current_branch()
            
        assert result is None

    @pytest.mark.asyncio
    async def test_get_repo_status_success(self, git_commands, sample_git_status_output):
        """Test getting repository status successfully."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_git_status_output), \
             patch.object(git_commands, 'get_current_branch', return_value="main"), \
             patch.object(git_commands, 'get_current_repo', return_value="owner/repo"):
            
            result = await git_commands.get_repo_status()
            
        assert result["repository"] == "owner/repo"
        assert result["branch"] == "main"
        assert "modified_file.py" in result["modified"]
        assert "added_file.py" in result["added"]
        assert "deleted_file.py" in result["deleted"]
        assert "untracked_file.py" in result["untracked"]
        assert not result["clean"]

    @pytest.mark.asyncio
    async def test_get_repo_status_clean(self, git_commands):
        """Test getting repository status when clean."""
        with patch.object(git_commands, '_run_git_command', return_value=""), \
             patch.object(git_commands, 'get_current_branch', return_value="main"), \
             patch.object(git_commands, 'get_current_repo', return_value="owner/repo"):
            
            result = await git_commands.get_repo_status()
            
        assert result["clean"] is True
        assert len(result["modified"]) == 0
        assert len(result["added"]) == 0
        assert len(result["deleted"]) == 0
        assert len(result["untracked"]) == 0

    @pytest.mark.asyncio
    async def test_get_repo_status_error(self, git_commands):
        """Test get_repo_status when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to get repository status"):
                await git_commands.get_repo_status()

    @pytest.mark.asyncio
    async def test_list_branches_local(self, git_commands, sample_git_branch_output):
        """Test listing local branches."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_git_branch_output):
            result = await git_commands.list_branches(remote=False)
            
        expected_branches = ["main", "feature/new-feature", "develop", "hotfix/urgent-fix"]
        assert set(result) == set(expected_branches)

    @pytest.mark.asyncio
    async def test_list_branches_remote(self, git_commands, sample_git_remote_branch_output):
        """Test listing remote branches."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_git_remote_branch_output):
            result = await git_commands.list_branches(remote=True)
            
        expected_branches = ["main", "develop", "feature/new-feature", "hotfix/urgent-fix"]
        assert set(result) == set(expected_branches)

    @pytest.mark.asyncio
    async def test_list_branches_error(self, git_commands):
        """Test list_branches when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to list branches"):
                await git_commands.list_branches()

    @pytest.mark.asyncio
    async def test_checkout_branch_existing(self, git_commands, mock_terminal_ui):
        """Test checking out existing branch."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.checkout_branch("develop")
            
        mock_terminal_ui.display_success.assert_called_once_with("Switched to branch 'develop'")

    @pytest.mark.asyncio
    async def test_checkout_branch_create_new(self, git_commands, mock_terminal_ui):
        """Test checking out and creating new branch."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.checkout_branch("new-feature", create=True)
            
        mock_terminal_ui.display_success.assert_called_once_with("Switched to branch 'new-feature'")

    @pytest.mark.asyncio
    async def test_checkout_branch_error(self, git_commands):
        """Test checkout_branch when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to checkout branch"):
                await git_commands.checkout_branch("develop")

    @pytest.mark.asyncio
    async def test_create_branch_simple(self, git_commands, mock_terminal_ui):
        """Test creating new branch from current."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.create_branch("new-feature")
            
        mock_terminal_ui.display_success.assert_called_once_with("Created and switched to branch 'new-feature'")

    @pytest.mark.asyncio
    async def test_create_branch_from_branch(self, git_commands, mock_terminal_ui):
        """Test creating new branch from specific branch."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.create_branch("new-feature", from_branch="develop")
            
        mock_terminal_ui.display_success.assert_called_once_with("Created and switched to branch 'new-feature'")

    @pytest.mark.asyncio
    async def test_create_branch_error(self, git_commands):
        """Test create_branch when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to create branch"):
                await git_commands.create_branch("new-feature")

    @pytest.mark.asyncio
    async def test_delete_branch_normal(self, git_commands, mock_terminal_ui):
        """Test deleting branch normally."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.delete_branch("old-feature")
            
        mock_terminal_ui.display_success.assert_called_once_with("Deleted branch 'old-feature'")

    @pytest.mark.asyncio
    async def test_delete_branch_force(self, git_commands, mock_terminal_ui):
        """Test force deleting branch."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.delete_branch("old-feature", force=True)
            
        mock_terminal_ui.display_success.assert_called_once_with("Deleted branch 'old-feature'")

    @pytest.mark.asyncio
    async def test_delete_branch_error(self, git_commands):
        """Test delete_branch when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to delete branch"):
                await git_commands.delete_branch("old-feature")

    @pytest.mark.asyncio
    async def test_get_commit_log_success(self, git_commands, sample_git_log_output):
        """Test getting commit log successfully."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_git_log_output):
            result = await git_commands.get_commit_log(limit=3)

        assert len(result) == 3
        assert result[0]["hash"] == "abc123"
        assert result[0]["author_name"] == "John Doe"
        assert result[0]["author_email"] == "john@example.com"
        assert result[0]["date"] == "2023-12-01"
        assert result[0]["message"] == "Initial commit"

    @pytest.mark.asyncio
    async def test_get_commit_log_with_branch(self, git_commands, sample_git_log_output):
        """Test getting commit log for specific branch."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_git_log_output):
            result = await git_commands.get_commit_log(limit=5, branch="develop")

        assert len(result) == 3  # Based on sample output

    @pytest.mark.asyncio
    async def test_get_commit_log_empty(self, git_commands):
        """Test getting commit log when no commits."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            result = await git_commands.get_commit_log()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_commit_log_malformed(self, git_commands):
        """Test getting commit log with malformed output."""
        malformed_output = "abc123|John Doe|incomplete"
        with patch.object(git_commands, '_run_git_command', return_value=malformed_output):
            result = await git_commands.get_commit_log()

        assert result == []  # Should skip malformed lines

    @pytest.mark.asyncio
    async def test_get_commit_log_error(self, git_commands):
        """Test get_commit_log when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to get commit log"):
                await git_commands.get_commit_log()

    @pytest.mark.asyncio
    async def test_stash_changes_with_message(self, git_commands, mock_terminal_ui):
        """Test stashing changes with message."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.stash_changes("Work in progress")

        mock_terminal_ui.display_success.assert_called_once_with("Changes stashed")

    @pytest.mark.asyncio
    async def test_stash_changes_without_message(self, git_commands, mock_terminal_ui):
        """Test stashing changes without message."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.stash_changes()

        mock_terminal_ui.display_success.assert_called_once_with("Changes stashed")

    @pytest.mark.asyncio
    async def test_stash_changes_error(self, git_commands):
        """Test stash_changes when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to stash changes"):
                await git_commands.stash_changes()

    @pytest.mark.asyncio
    async def test_list_stashes_success(self, git_commands, sample_git_stash_output):
        """Test listing stashes successfully."""
        with patch.object(git_commands, '_run_git_command', return_value=sample_git_stash_output):
            result = await git_commands.list_stashes()

        assert len(result) == 2
        assert result[0]["index"] == "stash@{0}"
        assert result[0]["message"] == "WIP on main: abc123 Initial commit"
        assert result[0]["date"] == "2023-12-01 10:00:00"

    @pytest.mark.asyncio
    async def test_list_stashes_empty(self, git_commands):
        """Test listing stashes when none exist."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            result = await git_commands.list_stashes()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_stashes_malformed(self, git_commands):
        """Test listing stashes with malformed output."""
        malformed_output = "stash@{0}|incomplete"
        with patch.object(git_commands, '_run_git_command', return_value=malformed_output):
            result = await git_commands.list_stashes()

        assert result == []  # Should skip malformed lines

    @pytest.mark.asyncio
    async def test_list_stashes_error(self, git_commands):
        """Test list_stashes when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to list stashes"):
                await git_commands.list_stashes()

    @pytest.mark.asyncio
    async def test_apply_stash_with_index(self, git_commands, mock_terminal_ui):
        """Test applying specific stash."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.apply_stash("stash@{0}")

        mock_terminal_ui.display_success.assert_called_once_with("Stash applied")

    @pytest.mark.asyncio
    async def test_apply_stash_without_index(self, git_commands, mock_terminal_ui):
        """Test applying latest stash."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.apply_stash()

        mock_terminal_ui.display_success.assert_called_once_with("Stash applied")

    @pytest.mark.asyncio
    async def test_apply_stash_error(self, git_commands):
        """Test apply_stash when git command fails."""
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git error")):
            with pytest.raises(GitHubCLIError, match="Failed to apply stash"):
                await git_commands.apply_stash()


@pytest.mark.unit
class TestHandleGitCommand:
    """Test cases for handle_git_command function."""

    @pytest.mark.asyncio
    async def test_handle_branch_command(self, git_commands):
        """Test handling branch command."""
        args = Mock()
        args.action = "branch"

        with patch.object(git_commands, 'list_branches', return_value=["main", "develop"]):
            await handle_git_command(args, git_commands)

        git_commands.terminal.display_git_branches.assert_called_once_with(["main", "develop"])

    @pytest.mark.asyncio
    async def test_handle_checkout_command_success(self, git_commands):
        """Test handling checkout command successfully."""
        args = Mock()
        args.action = "checkout"
        args.branch = "develop"

        with patch.object(git_commands, 'checkout_branch', return_value=None):
            await handle_git_command(args, git_commands)

    @pytest.mark.asyncio
    async def test_handle_checkout_command_no_branch(self, git_commands):
        """Test handling checkout command without branch name."""
        args = Mock()
        args.action = "checkout"
        args.branch = None

        await handle_git_command(args, git_commands)

        git_commands.terminal.display_error.assert_called_once_with("Branch name required for checkout")

    @pytest.mark.asyncio
    async def test_handle_stash_list_command(self, git_commands):
        """Test handling stash list command."""
        args = Mock()
        args.action = "stash"
        args.stash_action = "list"

        stashes = [{"index": "stash@{0}", "message": "WIP", "date": "2023-12-01"}]
        with patch.object(git_commands, 'list_stashes', return_value=stashes):
            await handle_git_command(args, git_commands)

        git_commands.terminal.display_git_stashes.assert_called_once_with(stashes)

    @pytest.mark.asyncio
    async def test_handle_stash_apply_command(self, git_commands):
        """Test handling stash apply command."""
        args = Mock()
        args.action = "stash"
        args.stash_action = "apply"
        args.stash_index = "stash@{0}"

        with patch.object(git_commands, 'apply_stash', return_value=None):
            await handle_git_command(args, git_commands)

    @pytest.mark.asyncio
    async def test_handle_stash_save_command(self, git_commands):
        """Test handling stash save command."""
        args = Mock()
        args.action = "stash"
        args.stash_action = "save"
        args.message = "Work in progress"

        with patch.object(git_commands, 'stash_changes', return_value=None):
            await handle_git_command(args, git_commands)

    @pytest.mark.asyncio
    async def test_handle_stash_command_no_action(self, git_commands):
        """Test handling stash command without specific action."""
        args = Mock()
        args.action = "stash"
        # No stash_action attribute

        with patch.object(git_commands, 'stash_changes', return_value=None):
            await handle_git_command(args, git_commands)

    @pytest.mark.asyncio
    async def test_handle_status_command(self, git_commands):
        """Test handling status command."""
        args = Mock()
        args.action = "status"

        status = {"repository": "owner/repo", "branch": "main", "clean": True}
        with patch.object(git_commands, 'get_repo_status', return_value=status):
            await handle_git_command(args, git_commands)

        git_commands.terminal.display_git_status.assert_called_once_with(status)

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self, git_commands):
        """Test handling unknown command."""
        args = Mock()
        args.action = "unknown"

        await handle_git_command(args, git_commands)

        git_commands.terminal.display_error.assert_called_once_with("Unknown git action: unknown")

    @pytest.mark.asyncio
    async def test_handle_command_with_error(self, git_commands):
        """Test handling command that raises GitHubCLIError."""
        args = Mock()
        args.action = "branch"

        error = GitHubCLIError("Test error")
        with patch.object(git_commands, 'list_branches', side_effect=error):
            await handle_git_command(args, git_commands)

        git_commands.terminal.display_error.assert_called_once_with("Test error")
