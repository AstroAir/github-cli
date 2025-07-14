#!/usr/bin/env python3
"""
GitHub CLI - An advanced terminal-based GitHub client
"""

import asyncio
import argparse
import sys
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from github_cli.auth.authenticator import Authenticator
from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.ui.dashboard import Dashboard
from github_cli.utils.exceptions import GitHubCLIError, AuthenticationError
from github_cli.utils.config import Config
from github_cli.utils.plugins import PluginManager
from github_cli.utils.cache import CacheManager
from github_cli.utils.shortcuts import ShortcutsManager


async def main() -> int:
    """Main entry point for the GitHub CLI"""

    parser = argparse.ArgumentParser(
        description="Advanced terminal-based GitHub client")

    # Define subcommands
    subparsers = parser.add_subparsers(
        dest="command", help="Command to execute")

    # Auth commands with enhanced options
    auth_parser = subparsers.add_parser("auth", help="Authentication commands")
    auth_parser.add_argument("action", choices=["login", "logout", "status", "token", "scopes"],
                             help="Authentication action")
    auth_parser.add_argument(
        "--scopes", help="Custom OAuth scopes (comma separated)")
    auth_parser.add_argument("--sso", help="Single sign-on identifier")

    # Repo commands with enhanced options
    repo_parser = subparsers.add_parser("repo", help="Repository commands")
    repo_parser.add_argument("action", choices=["list", "view", "create", "clone", "fork",
                                                "delete", "topics", "transfer", "stats"],
                             help="Repository action")
    repo_parser.add_argument("--name", help="Repository name (owner/repo)")
    repo_parser.add_argument(
        "--template", help="Template repository for creation")
    repo_parser.add_argument(
        "--private", action="store_true", help="Create as private repository")
    repo_parser.add_argument("--branch", help="Specific branch to operate on")

    # Issue commands with enhanced options
    issue_parser = subparsers.add_parser("issue", help="Issue commands")
    issue_parser.add_argument("action",
                              choices=["list", "view", "create", "edit", "close", "reopen",
                                       "comment", "assign", "label", "milestone", "subscribe"],
                              help="Issue action")
    issue_parser.add_argument("--repo", help="Repository name (owner/repo)")
    issue_parser.add_argument("--number", type=int, help="Issue number")
    issue_parser.add_argument("--format", choices=["table", "json", "md"], default="table",
                              help="Output format")
    issue_parser.add_argument(
        "--template", help="Template file for issue creation")
    issue_parser.add_argument(
        "--batch", help="Batch operations from JSON file")

    # PR commands with enhanced options
    pr_parser = subparsers.add_parser("pr", help="Pull request commands")
    pr_parser.add_argument("action",
                           choices=["list", "view", "create", "edit", "merge", "close", "reopen",
                                    "diff", "checks", "review", "ready", "comment", "sync"],
                           help="PR action")
    pr_parser.add_argument("--repo", help="Repository name (owner/repo)")
    pr_parser.add_argument("--number", type=int, help="PR number")
    pr_parser.add_argument("--base", help="Base branch for PR")
    pr_parser.add_argument("--head", help="Head branch for PR")
    pr_parser.add_argument("--merge-strategy",
                           choices=["merge", "squash", "rebase"],
                           help="Strategy for merging PRs")

    # New Gist commands
    gist_parser = subparsers.add_parser("gist", help="Gist commands")
    gist_parser.add_argument("action", choices=["list", "view", "create", "edit", "delete", "clone"],
                             help="Gist action")
    gist_parser.add_argument("--id", help="Gist ID")
    gist_parser.add_argument(
        "--file", help="File path for gist creation/editing")
    gist_parser.add_argument(
        "--public", action="store_true", help="Create as public gist")

    # New Actions workflows commands
    actions_parser = subparsers.add_parser(
        "actions", help="GitHub Actions commands")
    actions_parser.add_argument("action",
                                choices=["list", "view", "run",
                                         "logs", "cancel", "secrets"],
                                help="Actions action")
    actions_parser.add_argument("--repo", help="Repository name (owner/repo)")
    actions_parser.add_argument("--workflow", help="Workflow name or ID")
    actions_parser.add_argument("--run-id", type=int, help="Workflow run ID")

    # New Projects commands
    project_parser = subparsers.add_parser("project", help="Project commands")
    project_parser.add_argument("action", choices=["list", "view", "create", "edit", "delete", "cards"],
                                help="Project action")
    project_parser.add_argument("--repo", help="Repository name (owner/repo)")
    project_parser.add_argument("--number", type=int, help="Project number")

    # New Releases commands
    release_parser = subparsers.add_parser("release", help="Release commands")
    release_parser.add_argument("action", choices=["list", "view", "create", "edit", "delete", "assets"],
                                help="Release action")
    release_parser.add_argument("--repo", help="Repository name (owner/repo)")
    release_parser.add_argument("--tag", help="Release tag")
    release_parser.add_argument(
        "--draft", action="store_true", help="Create as draft release")
    release_parser.add_argument(
        "--prerelease", action="store_true", help="Mark as pre-release")

    # Enhanced Search commands
    search_parser = subparsers.add_parser("search", help="Search commands")
    search_parser.add_argument("target",
                               choices=["code", "repos", "issues",
                                        "prs", "users", "topics", "labels"],
                               help="Search target")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--language", help="Filter by language")
    search_parser.add_argument("--sort", help="Sort field")
    search_parser.add_argument(
        "--order", choices=["asc", "desc"], help="Sort order")
    search_parser.add_argument("--limit", type=int, help="Limit results")

    # Git commands
    git_parser = subparsers.add_parser("git", help="Git operations")
    git_parser.add_argument("action",
                            choices=["branch", "checkout", "stash",
                                     "rebase", "merge", "hooks"],
                            help="Git action")

    # Notifications commands
    notif_parser = subparsers.add_parser(
        "notify", help="Notification commands")
    notif_parser.add_argument("action", choices=["list", "watch", "read", "subscribe", "ignore"],
                              help="Notification action")

    # Stats and analysis commands
    stats_parser = subparsers.add_parser("stats", help="Statistics commands")
    stats_parser.add_argument("type",
                              choices=["commits", "contributors",
                                       "traffic", "community", "insights"],
                              help="Stats type")
    stats_parser.add_argument("--repo", help="Repository name (owner/repo)")
    stats_parser.add_argument("--format", choices=["table", "json", "chart"], default="table",
                              help="Output format")

    # Config commands
    config_parser = subparsers.add_parser(
        "config", help="Configuration commands")
    config_parser.add_argument("action", choices=["get", "set", "list", "reset", "shortcuts", "themes"],
                               help="Configuration action")
    config_parser.add_argument("--key", help="Configuration key")
    config_parser.add_argument("--value", help="Configuration value")

    # Interactive mode with enhancements
    parser.add_argument("--interactive", "-i",
                        action="store_true", help="Start in interactive mode")
    parser.add_argument("--dashboard", "-d", action="store_true",
                        help="Start with dashboard view")
    parser.add_argument("--theme", help="UI theme to use")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    parser.add_argument(
        "--cache", choices=["use", "refresh", "ignore"], help="Cache behavior")
    parser.add_argument("--version", "-v", action="store_true",
                        help="Show version and exit")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Show version and exit if requested
    if args.version:
        from github_cli import __version__
        print(f"GitHub CLI v{__version__}")
        return 0

    # Load config
    config = Config()

    # Initialize cache manager
    cache_manager = CacheManager(config, mode=args.cache or "use")

    # Initialize shortcuts manager
    shortcuts_manager = ShortcutsManager(config)

    # Initialize plugin manager
    plugin_manager = PluginManager(config)

    try:
        # Initialize authenticator with enhanced features
        authenticator = Authenticator(config)

        # If no command is provided, determine default mode
        if not args.command and not args.interactive and not args.dashboard:
            # Default to dashboard if authenticated, otherwise interactive mode
            if authenticator.is_authenticated():
                args.dashboard = True
            else:
                args.interactive = True

        # For commands requiring authentication, ensure the user is authenticated
        if args.command not in ["auth", "config"] or \
           (args.command == "auth" and args.action not in ["login", "status"]):
            if not authenticator.is_authenticated():
                print("You need to login first. Run 'github-cli auth login'")
                return 1

        # Initialize the API client with enhanced features
        client = GitHubClient(authenticator)
        # Cache manager will be passed directly to command handlers that need it

        # Initialize the terminal UI
        terminal = TerminalUI(client)
        # Set theme if needed
        terminal.theme = args.theme or config.get("ui.theme", "auto")

        # Load plugins
        if config.get("plugins.enabled", True):
            plugin_manager.load_plugins()

        # Process specific commands
        if args.dashboard:
            # Run dashboard mode
            dashboard = Dashboard(client, terminal)
            await dashboard.run()
            return 0

        if args.interactive:
            # Run enhanced interactive mode
            await terminal.start_interactive_mode(shortcuts_manager)
            return 0

        # Process commands using advanced pattern matching
        match args.command:
            case "auth":
                await handle_auth_command(args, authenticator, terminal)

            case "repo":
                from github_cli.api.commands import RepositoryCommands
                repo_cmds = RepositoryCommands(client, terminal)
                await handle_repo_command(args, repo_cmds)

            case "issue":
                from github_cli.api.commands import IssueCommands
                issue_cmds = IssueCommands(client, terminal)
                await handle_issue_command(args, issue_cmds)

            case "pr":
                from github_cli.api.commands import PullRequestCommands
                pr_cmds = PullRequestCommands(client, terminal)
                await handle_pr_command(args, pr_cmds)

            case "gist":
                from github_cli.api.commands import GistCommands
                gist_cmds = GistCommands(client, terminal)
                await handle_gist_command(args, gist_cmds)

            case "actions":
                from github_cli.api.commands import ActionsCommands
                actions_cmds = ActionsCommands(client, terminal)
                await handle_actions_command(args, actions_cmds)

            case "project":
                from github_cli.api.commands import ProjectCommands
                project_cmds = ProjectCommands(client, terminal)
                await handle_project_command(args, project_cmds)

            case "release":
                from github_cli.api.commands import ReleaseCommands
                release_cmds = ReleaseCommands(client, terminal)
                await handle_release_command(args, release_cmds)

            case "search":
                from github_cli.api.commands import SearchCommands
                search_cmds = SearchCommands(client, terminal)
                await handle_search_command(args, search_cmds)

            case "git":
                from github_cli.api.commands import GitCommands
                git_cmds = GitCommands(client, terminal)
                await handle_git_command(args, git_cmds)

            case "notify":
                from github_cli.api.commands import NotificationCommands
                notif_cmds = NotificationCommands(client, terminal)
                await handle_notification_command(args, notif_cmds)

            case "stats":
                from github_cli.api.commands import StatisticsCommands
                stats_cmds = StatisticsCommands(client, terminal)
                await handle_stats_command(args, stats_cmds)

            case "config":
                await handle_config_command(args, config, terminal, shortcuts_manager)

            case _:
                terminal.display_error(f"Unknown command: {args.command}")
                return 1

        return 0

    except AuthenticationError as e:
        print(f"Authentication error: {e}")
        return 1
    except GitHubCLIError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        return 130
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        print(f"Unexpected error: {e}")
        return 1


