"""
GitHub Statistics API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError


class StatisticsAPI:
    """API for working with GitHub Statistics"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def get_repo_statistics(self, repo: str) -> Dict[str, Any]:
        """Get comprehensive repository statistics"""
        try:
            # Get basic repo info
            repo_info = await self.client.get(f"repos/{repo}")

            # Get contributors
            contributors = await self.client.get(f"repos/{repo}/contributors")

            # Get commit activity
            commit_activity = await self.client.get(f"repos/{repo}/stats/commit_activity")

            # Get code frequency
            code_frequency = await self.client.get(f"repos/{repo}/stats/code_frequency")

            # Get participation
            participation = await self.client.get(f"repos/{repo}/stats/participation")

            # Get languages
            languages = await self.client.get(f"repos/{repo}/languages")

            return {
                "repository": repo_info,
                "contributors": contributors,
                "commit_activity": commit_activity,
                "code_frequency": code_frequency,
                "participation": participation,
                "languages": languages
            }
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to get repository statistics: {str(e)}")

    async def get_contributor_stats(self, repo: str) -> List[Dict[str, Any]]:
        """Get contributor statistics for a repository"""
        try:
            response = await self.client.get(f"repos/{repo}/stats/contributors")
            return response
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to get contributor statistics: {str(e)}")

    async def get_commit_activity(self, repo: str) -> List[Dict[str, Any]]:
        """Get weekly commit activity for a repository"""
        try:
            response = await self.client.get(f"repos/{repo}/stats/commit_activity")
            return response
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get commit activity: {str(e)}")

    async def get_code_frequency(self, repo: str) -> List[List[int]]:
        """Get weekly code frequency for a repository"""
        try:
            response = await self.client.get(f"repos/{repo}/stats/code_frequency")
            return response
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get code frequency: {str(e)}")

    async def get_punch_card(self, repo: str) -> List[List[int]]:
        """Get punch card data for a repository"""
        try:
            response = await self.client.get(f"repos/{repo}/stats/punch_card")
            return response
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get punch card data: {str(e)}")

    async def get_traffic_stats(self, repo: str) -> Dict[str, Any]:
        """Get traffic statistics for a repository"""
        try:
            # Get referrers
            referrers = await self.client.get(f"repos/{repo}/traffic/popular/referrers")

            # Get paths
            paths = await self.client.get(f"repos/{repo}/traffic/popular/paths")

            # Get views
            views = await self.client.get(f"repos/{repo}/traffic/views")

            # Get clones
            clones = await self.client.get(f"repos/{repo}/traffic/clones")

            return {
                "referrers": referrers,
                "paths": paths,
                "views": views,
                "clones": clones
            }
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get traffic statistics: {str(e)}")

    async def get_user_statistics(self, username: str) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Get user info
            user_info = await self.client.get(f"users/{username}")

            # Get user repos
            repos = await self.client.get(f"users/{username}/repos", params={"per_page": 100})

            # Calculate stats
            total_stars = sum(repo.get("stargazers_count", 0)
                              for repo in repos)
            total_forks = sum(repo.get("forks_count", 0) for repo in repos)
            total_watchers = sum(repo.get("watchers_count", 0)
                                 for repo in repos)

            languages = {}
            for repo in repos:
                if repo.get("language"):
                    lang = repo["language"]
                    languages[lang] = languages.get(lang, 0) + 1

            return {
                "user": user_info,
                "repositories": repos,
                "summary": {
                    "total_repos": len(repos),
                    "total_stars": total_stars,
                    "total_forks": total_forks,
                    "total_watchers": total_watchers,
                    "languages": languages
                }
            }
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get user statistics: {str(e)}")

    async def get_organization_statistics(self, org: str) -> Dict[str, Any]:
        """Get organization statistics"""
        try:
            # Get org info
            org_info = await self.client.get(f"orgs/{org}")

            # Get org repos
            repos = await self.client.get(f"orgs/{org}/repos", params={"per_page": 100})

            # Get org members
            members = await self.client.get(f"orgs/{org}/members")

            # Calculate stats
            total_stars = sum(repo.get("stargazers_count", 0)
                              for repo in repos)
            total_forks = sum(repo.get("forks_count", 0) for repo in repos)

            languages = {}
            for repo in repos:
                if repo.get("language"):
                    lang = repo["language"]
                    languages[lang] = languages.get(lang, 0) + 1

            return {
                "organization": org_info,
                "repositories": repos,
                "members": members,
                "summary": {
                    "total_repos": len(repos),
                    "total_members": len(members),
                    "total_stars": total_stars,
                    "total_forks": total_forks,
                    "languages": languages
                }
            }
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to get organization statistics: {str(e)}")


