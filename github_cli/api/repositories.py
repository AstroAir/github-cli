"""
GitHub repository API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
import re
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.models.repository import Repository
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError
from rich.table import Table
from rich import box


class RepositoryAPI:
    """API for working with GitHub repositories"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def list_user_repos(self, username: Optional[str] = None,
                              sort: str = "updated",
                              per_page: int = 30,
                              page: int = 1) -> List[Repository]:
        """List repositories for a user"""
        endpoint = f"users/{username}/repos" if username else "user/repos"
        params = {
            "sort": sort,
            "per_page": per_page,
            "page": page
        }

        response = await self.client.get(endpoint, params=params)
        return [Repository.from_json(repo_data) for repo_data in response]

    async def list_org_repos(self, org: str,
                             type: str = "all",
                             sort: str = "updated",
                             per_page: int = 30,
                             page: int = 1) -> List[Repository]:
        """List repositories for an organization"""
        endpoint = f"orgs/{org}/repos"
        params = {
            "type": type,
            "sort": sort,
            "per_page": per_page,
            "page": page
        }

        response = await self.client.get(endpoint, params=params)
        return [Repository.from_json(repo_data) for repo_data in response]

    async def get_repo(self, repo_name: str) -> Repository:
        """Get a repository by name (format: owner/repo)"""
        if not re.match(r"^[^/]+/[^/]+$", repo_name):
            raise GitHubCLIError(
                f"Invalid repository name format: {repo_name}. Expected format: owner/repo")

        endpoint = f"repos/{repo_name}"

        try:
            response = await self.client.get(endpoint)
            return Repository.from_json(response)
        except NotFoundError:
            raise GitHubCLIError(f"Repository not found: {repo_name}")

    async def create_repo(self, name: str, description: Optional[str] = None,
                          private: bool = False, org: Optional[str] = None,
                          **kwargs) -> Repository:
        """Create a new repository"""
        if org:
            endpoint = f"orgs/{org}/repos"
        else:
            endpoint = "user/repos"

        data = {
            "name": name,
            "private": private,
            **kwargs
        }

        if description:
            data["description"] = description

        response = await self.client.post(endpoint, data=data)
        return Repository.from_json(response)

    async def update_repo(self, repo_name: str, **kwargs) -> Repository:
        """Update a repository"""
        endpoint = f"repos/{repo_name}"
        response = await self.client.patch(endpoint, data=kwargs)
        return Repository.from_json(response)

    async def delete_repo(self, repo_name: str) -> bool:
        """Delete a repository"""
        endpoint = f"repos/{repo_name}"
        await self.client.delete(endpoint)
        return True

    async def list_topics(self, repo_name: str) -> List[str]:
        """List topics for a repository"""
        endpoint = f"repos/{repo_name}/topics"
        headers = {"Accept": "application/vnd.github.mercy-preview+json"}

        response = await self.client.get(endpoint, params={"headers": headers})
        return response.get("names", [])

    async def add_topics(self, repo_name: str, topics: List[str]) -> List[str]:
        """Add topics to a repository"""
        endpoint = f"repos/{repo_name}/topics"
        headers = {"Accept": "application/vnd.github.mercy-preview+json"}

        # First, get current topics
        response = await self.client.get(endpoint, params={"headers": headers})
        current_topics = set(response.get("names", []))

        # Add new topics
        new_topics = list(current_topics.union(set(topics)))

        # Update topics
        data = {"names": new_topics}
        response = await self.client.put(endpoint, data, headers=headers)
        return response.get("names", [])

    async def get_repo_stats(self, repo_name: str) -> Dict[str, Any]:
        """Get repository statistics"""
        stats = {}

        # Get contributors stats
        try:
            stats["contributors"] = await self.client.get(f"repos/{repo_name}/stats/contributors")
        except GitHubCLIError:
            stats["contributors"] = []

        # Get commit activity
        try:
            stats["commit_activity"] = await self.client.get(f"repos/{repo_name}/stats/commit_activity")
        except GitHubCLIError:
            stats["commit_activity"] = []

        # Get code frequency
        try:
            stats["code_frequency"] = await self.client.get(f"repos/{repo_name}/stats/code_frequency")
        except GitHubCLIError:
            stats["code_frequency"] = []

        # Get participation stats
        try:
            stats["participation"] = await self.client.get(f"repos/{repo_name}/stats/participation")
        except GitHubCLIError:
            stats["participation"] = {"all": [], "owner": []}

        return stats