# Command handler implementations

async def handle_auth_command(args, authenticator, terminal):
    """Handle authentication commands"""
    match args.action:
        case "login":
            await authenticator.login_interactive(scopes=args.scopes, sso=args.sso)
        case "logout":
            authenticator.logout()
            terminal.display_success("Successfully logged out")
        case "status":
            await authenticator.show_status(terminal)
        case "token":
            authenticator.manage_tokens(terminal)
        case "scopes":
            await authenticator.show_scopes(terminal)

async def handle_repo_command(args, repo_cmds):
    """Handle repository commands"""
    match args.action:
        case "list":
            await repo_cmds.list_repositories()
        case "view":
            await repo_cmds.view_repository(args.name)
        case "create":
            await repo_cmds.create_repository(args)
        case "clone":
            await repo_cmds.clone_repository(args.name)
        case "fork":
            await repo_cmds.fork_repository(args.name)
        case "delete":
            await repo_cmds.delete_repository(args.name)
        case "topics":
            await repo_cmds.manage_topics(args.name)
        case "transfer":
            await repo_cmds.transfer_repository(args.name)
        case "stats":
            await repo_cmds.show_repository_stats(args.name)

async def handle_issue_command(args, issue_cmds):
    """Handle issue commands"""
    match args.action:
        case "list":
            await issue_cmds.list_issues(args.repo)
        case "view":
            await issue_cmds.view_issue(args.repo, args.number)
        case "create":
            await issue_cmds.create_issue(args.repo, args.template)
        case "edit":
            await issue_cmds.edit_issue(args.repo, args.number)
        case "close":
            await issue_cmds.close_issue(args.repo, args.number)
        case "reopen":
            await issue_cmds.reopen_issue(args.repo, args.number)
        case "comment":
            await issue_cmds.comment_on_issue(args.repo, args.number)
        case "assign":
            await issue_cmds.assign_issue(args.repo, args.number)
        case "label":
            await issue_cmds.label_issue(args.repo, args.number)
        case "milestone":
            await issue_cmds.set_milestone(args.repo, args.number)
        case "subscribe":
            await issue_cmds.subscribe_to_issue(args.repo, args.number)

