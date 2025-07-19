"""
Git commands integration module
"""

import asyncio
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError


class GitCommands:
    """Git operations integration for GitHub CLI"""

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.logger = logging.getLogger(__name__)

    async def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> str:
        """Run a git command and return output"""
        cmd = ["git"] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise GitHubCLIError(f"Git command failed: {e.stderr.strip()}")
        except FileNotFoundError:
            raise GitHubCLIError("Git not found. Please install Git.")

    async def get_current_repo(self) -> Optional[str]:
        """Get current repository name from git remote"""
        try:
            remote_url = await self._run_git_command(["remote", "get-url", "origin"])

            # Parse GitHub repository from URL
            if "github.com" in remote_url:
                if remote_url.startswith("git@"):
                    # SSH format: git@github.com:owner/repo.git
                    parts = remote_url.split(":")
                    if len(parts) == 2:
                        repo = parts[1].replace(".git", "")
                        return repo
                elif remote_url.startswith("https://"):
                    # HTTPS format: https://github.com/owner/repo.git
                    parts = remote_url.replace(
                        "https://github.com/", "").replace(".git", "")
                    return parts

            return None
        except GitHubCLIError:
            return None

    async def get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            return await self._run_git_command(["branch", "--show-current"])
        except GitHubCLIError:
            return None

    async def get_repo_status(self) -> Dict[str, Any]:
        """Get repository status"""
        try:
            status_output = await self._run_git_command(["status", "--porcelain"])
            branch = await self.get_current_branch()
            repo = await self.get_current_repo()

            # Parse status
            modified = []
            added = []
            deleted = []
            untracked = []

            for line in status_output.split("\n"):
                if not line:
                    continue

                status_code = line[:3]
                filename = line[3:]

                if status_code.startswith("M"):
                    modified.append(filename)
                elif status_code.startswith("A"):
                    added.append(filename)
                elif status_code.startswith("D"):
                    deleted.append(filename)
                elif status_code.startswith("??"):
                    untracked.append(filename)

            return {
                "repository": repo,
                "branch": branch,
                "modified": modified,
                "added": added,
                "deleted": deleted,
                "untracked": untracked,
                "clean": not any([modified, added, deleted, untracked])
            }
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get repository status: {e}")

    async def list_branches(self, remote: bool = False) -> List[str]:
        """List git branches"""
        try:
            if remote:
                output = await self._run_git_command(["branch", "-r"])
            else:
                output = await self._run_git_command(["branch"])

            branches = []
            for line in output.split("\n"):
                line = line.strip()
                if line and not line.startswith("*"):
                    # Remove origin/ prefix for remote branches
                    if remote and line.startswith("origin/"):
                        line = line[7:]
                    branches.append(line)
                elif line.startswith("*"):
                    # Current branch
                    branches.append(line[2:])

            return branches
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list branches: {e}")

    async def checkout_branch(self, branch: str, create: bool = False) -> None:
        """Checkout a git branch"""
        try:
            if create:
                await self._run_git_command(["checkout", "-b", branch])
            else:
                await self._run_git_command(["checkout", branch])

            self.terminal.display_success(f"Switched to branch '{branch}'")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to checkout branch: {e}")

    async def create_branch(self, branch: str, from_branch: Optional[str] = None) -> None:
        """Create a new git branch"""
        try:
            if from_branch:
                await self._run_git_command(["checkout", "-b", branch, from_branch])
            else:
                await self._run_git_command(["checkout", "-b", branch])

            self.terminal.display_success(
                f"Created and switched to branch '{branch}'")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create branch: {e}")

    async def delete_branch(self, branch: str, force: bool = False) -> None:
        """Delete a git branch"""
        try:
            if force:
                await self._run_git_command(["branch", "-D", branch])
            else:
                await self._run_git_command(["branch", "-d", branch])

            self.terminal.display_success(f"Deleted branch '{branch}'")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to delete branch: {e}")

    async def get_commit_log(self, limit: int = 10, branch: Optional[str] = None) -> List[Dict[str, str]]:
        """Get git commit log"""
        try:
            args = [
                "log", f"--max-count={limit}", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=short"]
            if branch:
                args.append(branch)

            output = await self._run_git_command(args)

            commits = []
            for line in output.split("\n"):
                if not line:
                    continue

                parts = line.split("|", 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author_name": parts[1],
                        "author_email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })

            return commits
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get commit log: {e}")

    async def stash_changes(self, message: Optional[str] = None) -> None:
        """Stash current changes"""
        try:
            if message:
                await self._run_git_command(["stash", "push", "-m", message])
            else:
                await self._run_git_command(["stash"])

            self.terminal.display_success("Changes stashed")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to stash changes: {e}")

    async def list_stashes(self) -> List[Dict[str, str]]:
        """List git stashes"""
        try:
            output = await self._run_git_command(["stash", "list", "--pretty=format:%gd|%gs|%gD"])

            stashes = []
            for line in output.split("\n"):
                if not line:
                    continue

                parts = line.split("|", 2)
                if len(parts) == 3:
                    stashes.append({
                        "index": parts[0],
                        "message": parts[1],
                        "date": parts[2]
                    })

            return stashes
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list stashes: {e}")

    async def apply_stash(self, stash_index: Optional[str] = None) -> None:
        """Apply a git stash"""
        try:
            if stash_index:
                await self._run_git_command(["stash", "apply", stash_index])
            else:
                await self._run_git_command(["stash", "apply"])

            self.terminal.display_success("Stash applied")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to apply stash: {e}")


async def handle_git_command(args, git_cmds: GitCommands):
    """Handle git command dispatch"""
    try:
        match args.action:
            case "branch":
                branches = await git_cmds.list_branches()
                git_cmds.terminal.display_git_branches(branches)

            case "checkout":
                if not args.branch:
                    git_cmds.terminal.display_error(
                        "Branch name required for checkout")
                    return
                await git_cmds.checkout_branch(args.branch)

            case "stash":
                if hasattr(args, "stash_action"):
                    if args.stash_action == "list":
                        stashes = await git_cmds.list_stashes()
                        git_cmds.terminal.display_git_stashes(stashes)
                    elif args.stash_action == "apply":
                        await git_cmds.apply_stash(getattr(args, "stash_index", None))
                    elif args.stash_action == "save":
                        await git_cmds.stash_changes(getattr(args, "message", None))
                else:
                    await git_cmds.stash_changes()

            case "status":
                status = await git_cmds.get_repo_status()
                git_cmds.terminal.display_git_status(status)

            case _:
                git_cmds.terminal.display_error(
                    f"Unknown git action: {args.action}")

    except GitHubCLIError as e:
        git_cmds.terminal.display_error(str(e))
