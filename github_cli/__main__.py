from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Any, NoReturn

from loguru import logger
from rich.console import Console
from rich.traceback import install as install_rich_tracebacks
# Import RichHelpFormatter from rich_argparse
from rich_argparse import RichHelpFormatter

from github_cli.auth.authenticator import Authenticator
from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.ui.dashboard import Dashboard
# Removed unused GitHubCLIError
from github_cli.utils.exceptions import AuthenticationError
from github_cli.utils.config import Config

# Configure rich tracebacks for better error display
install_rich_tracebacks(show_locals=True)
console = Console()

# Configure loguru for structured logging
logger.remove()  # Remove default handler
logger.add(
    "logs/github_cli.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    rotation="10 MB",
    retention="1 week",
    level="DEBUG",
    enqueue=True  # Thread-safe logging
)
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@asynccontextmanager
async def application_context():
    """Application context manager for resource management."""
    config = Config()
    authenticator = Authenticator(config)

    logger.info("Initializing GitHub CLI application")

    async with GitHubClient(authenticator) as client:
        ui = TerminalUI(client)
        try:
            yield config, authenticator, client, ui
        finally:
            logger.info("Shutting down GitHub CLI application")


async def main() -> int:
    """Modern main entry point with enhanced error handling and performance."""

    try:
        # Import argparse here for faster startup when not needed
        import argparse

        parser = argparse.ArgumentParser(
            description="Advanced terminal-based GitHub client",
            # Use RichHelpFormatter from rich_argparse if available
            formatter_class=RichHelpFormatter if hasattr(
                argparse, 'ArgumentParser') and 'RichHelpFormatter' in globals() else argparse.HelpFormatter
        )

        # Define subcommands with modern Python patterns
        subparsers = parser.add_subparsers(
            dest="command",
            help="Command to execute",
            required=False
        )

        # Auth commands
        _setup_auth_parser(subparsers)  # Removed unused assignment

        # Repo commands
        _setup_repo_parser(subparsers)  # Removed unused assignment

        # PR commands
        _setup_pr_parser(subparsers)  # Removed unused assignment

        # Actions commands
        _setup_actions_parser(subparsers)  # Removed unused assignment

        # Notifications commands
        _setup_notifications_parser(subparsers)  # Removed unused assignment

        # User commands
        _setup_user_parser(subparsers)  # Removed unused assignment

        # Organization commands
        _setup_org_parser(subparsers)  # Removed unused assignment

        # Search commands
        _setup_search_parser(subparsers)  # Removed unused assignment

        # Release commands
        _setup_release_parser(subparsers)  # Removed unused assignment

        # Dashboard command
        subparsers.add_parser(  # Removed unused assignment
            "dashboard",
            help="Open interactive dashboard"
        )

        # Global options
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging"
        )
        parser.add_argument(
            "--version",
            action="version",
            version="GitHub CLI 0.1.0"
        )
        parser.add_argument(
            "--tui",
            action="store_true",
            help="Launch TUI (Terminal User Interface)"
        )

        # Parse arguments
        args = parser.parse_args()

        # Configure logging level based on debug flag
        if args.debug:
            logger.remove()
            logger.add(
                sys.stderr,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level="DEBUG"
            )

        logger.debug(f"Parsed arguments: {args}")

        # Handle TUI mode
        if args.tui:
            logger.info("Launching TUI mode")
            from github_cli.ui.tui.core.app import run_tui
            import asyncio
            import threading

            # Run TUI in a separate thread since it needs its own event loop
            def run_tui_in_thread():
                run_tui()

            # Start TUI in a separate thread
            tui_thread = threading.Thread(target=run_tui_in_thread)
            tui_thread.start()
            tui_thread.join()
            return 0

        # Handle no command case
        if not args.command:
            # Try to determine best default action
            async with application_context() as (config, authenticator, client, ui):
                if authenticator.is_authenticated():
                    logger.info("No command specified, launching dashboard")
                    dashboard = Dashboard(client, ui)
                    await dashboard.start()
                else:
                    logger.info(
                        "No command specified and not authenticated, showing help")
                    parser.print_help()
            return 0

        # Handle commands with application context
        async with application_context() as (config, authenticator, client, ui):
            # Removed config from _handle_command call
            return await _handle_command(args, authenticator, client, ui)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        logger.info("Operation cancelled by user")
        return 130

    except Exception as e:
        logger.exception("Unhandled exception in main")
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