async def handle_pr_command(args, pr_cmds):
    """Handle pull request commands"""
    match args.action:
        case "list":
            await pr_cmds.list_pull_requests(args.repo)
        case "view":
            await pr_cmds.view_pull_request(args.repo, args.number)
        case "create":
            await pr_cmds.create_pull_request(args.repo, args.base, args.head)
        case "edit":
            await pr_cmds.edit_pull_request(args.repo, args.number)
        case "merge":
            await pr_cmds.merge_pull_request(args.repo, args.number, args.merge_strategy)
        case "close":
            await pr_cmds.close_pull_request(args.repo, args.number)
        case "reopen":
            await pr_cmds.reopen_pull_request(args.repo, args.number)
        case "diff":
            await pr_cmds.show_diff(args.repo, args.number)
        case "checks":
            await pr_cmds.show_checks(args.repo, args.number)
        case "review":
            await pr_cmds.review_pull_request(args.repo, args.number)
        case "ready":
            await pr_cmds.mark_ready(args.repo, args.number)
        case "comment":
            await pr_cmds.comment_on_pr(args.repo, args.number)
        case "sync":
            await pr_cmds.sync_pull_request(args.repo, args.number)

async def handle_gist_command(args, gist_cmds):
    """Handle gist commands"""
    match args.action:
        case "list":
            await gist_cmds.list_gists()
        case "view":
            await gist_cmds.view_gist(args.id)
        case "create":
            await gist_cmds.create_gist(args.file, args.public)
        case "edit":
            await gist_cmds.edit_gist(args.id, args.file)
        case "delete":
            await gist_cmds.delete_gist(args.id)
        case "clone":
            await gist_cmds.clone_gist(args.id)