class StatisticsCommands:
    """High-level statistics commands"""

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.api = StatisticsAPI(client, terminal)

    async def show_repo_stats(self, repo: str) -> None:
        """Show repository statistics"""
        try:
            stats = await self.api.get_repo_statistics(repo)
            self.terminal.display_repo_statistics(stats)
        except GitHubCLIError as e:
            self.terminal.display_error(
                f"Failed to get repository statistics: {e}")

    async def show_contributor_stats(self, repo: str) -> None:
        """Show contributor statistics"""
        try:
            contributors = await self.api.get_contributor_stats(repo)
            self.terminal.display_contributor_statistics(contributors)
        except GitHubCLIError as e:
            self.terminal.display_error(
                f"Failed to get contributor statistics: {e}")

    async def show_traffic_stats(self, repo: str) -> None:
        """Show traffic statistics"""
        try:
            traffic = await self.api.get_traffic_stats(repo)
            self.terminal.display_traffic_statistics(traffic)
        except GitHubCLIError as e:
            self.terminal.display_error(
                f"Failed to get traffic statistics: {e}")

    async def show_user_stats(self, username: str) -> None:
        """Show user statistics"""
        try:
            stats = await self.api.get_user_statistics(username)
            self.terminal.display_user_statistics(stats)
        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to get user statistics: {e}")

    async def show_org_stats(self, org: str) -> None:
        """Show organization statistics"""
        try:
            stats = await self.api.get_organization_statistics(org)
            self.terminal.display_organization_statistics(stats)
        except GitHubCLIError as e:
            self.terminal.display_error(
                f"Failed to get organization statistics: {e}")


async def handle_stats_command(args, stats_cmds: StatisticsCommands):
    """Handle statistics command dispatch"""
    try:
        match args.type:
            case "commits":
                if not args.repo:
                    stats_cmds.terminal.display_error(
                        "Repository required for commit statistics")
                    return
                await stats_cmds.show_contributor_stats(args.repo)

            case "contributors":
                if not args.repo:
                    stats_cmds.terminal.display_error(
                        "Repository required for contributor statistics")
                    return
                await stats_cmds.show_contributor_stats(args.repo)

            case "traffic":
                if not args.repo:
                    stats_cmds.terminal.display_error(
                        "Repository required for traffic statistics")
                    return
                await stats_cmds.show_traffic_stats(args.repo)

            case "community":
                if args.repo:
                    await stats_cmds.show_repo_stats(args.repo)
                else:
                    stats_cmds.terminal.display_error(
                        "Repository required for community statistics")

            case "insights":
                if args.repo:
                    await stats_cmds.show_repo_stats(args.repo)
                else:
                    stats_cmds.terminal.display_error(
                        "Repository required for insights")

            case _:
                stats_cmds.terminal.display_error(
                    f"Unknown statistics type: {args.type}")

    except GitHubCLIError as e:
        stats_cmds.terminal.display_error(str(e))