def _setup_auth_parser(subparsers) -> Any:
    """Setup authentication command parser."""
    auth_parser = subparsers.add_parser("auth", help="Authentication commands")
    auth_parser.add_argument(
        "action",
        choices=["login", "logout", "status", "token", "scopes"],
        help="Authentication action"
    )
    auth_parser.add_argument(
        "--scopes",
        help="Custom OAuth scopes (comma separated)"
    )
    auth_parser.add_argument(
        "--sso",
        help="Single sign-on identifier"
    )
    return auth_parser


def _setup_repo_parser(subparsers) -> Any:
    """Setup repository command parser."""
    repo_parser = subparsers.add_parser("repo", help="Repository commands")
    repo_parser.add_argument(
        "action",
        choices=["list", "view", "create", "clone", "fork",
                 "delete", "topics", "transfer", "stats"],
        help="Repository action"
    )
    repo_parser.add_argument("--name", help="Repository name (owner/repo)")
    repo_parser.add_argument(
        "--template", help="Template repository for creation")
    repo_parser.add_argument("--description", help="Repository description")
    repo_parser.add_argument(
        "--private", action="store_true", help="Create a private repository")
    repo_parser.add_argument("--org", help="Organization for repository")
    repo_parser.add_argument(
        "--topics", help="Repository topics (comma separated)")
    return repo_parser


def _setup_pr_parser(subparsers) -> Any:
    """Setup pull request command parser."""
    pr_parser = subparsers.add_parser("pr", help="Pull request commands")
    pr_parser.add_argument(
        "action",
        choices=["list", "view", "create", "merge",
                 "close", "reopen", "diff", "checkout"],
        help="Pull request action"
    )
    pr_parser.add_argument("--repo", help="Repository name (owner/repo)")
    pr_parser.add_argument("--number", help="Pull request number")
    pr_parser.add_argument("--title", help="Pull request title")
    pr_parser.add_argument("--body", help="Pull request body")
    pr_parser.add_argument("--head", help="Head branch")
    pr_parser.add_argument("--base", help="Base branch")
    pr_parser.add_argument("--draft", action="store_true",
                           help="Create as draft pull request")
    pr_parser.add_argument(
        "--state", choices=["open", "closed", "all"], default="open", help="Filter by state")
    return pr_parser


def _setup_actions_parser(subparsers) -> Any:
    """Setup GitHub Actions command parser."""
    actions_parser = subparsers.add_parser(
        "actions", help="GitHub Actions commands")
    actions_parser.add_argument(
        "action",
        choices=["list", "runs", "view-run", "cancel", "rerun"],
        help="GitHub Actions action"
    )
    actions_parser.add_argument("--repo", help="Repository name (owner/repo)")
    actions_parser.add_argument("--id", help="Run ID or job ID")
    actions_parser.add_argument("--workflow", help="Workflow ID or filename")
    actions_parser.add_argument("--branch", help="Filter by branch name")
    actions_parser.add_argument(
        "--status",
        choices=["queued", "in_progress", "completed"],
        help="Filter by run status"
    )
    return actions_parser


