"""
Edge case tests for GitCommands class.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from github_cli.git.commands import GitCommands
from github_cli.utils.exceptions import GitHubCLIError


@pytest.mark.unit
class TestGitCommandsEdgeCases:
    """Test edge cases and error conditions for GitCommands."""

    @pytest.mark.asyncio
    async def test_get_current_repo_malformed_ssh_url(self, git_commands):
        """Test parsing malformed SSH URL."""
        malformed_urls = [
            "git@github.com",  # Missing colon and repo - should return None
            "git@github.com:",  # Missing repo - should return empty string
        ]

        # Test URL without colon (should return None)
        with patch.object(git_commands, '_run_git_command', return_value="git@github.com"):
            result = await git_commands.get_current_repo()
            assert result is None

        # Test URL with colon but no repo (should return empty string)
        with patch.object(git_commands, '_run_git_command', return_value="git@github.com:"):
            result = await git_commands.get_current_repo()
            assert result == ""

        # Test URL with only owner (should return "owner")
        with patch.object(git_commands, '_run_git_command', return_value="git@github.com:owner"):
            result = await git_commands.get_current_repo()
            assert result == "owner"

        # Test URL with owner and trailing slash (should return "owner/")
        with patch.object(git_commands, '_run_git_command', return_value="git@github.com:owner/"):
            result = await git_commands.get_current_repo()
            assert result == "owner/"

    @pytest.mark.asyncio
    async def test_get_current_repo_malformed_https_url(self, git_commands):
        """Test parsing malformed HTTPS URL."""
        # Test URL with only base path (should return empty string)
        with patch.object(git_commands, '_run_git_command', return_value="https://github.com/"):
            result = await git_commands.get_current_repo()
            assert result == ""

        # Test URL with only owner (should return "owner")
        with patch.object(git_commands, '_run_git_command', return_value="https://github.com/owner"):
            result = await git_commands.get_current_repo()
            assert result == "owner"

        # Test URL with owner and trailing slash (should return "owner/")
        with patch.object(git_commands, '_run_git_command', return_value="https://github.com/owner/"):
            result = await git_commands.get_current_repo()
            assert result == "owner/"

        # Test non-GitHub domain (should return None)
        with patch.object(git_commands, '_run_git_command', return_value="https://example.com/owner/repo.git"):
            result = await git_commands.get_current_repo()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_repo_status_complex_filenames(self, git_commands):
        """Test repository status with complex filenames."""
        complex_status = """M  "file with spaces.py"