# Add display methods to TerminalUI
def _add_statistics_methods_to_terminal():
    """Add statistics display methods to TerminalUI class"""
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn
    from rich import box

    def display_repo_statistics(self, stats: Dict[str, Any]) -> None:
        """Display repository statistics"""
        repo = stats["repository"]
        contributors = stats.get("contributors", [])
        languages = stats.get("languages", {})

        # Repository overview
        header = f"Repository: {repo['full_name']}"

        panel_content = []
        panel_content.append(f"Stars: {repo.get('stargazers_count', 0)}")
        panel_content.append(f"Forks: {repo.get('forks_count', 0)}")
        panel_content.append(f"Watchers: {repo.get('watchers_count', 0)}")
        panel_content.append(f"Issues: {repo.get('open_issues_count', 0)}")
        panel_content.append(f"Size: {repo.get('size', 0)} KB")
        panel_content.append(
            f"Created: {repo.get('created_at', '').split('T')[0]}")
        panel_content.append(
            f"Updated: {repo.get('updated_at', '').split('T')[0]}")

        self.console.print(Panel("\n".join(panel_content),
                           title=header, box=box.ROUNDED))

        # Top contributors
        if contributors:
            table = Table(title="Top Contributors", box=box.ROUNDED)
            table.add_column("User", style="cyan")
            table.add_column("Contributions", style="yellow")

            for contrib in contributors[:10]:  # Top 10
                table.add_row(
                    contrib["login"],
                    str(contrib["contributions"])
                )

            self.console.print(table)

        # Languages
        if languages:
            self.console.print("\n[bold]Languages:[/bold]")
            total_bytes = sum(languages.values())

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
                expand=True
            ) as progress:
                for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                    percentage = (bytes_count / total_bytes) * 100
                    progress.add_task(
                        f"{lang:.<20}", completed=percentage, total=100)

    def display_contributor_statistics(self, contributors: List[Dict[str, Any]]) -> None:
        """Display contributor statistics"""
        if not contributors:
            self.display_info("No contributor statistics available")
            return

        table = Table(title="Contributor Statistics", box=box.ROUNDED)
        table.add_column("User", style="cyan")
        table.add_column("Total Commits", style="yellow")
        table.add_column("Additions", style="green")
        table.add_column("Deletions", style="red")

        for contrib in contributors:
            total_commits = contrib.get("total", 0)
            total_additions = sum(week.get("a", 0)
                                  for week in contrib.get("weeks", []))
            total_deletions = sum(week.get("d", 0)
                                  for week in contrib.get("weeks", []))

            table.add_row(
                contrib["author"]["login"],
                str(total_commits),
                str(total_additions),
                str(total_deletions)
            )

        self.console.print(table)

    def display_traffic_statistics(self, traffic: Dict[str, Any]) -> None:
        """Display traffic statistics"""
        views = traffic.get("views", {})
        clones = traffic.get("clones", {})
        referrers = traffic.get("referrers", [])

        # Views and clones summary
        panel_content = []
        if views:
            panel_content.append(f"Total Views: {views.get('count', 0)}")
            panel_content.append(f"Unique Visitors: {views.get('uniques', 0)}")

        if clones:
            panel_content.append(f"Total Clones: {clones.get('count', 0)}")
            panel_content.append(f"Unique Cloners: {clones.get('uniques', 0)}")

        if panel_content:
            self.console.print(
                Panel("\n".join(panel_content), title="Traffic Summary", box=box.ROUNDED))

        # Top referrers
        if referrers:
            table = Table(title="Top Referrers", box=box.ROUNDED)
            table.add_column("Referrer", style="cyan")
            table.add_column("Views", style="yellow")
            table.add_column("Unique Visitors", style="green")

            for referrer in referrers[:10]:  # Top 10
                table.add_row(
                    referrer.get("referrer", "Direct"),
                    str(referrer.get("count", 0)),
                    str(referrer.get("uniques", 0))
                )

            self.console.print(table)

    def display_user_statistics(self, stats: Dict[str, Any]) -> None:
        """Display user statistics"""
        user = stats["user"]
        summary = stats["summary"]

        # User overview
        header = f"User: {user['login']}"

        panel_content = []
        panel_content.append(f"Name: {user.get('name', 'N/A')}")
        panel_content.append(f"Company: {user.get('company', 'N/A')}")
        panel_content.append(f"Location: {user.get('location', 'N/A')}")
        panel_content.append(f"Public Repos: {summary['total_repos']}")
        panel_content.append(f"Total Stars: {summary['total_stars']}")
        panel_content.append(f"Total Forks: {summary['total_forks']}")
        panel_content.append(f"Followers: {user.get('followers', 0)}")
        panel_content.append(f"Following: {user.get('following', 0)}")

        self.console.print(Panel("\n".join(panel_content),
                           title=header, box=box.ROUNDED))

        # Languages
        languages = summary.get("languages", {})
        if languages:
            table = Table(title="Languages Used", box=box.ROUNDED)
            table.add_column("Language", style="cyan")
            table.add_column("Repositories", style="yellow")

            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                table.add_row(lang, str(count))

            self.console.print(table)

    def display_organization_statistics(self, stats: Dict[str, Any]) -> None:
        """Display organization statistics"""
        org = stats["organization"]
        summary = stats["summary"]

        # Organization overview
        header = f"Organization: {org['login']}"

        panel_content = []
        panel_content.append(f"Name: {org.get('name', 'N/A')}")
        panel_content.append(f"Description: {org.get('description', 'N/A')}")
        panel_content.append(f"Location: {org.get('location', 'N/A')}")
        panel_content.append(f"Public Repos: {summary['total_repos']}")
        panel_content.append(f"Members: {summary['total_members']}")
        panel_content.append(f"Total Stars: {summary['total_stars']}")
        panel_content.append(f"Total Forks: {summary['total_forks']}")

        self.console.print(Panel("\n".join(panel_content),
                           title=header, box=box.ROUNDED))

    # Add methods to TerminalUI class
    TerminalUI.display_repo_statistics = display_repo_statistics
    TerminalUI.display_contributor_statistics = display_contributor_statistics
    TerminalUI.display_traffic_statistics = display_traffic_statistics
    TerminalUI.display_user_statistics = display_user_statistics
    TerminalUI.display_organization_statistics = display_organization_statistics


# Initialize the methods
_add_statistics_methods_to_terminal()
