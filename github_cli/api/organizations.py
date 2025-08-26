"""
GitHub Organizations API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, cast
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.models.repository import Repository
from github_cli.models.team import Team
from github_cli.models.user import User
from github_cli.utils.exceptions import APIError, ValidationError


async def list_organizations(
    client: GitHubClient,
    per_page: int = 30,
    max_pages: int = 3
) -> List[Dict[str, Any]]:
    """
    List organizations for the authenticated user

    Args:
        client: The GitHub client
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of organization data
    """
    response = await client.paginated_request(
        "GET",
        "/user/orgs",
        params={"per_page": per_page},
        max_pages=max_pages
    )

    return response


async def get_organization(
    client: GitHubClient,
    org_name: str
) -> Dict[str, Any]:
    """
    Get information about an organization

    Args:
        client: The GitHub client
        org_name: Organization name

    Returns:
        Organization data
    """
    response = await client.get(f"/orgs/{org_name}")
    return cast(Dict[str, Any], response.data)


async def get_organization_members(
    client: GitHubClient,
    org_name: str,
    role: str = "all",
    filter_2fa: Optional[bool] = None,
    per_page: int = 100,
    max_pages: int = 5
) -> List[User]:
    """
    List members of an organization

    Args:
        client: The GitHub client
        org_name: Organization name
        role: Filter by role (all, admin, member)
        filter_2fa: Filter by 2FA requirement
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of User objects
    """
    params = {
        "per_page": per_page,
        "role": role
    }

    if filter_2fa is not None:
        params["filter"] = "2fa_disabled" if filter_2fa is False else "2fa_enabled"

    response = await client.paginated_request(
        "GET",
        f"/orgs/{org_name}/members",
        params=params,
        max_pages=max_pages
    )

    return [User.from_json(item) for item in response]


async def get_organization_teams(
    client: GitHubClient,
    org_name: str,
    per_page: int = 100,
    max_pages: int = 5
) -> List[Team]:
    """
    List teams in an organization

    Args:
        client: The GitHub client
        org_name: Organization name
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of Team objects
    """
    response = await client.paginated_request(
        "GET",
        f"/orgs/{org_name}/teams",
        params={"per_page": per_page},
        max_pages=max_pages
    )

    return [Team.from_json(item) for item in response]


async def get_team(
    client: GitHubClient,
    org_name: str,
    team_slug: str
) -> Team:
    """
    Get a team by name

    Args:
        client: The GitHub client
        org_name: Organization name
        team_slug: Team slug

    Returns:
        Team object
    """
    response = await client.get(f"/orgs/{org_name}/teams/{team_slug}")
    return Team.from_json(response.data)


async def get_team_members(
    client: GitHubClient,
    org_name: str,
    team_slug: str,
    role: str = "all",
    per_page: int = 100,
    max_pages: int = 5
) -> List[User]:
    """
    List members of a team

    Args:
        client: The GitHub client
        org_name: Organization name
        team_slug: Team slug
        role: Filter by role (all, maintainer, member)
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of User objects
    """
    params = {
        "per_page": per_page,
        "role": role
    }

    response = await client.paginated_request(
        "GET",
        f"/orgs/{org_name}/teams/{team_slug}/members",
        params=params,
        max_pages=max_pages
    )

    return [User.from_json(item) for item in response]


async def get_team_repositories(
    client: GitHubClient,
    org_name: str,
    team_slug: str,
    per_page: int = 100,
    max_pages: int = 5
) -> List[Repository]:
    """
    List repositories that a team has access to

    Args:
        client: The GitHub client
        org_name: Organization name
        team_slug: Team slug
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of Repository objects
    """
    response = await client.paginated_request(
        "GET",
        f"/orgs/{org_name}/teams/{team_slug}/repos",
        params={"per_page": per_page},
        max_pages=max_pages
    )

    return [Repository.from_json(item) for item in response]


async def get_organization_repositories(
    client: GitHubClient,
    org_name: str,
    type_filter: str = "all",
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 100,
    max_pages: int = 5
) -> List[Repository]:
    """
    List repositories in an organization

    Args:
        client: The GitHub client
        org_name: Organization name
        type_filter: Type of repositories (all, public, private, forks, sources, member, internal)
        sort: Sort by (created, updated, pushed, full_name)
        direction: Sort direction (asc, desc)
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of Repository objects
    """
    params = {
        "per_page": per_page,
        "type": type_filter,
        "sort": sort,
        "direction": direction
    }

    response = await client.paginated_request(
        "GET",
        f"/orgs/{org_name}/repos",
        params=params,
        max_pages=max_pages
    )

    return [Repository.from_json(item) for item in response]


async def check_membership(
    client: GitHubClient,
    org_name: str,
    username: str
) -> Dict[str, Any]:
    """
    Check if a user is a member of an organization

    Args:
        client: The GitHub client
        org_name: Organization name
        username: GitHub username

    Returns:
        Membership status data
    """
    try:
        response = await client.get(f"/orgs/{org_name}/memberships/{username}")
        return {
            "state": response.data.get("state", ""),
            "role": response.data.get("role", ""),
            "is_member": True
        }
    except APIError as e:
        if e.status_code == 404:
            return {
                "state": "not_member",
                "role": None,
                "is_member": False
            }
        raise


async def invite_user(
    client: GitHubClient,
    org_name: str,
    username: str,
    role: str = "member",
    team_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Invite a user to an organization

    Args:
        client: The GitHub client
        org_name: Organization name
        username: GitHub username
        role: Role (admin, member, billing_manager)
        team_ids: List of team IDs to add the user to

    Returns:
        Invitation data
    """
    data = {
        "role": role
    }

    if team_ids:
        data["team_ids"] = team_ids  # type: ignore

    response = await client.post(f"/orgs/{org_name}/memberships/{username}", data=data)
    return cast(Dict[str, Any], response.data)