A  file-with-dashes.py
D  file_with_underscores.py
?? "file with (parentheses).py"
 M "staged file.py\""""
        
        with patch.object(git_commands, '_run_git_command', return_value=complex_status), \
             patch.object(git_commands, 'get_current_branch', return_value="main"), \
             patch.object(git_commands, 'get_current_repo', return_value="owner/repo"):
            
            result = await git_commands.get_repo_status()
            
            # Should handle complex filenames correctly
            assert len(result["modified"]) >= 1
            assert len(result["added"]) >= 1
            assert len(result["deleted"]) >= 1
            assert len(result["untracked"]) >= 1

    @pytest.mark.asyncio
    async def test_list_branches_with_special_characters(self, git_commands):
        """Test listing branches with special characters."""
        branch_output = """  feature/user-123
* main
  hotfix/issue-#456
  release/v1.0.0
  bugfix/fix_underscore_issue"""
        
        with patch.object(git_commands, '_run_git_command', return_value=branch_output):
            result = await git_commands.list_branches()
            
            expected_branches = [
                "main", "feature/user-123", "hotfix/issue-#456", 
                "release/v1.0.0", "bugfix/fix_underscore_issue"
            ]
            assert set(result) == set(expected_branches)

    @pytest.mark.asyncio
    async def test_list_branches_empty_output(self, git_commands):
        """Test listing branches with empty output."""
        with patch.object(git_commands, '_run_git_command', return_value=""):
            result = await git_commands.list_branches()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_list_branches_only_current_branch(self, git_commands):
        """Test listing branches when only current branch exists."""
        with patch.object(git_commands, '_run_git_command', return_value="* main"):
            result = await git_commands.list_branches()
            
            assert result == ["main"]

    @pytest.mark.asyncio
    async def test_get_commit_log_unicode_characters(self, git_commands):
        """Test commit log with unicode characters."""
        unicode_log = """abc123|José García|jose@example.com|2023-12-01|Añadir función de búsqueda
def456|李小明|li@example.com|2023-12-02|添加新功能
ghi789|محمد أحمد|mohamed@example.com|2023-12-03|إضافة ميزة جديدة"""
        
        with patch.object(git_commands, '_run_git_command', return_value=unicode_log):
            result = await git_commands.get_commit_log()
            
            assert len(result) == 3
            assert result[0]["author_name"] == "José García"
            assert result[1]["author_name"] == "李小明"
            assert result[2]["author_name"] == "محمد أحمد"

    @pytest.mark.asyncio
    async def test_get_commit_log_very_long_message(self, git_commands):
        """Test commit log with very long commit message."""
        long_message = "A" * 1000  # Very long commit message
        long_log = f"abc123|John Doe|john@example.com|2023-12-01|{long_message}"
        
        with patch.object(git_commands, '_run_git_command', return_value=long_log):
            result = await git_commands.get_commit_log()
            
            assert len(result) == 1
            assert result[0]["message"] == long_message

    @pytest.mark.asyncio
    async def test_list_stashes_with_complex_messages(self, git_commands):
        """Test listing stashes with complex messages."""
        complex_stash = """stash@{0}|WIP on feature/complex: abc123 Fix issue with "quotes" and |pipes||2023-12-01 10:00:00
stash@{1}|On main: def456 Add feature with émojis 🚀|2023-12-02 15:30:00"""
        
        with patch.object(git_commands, '_run_git_command', return_value=complex_stash):
            result = await git_commands.list_stashes()
            
            assert len(result) == 2
            assert "quotes" in result[0]["message"]
            assert "🚀" in result[1]["message"]

    @pytest.mark.asyncio
    async def test_run_git_command_with_cwd(self, git_commands):
        """Test running git command with custom working directory."""
        mock_result = Mock()
        mock_result.stdout = "test output"
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = await git_commands._run_git_command(["status"], cwd="/custom/path")
            
            assert result == "test output"
            mock_run.assert_called_once()
            assert mock_run.call_args[1]['cwd'] == "/custom/path"

    @pytest.mark.asyncio
    async def test_run_git_command_timeout_simulation(self, git_commands):
        """Test git command timeout handling."""
        # Simulate a timeout by raising CalledProcessError
        error = subprocess.CalledProcessError(124, "git", stderr="timeout")
        
        with patch('subprocess.run', side_effect=error):
            with pytest.raises(GitHubCLIError, match="Git command failed: timeout"):
                await git_commands._run_git_command(["status"])

    @pytest.mark.asyncio
    async def test_checkout_branch_with_special_characters(self, git_commands):
        """Test checking out branch with special characters."""
        special_branch = "feature/issue-#123_fix"
        
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.checkout_branch(special_branch)
            
            git_commands.terminal.display_success.assert_called_once_with(
                f"Switched to branch '{special_branch}'"
            )

    @pytest.mark.asyncio
    async def test_create_branch_with_slash_in_name(self, git_commands):
        """Test creating branch with slashes in name."""
        branch_name = "feature/user/new-feature"
        
        with patch.object(git_commands, '_run_git_command', return_value=""):
            await git_commands.create_branch(branch_name)
            
            git_commands.terminal.display_success.assert_called_once_with(
                f"Created and switched to branch '{branch_name}'"
            )

    @pytest.mark.asyncio
    async def test_delete_branch_current_branch_error(self, git_commands):
        """Test deleting current branch (should fail)."""
        error = subprocess.CalledProcessError(
            1, "git", stderr="error: Cannot delete branch 'main' checked out at"
        )
        
        with patch.object(git_commands, '_run_git_command', side_effect=GitHubCLIError("Git command failed: error: Cannot delete branch 'main' checked out at")):
            with pytest.raises(GitHubCLIError, match="Failed to delete branch"):
                await git_commands.delete_branch("main")

    @pytest.mark.asyncio
    async def test_stash_changes_no_changes_to_stash(self, git_commands):
        """Test stashing when there are no changes."""
        # Git typically outputs a message when there's nothing to stash
        with patch.object(git_commands, '_run_git_command', return_value="No local changes to save"):
            await git_commands.stash_changes()
            
            git_commands.terminal.display_success.assert_called_once_with("Changes stashed")

    @pytest.mark.asyncio
    async def test_apply_stash_no_stash_exists(self, git_commands):
        """Test applying stash when no stash exists."""
        error = GitHubCLIError("Git command failed: fatal: No stash entries found.")
        
        with patch.object(git_commands, '_run_git_command', side_effect=error):
            with pytest.raises(GitHubCLIError, match="Failed to apply stash"):
                await git_commands.apply_stash()

    @pytest.mark.asyncio
    async def test_concurrent_git_operations(self, git_commands):
        """Test multiple git operations running concurrently."""
        import asyncio
        
        async def mock_git_command(args, cwd=None):
            await asyncio.sleep(0.01)  # Simulate some delay
            if args == ["branch", "--show-current"]:
                return "main"
            elif args == ["remote", "get-url", "origin"]:
                return "https://github.com/owner/repo.git"
            return ""
        
        with patch.object(git_commands, '_run_git_command', side_effect=mock_git_command):
            # Run multiple operations concurrently
            tasks = [
                git_commands.get_current_branch(),
                git_commands.get_current_repo(),
                git_commands.get_current_branch(),
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert results[0] == "main"
            assert results[1] == "owner/repo"
            assert results[2] == "main"