# Handler function for CLI commands
async def handle_repo_command(args: Dict[str, Any], client: GitHubClient, ui: TerminalUI) -> None:
    """Handle repository commands from the CLI"""
    repo_api = RepositoryAPI(client, ui)

    action = args.get("action")

    if action == "list":
        org = args.get("org")
        if org:
            ui.display_info(f"Listing repositories for organization: {org}")
            repos = await repo_api.list_org_repos(org)
        else:
            ui.display_info("Listing your repositories")
            repos = await repo_api.list_user_repos()

        ui.display_repositories(repos)

    elif action == "view":
        repo_name = args.get("name")
        if not repo_name:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        ui.display_info(f"Fetching repository: {repo_name}")
        try:
            repo = await repo_api.get_repo(repo_name)
            _display_repo_details(repo, ui)
        except GitHubCLIError as e:
            ui.display_error(str(e))

    elif action == "create":
        name = args.get("name")
        if not name:
            ui.display_error("Repository name required")
            return

        description = args.get("description", "")
        private = args.get("private", False)
        org = args.get("org")

        try:
            ui.display_info(f"Creating repository: {name}")
            repo = await repo_api.create_repo(
                name=name,
                description=description,
                private=private,
                org=org,
                auto_init=args.get("auto_init", False),
                gitignore_template=args.get("gitignore"),
                license_template=args.get("license")
            )

            ui.display_success(f"Repository created: {repo.full_name}")
            ui.display_info(f"URL: {repo.html_url}")

        except GitHubCLIError as e:
            ui.display_error(f"Failed to create repository: {str(e)}")

    elif action == "delete":
        repo_name = args.get("name")
        if not repo_name:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        # Confirm deletion
        confirmed = ui.confirm(
            f"Are you sure you want to delete {repo_name}", default=False)
        if not confirmed:
            ui.display_info("Deletion cancelled")
            return

        try:
            ui.display_info(f"Deleting repository: {repo_name}")
            await repo_api.delete_repo(repo_name)
            ui.display_success(f"Repository deleted: {repo_name}")
        except GitHubCLIError as e:
            ui.display_error(f"Failed to delete repository: {str(e)}")

    elif action == "topics":
        repo_name = args.get("name")
        if not repo_name:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        topics = args.get("topics")
        if topics:
            # Add topics
            topic_list = topics.split(",")
            try:
                ui.display_info(f"Adding topics to {repo_name}")
                result = await repo_api.add_topics(repo_name, topic_list)
                ui.display_success(f"Topics updated: {', '.join(result)}")
            except GitHubCLIError as e:
                ui.display_error(f"Failed to update topics: {str(e)}")
        else:
            # List topics
            try:
                topics = await repo_api.list_topics(repo_name)
                if topics:
                    ui.display_info(
                        f"Topics for {repo_name}: {', '.join(topics)}")
                else:
                    ui.display_info(f"No topics set for {repo_name}")
            except GitHubCLIError as e:
                ui.display_error(f"Failed to list topics: {str(e)}")

    elif action == "stats":
        repo_name = args.get("name")
        if not repo_name:
            ui.display_error("Repository name required (format: owner/repo)")
            return

        try:
            ui.display_info(f"Fetching statistics for {repo_name}")
            stats = await repo_api.get_repo_stats(repo_name)
            _display_repo_stats(stats, ui)
        except GitHubCLIError as e:
            ui.display_error(f"Failed to get repository statistics: {str(e)}")

    else:
        ui.display_error(f"Unknown repository action: {action}")
        ui.display_info(
            "Available actions: list, view, create, delete, topics, stats")


def _display_repo_details(repo: Repository, ui: TerminalUI) -> None:
    """Display detailed information about a repository"""
    ui.display_heading(f"Repository: {repo.full_name}")

    # Create a table for repo details
    table = Table(box=box.SIMPLE)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Description", repo.description or "No description")
    table.add_row("Visibility", "Private" if repo.private else "Public")
    table.add_row("Default Branch", repo.default_branch)
    table.add_row("Language", repo.language or "Not specified")
    table.add_row("Stars", str(repo.stargazers_count))
    table.add_row("Forks", str(repo.forks_count))
    table.add_row("Open Issues", str(repo.open_issues_count))
    table.add_row("Created", repo.created_date.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Updated", repo.updated_date.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("License", repo.license_name or "No license")
    table.add_row("URL", repo.html_url)

    ui.console.print(table)


def _display_repo_stats(stats: Dict[str, Any], ui: TerminalUI) -> None:
    """Display repository statistics"""
    ui.display_heading("Repository Statistics")

    # Display commit activity
    commit_activity = stats.get("commit_activity", [])
    if commit_activity:
        ui.display_info("Weekly Commit Activity (last year):")
        table = Table(box=box.SIMPLE)
        table.add_column("Week", style="cyan")
        table.add_column("Commits", justify="right")

        # Show the last 12 weeks
        for week in commit_activity[-12:]:
            week_date = datetime.fromtimestamp(
                week["week"]).strftime("%Y-%m-%d")
            table.add_row(week_date, str(week["total"]))

        ui.console.print(table)

    # Display participation stats
    participation = stats.get("participation", {})
    if participation and participation.get("all"):
        ui.display_info("Participation (last 52 weeks):")
        ui.display_info(f"Total commits: {sum(participation['all'])}")
        ui.display_info(f"Owner commits: {sum(participation['owner'])}")

    # Display top contributors
    contributors = stats.get("contributors", [])
    if contributors:
        ui.display_info("Top Contributors:")
        table = Table(box=box.SIMPLE)
        table.add_column("Username", style="cyan")
        table.add_column("Commits", justify="right")
        table.add_column("Additions", justify="right", style="green")
        table.add_column("Deletions", justify="right", style="red")

        # Sort by total commits
        contributors.sort(key=lambda c: c["total"], reverse=True)

        # Show top 10 contributors
        for contributor in contributors[:10]:
            username = contributor["author"]["login"]
            total_commits = contributor["total"]

            # Calculate total additions and deletions
            additions = sum(week["a"] for week in contributor["weeks"])
            deletions = sum(week["d"] for week in contributor["weeks"])

            table.add_row(username, str(total_commits),
                          str(additions), str(deletions))

        ui.console.print(table)