async def handle_actions_command(args, actions_cmds):
    """Handle GitHub Actions commands"""
    match args.action:
        case "list":
            await actions_cmds.list_workflows(args.repo)
        case "view":
            await actions_cmds.view_workflow(args.repo, args.workflow)
        case "run":
            await actions_cmds.run_workflow(args.repo, args.workflow)
        case "logs":
            await actions_cmds.get_logs(args.repo, args.run_id)
        case "cancel":
            await actions_cmds.cancel_workflow(args.repo, args.run_id)
        case "secrets":
            await actions_cmds.manage_secrets(args.repo)

async def handle_project_command(args, project_cmds):
    """Handle project commands"""
    match args.action:
        case "list":
            await project_cmds.list_projects(args.repo)
        case "view":
            await project_cmds.view_project(args.repo, args.number)
        case "create":
            await project_cmds.create_project(args.repo)
        case "edit":
            await project_cmds.edit_project(args.repo, args.number)
        case "delete":
            await project_cmds.delete_project(args.repo, args.number)
        case "cards":
            await project_cmds.manage_cards(args.repo, args.number)

async def handle_release_command(args, release_cmds):
    """Handle release commands"""
    match args.action:
        case "list":
            await release_cmds.list_releases(args.repo)
        case "view":
            await release_cmds.view_release(args.repo, args.tag)
        case "create":
            await release_cmds.create_release(args.repo, args.tag, args.draft, args.prerelease)
        case "edit":
            await release_cmds.edit_release(args.repo, args.tag)
        case "delete":
            await release_cmds.delete_release(args.repo, args.tag)
        case "assets":
            await release_cmds.manage_assets(args.repo, args.tag)

async def handle_search_command(args, search_cmds):
    """Handle search commands"""
    await search_cmds.search(args.target, args.query, args.language, 
                            args.sort, args.order, args.limit)

async def handle_git_command(args, git_cmds):
    """Handle Git commands"""
    match args.action:
        case "branch":
            await git_cmds.manage_branches()
        case "checkout":
            await git_cmds.checkout()
        case "stash":
            await git_cmds.manage_stashes()
        case "rebase":
            await git_cmds.rebase()
        case "merge":
            await git_cmds.merge()
        case "hooks":
            await git_cmds.manage_hooks()

async def handle_notification_command(args, notif_cmds):
    """Handle notification commands"""
    match args.action:
        case "list":
            await notif_cmds.list_notifications()
        case "watch":
            await notif_cmds.watch_notifications()
        case "read":
            await notif_cmds.mark_as_read()
        case "subscribe":
            await notif_cmds.subscribe()
        case "ignore":
            await notif_cmds.ignore()

async def handle_stats_command(args, stats_cmds):
    """Handle statistics commands"""
    await stats_cmds.show_stats(args.type, args.repo, args.format)

async def handle_config_command(args, config, terminal, shortcuts_manager):
    """Handle config commands"""
    match args.action:
        case "get":
            value = config.get(args.key)
            terminal.display_info(f"{args.key}: {value}")
        case "set":
            config.set(args.key, args.value)
            terminal.display_success(f"Set {args.key} to {args.value}")
        case "list":
            config_values = config.get_all()
            terminal.display_dict(config_values, "Configuration")
        case "reset":
            config.reset()
            terminal.display_success("Configuration reset to defaults")
        case "shortcuts":
            shortcuts = shortcuts_manager.get_all_shortcuts()
            terminal.display_dict(shortcuts, "Keyboard Shortcuts")
        case "themes":
            themes = config.get("ui.available_themes", [])
            terminal.display_list(themes, "Available Themes")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