def _setup_notifications_parser(subparsers) -> Any:
    """Setup notifications command parser."""
    notifications_parser = subparsers.add_parser(
        "notifications", help="Notification commands")
    notifications_parser.add_argument(
        "action",
        choices=["list", "read", "subscribe"],
        help="Notification action"
    )
    notifications_parser.add_argument(
        "--all", action="store_true", help="Include read notifications")
    notifications_parser.add_argument(
        "--participating",
        action="store_true",
        help="Only show notifications where you're participating"
    )
    notifications_parser.add_argument(
        "--since",
        help="Only show notifications updated after the given time"
    )
    notifications_parser.add_argument(
        "--repo", help="Repository name (owner/repo)")
    notifications_parser.add_argument("--thread", help="Thread ID")
    notifications_parser.add_argument(
        "--subscribed",
        action="store_true",
        help="Subscribe to thread notifications"
    )
    notifications_parser.add_argument(
        "--ignored",
        action="store_true",
        help="Ignore notifications from this thread"
    )
    return notifications_parser


def _setup_user_parser(subparsers) -> Any:
    """Setup user command parser."""
    user_parser = subparsers.add_parser("user", help="User commands")
    user_parser.add_argument(
        "action",
        choices=[
            "view", "followers", "following", "follow", "unfollow",
            "block", "unblock", "repos", "starred", "star", "unstar"
        ],
        help="User action"
    )
    user_parser.add_argument("--username", help="GitHub username")
    user_parser.add_argument("--repo", help="Repository name (owner/repo)")
    return user_parser


def _setup_org_parser(subparsers) -> Any:
    """Setup organization command parser."""
    org_parser = subparsers.add_parser("org", help="Organization commands")
    org_parser.add_argument(
        "action",
        choices=["list", "view", "repos", "teams", "members"],
        help="Organization action"
    )
    org_parser.add_argument("--name", help="Organization name")
    org_parser.add_argument("--team", help="Team name or ID")
    return org_parser