async def remove_member(
    client: GitHubClient,
    org_name: str,
    username: str
) -> bool:
    """
    Remove a member from an organization

    Args:
        client: The GitHub client
        org_name: Organization name
        username: GitHub username

    Returns:
        True if successful
    """
    try:
        await client.delete(f"/orgs/{org_name}/memberships/{username}")
        return True
    except APIError:
        return False


# Handler function for CLI commands
async def handle_org_command(args: Dict[str, Any], client: GitHubClient, ui: Any) -> None:
    """Handle organization commands from the CLI"""
    action = args.get("org_action")

    try:
        if action == "list":
            # List organizations
            orgs = await list_organizations(client)

            if not orgs:
                ui.display_info("You are not a member of any organizations")
                return

            ui.display_heading("Your Organizations")

            table = ui.create_table("Name", "URL", "Description")

            for org in orgs:
                table.add_row(
                    org.get("login", "Unknown"),
                    org.get("url", ""),
                    org.get("description", "") or ""
                )

            ui.console.print(table)

        elif action == "view":
            org_name = args.get("name")
            if not org_name:
                ui.display_error("Organization name required")
                return

            # Get organization details
            org = await get_organization(client, org_name)

            ui.display_heading(f"Organization: {org_name}")

            if org.get("description"):
                ui.display_info(f"Description: {org['description']}")

            ui.display_info(f"URL: {org.get('html_url', '')}")
            ui.display_info(f"Email: {org.get('email', 'Not specified')}")
            ui.display_info(
                f"Location: {org.get('location', 'Not specified')}")
            ui.display_info(
                f"Public Repositories: {org.get('public_repos', 0)}")

            # Get basic member counts
            try:
                members = await get_organization_members(client, org_name, max_pages=1)
                ui.display_info(f"Members: {len(members)}+")
            except APIError:
                ui.display_info("Members: Unknown (no access)")

        elif action == "members":
            org_name = args.get("name")
            role = args.get("role", "all")

            if not org_name:
                ui.display_error("Organization name required")
                return

            # Get members
            members = await get_organization_members(client, org_name, role=role)

            if not members:
                ui.display_info(f"No members found for {org_name}")
                return

            ui.display_heading(f"Members of {org_name}")

            table = ui.create_table("Username", "Type", "URL")

            for member in members:
                table.add_row(
                    member.login,
                    member.type,
                    member.html_url
                )

            ui.console.print(table)

        elif action == "teams":
            org_name = args.get("name")

            if not org_name:
                ui.display_error("Organization name required")
                return

            # Get teams
            try:
                teams = await get_organization_teams(client, org_name)

                if not teams:
                    ui.display_info(f"No teams found for {org_name}")
                    return

                ui.display_heading(f"Teams in {org_name}")

                table = ui.create_table("Name", "Description", "Permission")

                for team in teams:
                    table.add_row(
                        team.name,
                        team.description or "",
                        team.permission
                    )

                ui.console.print(table)

            except APIError as e:
                ui.display_error(f"Error getting teams: {str(e)}")

        elif action == "repos":
            org_name = args.get("name")
            type_filter = args.get("type", "all")

            if not org_name:
                ui.display_error("Organization name required")
                return

            # Get repositories
            repos = await get_organization_repositories(
                client,
                org_name,
                type_filter=type_filter
            )

            if not repos:
                ui.display_info(f"No repositories found for {org_name}")
                return

            ui.display_heading(f"Repositories in {org_name}")

            table = ui.create_table(
                "Name", "Description", "Language", "Stars", "Visibility")

            for repo in repos:
                visibility = "Private" if repo.private else "Public"
                table.add_row(
                    repo.name,
                    repo.description or "",
                    repo.language or "Unknown",
                    str(repo.stargazers_count),
                    visibility
                )

            ui.console.print(table)

        elif action == "team-members":
            org_name = args.get("org")
            team_name = args.get("team")

            if not org_name or not team_name:
                ui.display_error("Organization and team name required")
                return

            # Get team members
            try:
                # Get team first to validate
                team = await get_team(client, org_name, team_name)

                # Then get members
                members = await get_team_members(client, org_name, team_name)

                if not members:
                    ui.display_info(f"No members found for team {team_name}")
                    return

                ui.display_heading(f"Members of {org_name}/{team.name}")

                table = ui.create_table("Username", "Type", "URL")

                for member in members:
                    table.add_row(
                        member.login,
                        member.type,
                        member.html_url
                    )

                ui.console.print(table)

            except APIError as e:
                ui.display_error(f"Error getting team members: {str(e)}")

        elif action == "team-repos":
            org_name = args.get("org")
            team_name = args.get("team")

            if not org_name or not team_name:
                ui.display_error("Organization and team name required")
                return

            # Get team repositories
            try:
                # Get team first to validate
                team = await get_team(client, org_name, team_name)

                # Then get repositories
                repos = await get_team_repositories(client, org_name, team_name)

                if not repos:
                    ui.display_info(
                        f"No repositories found for team {team_name}")
                    return

                ui.display_heading(f"Repositories for {org_name}/{team.name}")

                table = ui.create_table(
                    "Name", "Description", "Language", "Stars")

                for repo in repos:
                    table.add_row(
                        repo.name,
                        repo.description or "",
                        repo.language or "Unknown",
                        str(repo.stargazers_count)
                    )

                ui.console.print(table)

            except APIError as e:
                ui.display_error(f"Error getting team repositories: {str(e)}")

        elif action == "check-membership":
            org_name = args.get("org")
            username = args.get("user")

            if not org_name or not username:
                ui.display_error("Organization and username required")
                return

            # Check membership
            try:
                membership = await check_membership(client, org_name, username)

                if membership["is_member"]:
                    ui.display_success(f"{username} is a member of {org_name}")
                    ui.display_info(f"Role: {membership['role']}")
                    ui.display_info(f"State: {membership['state']}")
                else:
                    ui.display_info(
                        f"{username} is not a member of {org_name}")

            except APIError as e:
                ui.display_error(f"Error checking membership: {str(e)}")

        else:
            ui.display_error(f"Unknown organization action: {action}")
            ui.display_info(
                "Available actions: list, view, members, teams, repos, team-members, team-repos, check-membership")

    except APIError as e:
        ui.display_error(f"API error: {str(e)}")
    except Exception as e:
        ui.display_error(f"Error: {str(e)}")