def _setup_search_parser(subparsers) -> Any:
    """Setup search command parser."""
    search_parser = subparsers.add_parser("search", help="Search commands")
    search_parser.add_argument(
        "action",
        choices=["repos", "users", "code", "issues", "commits"],
        help="Search type"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--sort", help="Sort field")
    search_parser.add_argument(
        "--order",
        choices=["asc", "desc"],
        default="desc",
        help="Sort order (asc or desc)"
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Limit number of results"
    )
    return search_parser


def _setup_release_parser(subparsers) -> Any:
    """Setup release command parser."""
    release_parser = subparsers.add_parser("release", help="Release commands")
    release_parser.add_argument(
        "action",
        choices=["list", "view", "create", "delete", "assets"],
        help="Release action"
    )
    release_parser.add_argument("--repo", help="Repository name (owner/repo)")
    release_parser.add_argument("--tag", help="Release tag")
    release_parser.add_argument("--name", help="Release name")
    release_parser.add_argument("--body", help="Release description")
    release_parser.add_argument(
        "--draft", action="store_true", help="Create as draft release")
    release_parser.add_argument(
        "--prerelease", action="store_true", help="Mark as prerelease")
    return release_parser


async def _handle_command(
    args,
    # Removed unused config parameter
    authenticator: Authenticator,
    client: GitHubClient,
    ui: TerminalUI
) -> int:
    """Handle command execution with modern pattern matching and error handling."""

    logger.debug(f"Handling command: {args.command}")

    # Check authentication requirements
    auth_required_commands = {
        # view doesn't need auth
        "repo": ["create", "delete", "fork", "transfer"],
        "pr": [],  # All PR commands need auth
        "actions": [],  # All actions commands need auth
        "dashboard": [],  # Dashboard needs auth
        "user": ["follow", "unfollow", "block", "unblock", "star", "unstar"],
        "notifications": [],  # All notification commands need auth
    }

    if args.command in auth_required_commands:
        # Check if this specific action requires auth
        required_actions = auth_required_commands[args.command]
        action = getattr(args, 'action', None)

        if not required_actions or action in required_actions or not action:
            if not authenticator.is_authenticated():
                console.print(
                    "[red]Authentication required. Use 'auth login' first.[/red]")
                logger.warning(
                    f"Authentication required for command: {args.command}")
                return 1

    # Use modern pattern matching for command handling
    match args.command:
        case "auth":
            # ui is used in _handle_auth_command
            return await _handle_auth_command(args, authenticator, ui)

        case "repo":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_repo_command(args)

        case "pr":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_pr_command(args)

        case "actions":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_actions_command(args)

        case "dashboard":
            dashboard = Dashboard(client, ui)
            await dashboard.start()
            return 0

        case "notifications":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_notifications_command(args)

        case "user":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_user_command(args)

        case "org":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_org_command(args)

        case "search":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_search_command(args)

        case "release":
            # Removed client and ui from call as they are unused in placeholder
            return await _handle_release_command(args)

        case _:
            console.print(f"[red]Unknown command: {args.command}[/red]")
            logger.error(f"Unknown command: {args.command}")
            return 1


async def _handle_auth_command(args, authenticator: Authenticator, ui: TerminalUI) -> int:
    """Handle authentication commands with enhanced error handling."""
    try:
        match args.action:
            case "login":
                await authenticator.login_interactive(scopes=args.scopes, sso=args.sso)

            case "logout":
                await authenticator.logout()

            case "status":
                if authenticator.is_authenticated():
                    user_info = await authenticator.fetch_user_info()
                    if user_info:
                        console.print(
                            f"[green]�Logged in as {user_info.login}[/green]")
                        if user_info.name:
                            console.print(f"[dim]Name: {user_info.name}[/dim]")
                        if user_info.email:
                            console.print(
                                f"[dim]Email: {user_info.email}[/dim]")
                    else:
                        console.print(
                            "[yellow]⚠️ Authenticated, but unable to fetch user info.[/yellow]")
                else:
                    console.print("[red]�Not logged in.[/red]")

            case "token":
                if authenticator.is_authenticated():
                    token = authenticator.token
                    if token:
                        # Show only the first 8 characters for security
                        masked_token = f"{token[:8]}{'*' * (len(token) - 8)}"
                        console.print(
                            f"[dim]Current token: {masked_token}[/dim]")
                    else:
                        console.print("[red]No active token.[/red]")
                else:
                    console.print("[red]Not logged in.[/red]")

            case "scopes":
                if authenticator.is_authenticated():
                    console.print(
                        "[dim]Scope information not yet implemented.[/dim]")
                else:
                    console.print("[red]Not logged in.[/red]")

        return 0

    except AuthenticationError as e:
        console.print(f"[red]Authentication error: {e}[/red]")
        logger.error(f"Authentication error: {e}")
        return 1
    except Exception as e:
        console.print(f"[red]Unexpected error in auth command: {e}[/red]")
        logger.exception("Unexpected error in auth command")
        return 1


# Placeholder command handlers - these would be implemented with proper command modules
# Removed unused client and ui parameters from placeholder functions
async def _handle_repo_command(args) -> int:
    """Handle repository commands."""
    console.print(
        f"[yellow]Repository command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_pr_command(args) -> int:
    """Handle pull request commands."""
    console.print(
        f"[yellow]Pull request command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_actions_command(args) -> int:
    """Handle GitHub Actions commands."""
    console.print(
        f"[yellow]Actions command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_notifications_command(args) -> int:
    """Handle notifications commands."""
    console.print(
        f"[yellow]Notifications command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_user_command(args) -> int:
    """Handle user commands."""
    console.print(
        f"[yellow]User command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_org_command(args) -> int:
    """Handle organization commands."""
    console.print(
        f"[yellow]Organization command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_search_command(args) -> int:
    """Handle search commands."""
    console.print(
        f"[yellow]Search command '{args.action}' not yet implemented.[/yellow]")
    return 0


# Removed unused client and ui parameters from placeholder functions
async def _handle_release_command(args) -> int:
    """Handle release commands."""
    console.print(
        f"[yellow]Release command '{args.action}' not yet implemented.[/yellow]")
    return 0


def main_entrypoint() -> NoReturn:
    """Entry point for the CLI when installed as a package."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.exception("Fatal error in main entrypoint")
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.exception("Fatal error in main execution")
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)
