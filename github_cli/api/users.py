"""
GitHub Users API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.models.user import User
from github_cli.models.repository import Repository
from github_cli.utils.exceptions import APIError, ValidationError


async def get_user(
    client: GitHubClient,
    username: Optional[str] = None
) -> User:
    """
    Get a user's information

    Args:
        client: The GitHub client
        username: Username (if None, gets authenticated user)

    Returns:
        User object
    """
    if username:
        response = await client.get(f"/users/{username}")
    else:
        response = await client.get("/user")

    return User.from_json(response.data)


async def get_authenticated_user(client: GitHubClient) -> User:
    """
    Get the authenticated user's information

    Args:
        client: The GitHub client

    Returns:
        User object
    """
    return await get_user(client)


async def list_followers(
    client: GitHubClient,
    username: Optional[str] = None,
    per_page: int = 100,
    max_pages: int = 1
) -> List[User]:
    """
    List followers of a user

    Args:
        client: The GitHub client
        username: Username (if None, uses authenticated user)
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of User objects
    """
    if username:
        endpoint = f"/users/{username}/followers"
    else:
        endpoint = "/user/followers"

    response = await client.paginated_request(
        "GET",
        endpoint,
        params={"per_page": per_page},
        max_pages=max_pages
    )

    return [User.from_json(item) for item in response]


async def list_following(
    client: GitHubClient,
    username: Optional[str] = None,
    per_page: int = 100,
    max_pages: int = 1
) -> List[User]:
    """
    List users a user is following

    Args:
        client: The GitHub client
        username: Username (if None, uses authenticated user)
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of User objects
    """
    if username:
        endpoint = f"/users/{username}/following"
    else:
        endpoint = "/user/following"

    response = await client.paginated_request(
        "GET",
        endpoint,
        params={"per_page": per_page},
        max_pages=max_pages
    )

    return [User.from_json(item) for item in response]


async def check_following(
    client: GitHubClient,
    username: str,
    target_user: Optional[str] = None
) -> bool:
    """
    Check if a user follows another user

    Args:
        client: The GitHub client
        username: Username
        target_user: Target username (if None, checks if authenticated user follows username)

    Returns:
        True if following
    """
    try:
        if target_user:
            # Check if username follows target_user
            await client.get(f"/users/{username}/following/{target_user}")
        else:
            # Check if authenticated user follows username
            await client.get(f"/user/following/{username}")

        return True
    except APIError:
        return False


async def follow_user(
    client: GitHubClient,
    username: str
) -> bool:
    """
    Follow a user (authenticated user)

    Args:
        client: The GitHub client
        username: Username to follow

    Returns:
        True if successful
    """
    try:
        await client.put(f"/user/following/{username}", data={})
        return True
    except APIError:
        return False


async def unfollow_user(
    client: GitHubClient,
    username: str
) -> bool:
    """
    Unfollow a user (authenticated user)

    Args:
        client: The GitHub client
        username: Username to unfollow

    Returns:
        True if successful
    """
    try:
        await client.delete(f"/user/following/{username}")
        return True
    except APIError:
        return False


async def list_user_repositories(
    client: GitHubClient,
    username: Optional[str] = None,
    type_filter: str = "owner",
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 100,
    max_pages: int = 2
) -> List[Repository]:
    """
    List repositories for a user

    Args:
        client: The GitHub client
        username: Username (if None, uses authenticated user)
        type_filter: Type of repositories (all, owner, member)
        sort: Sort by (created, updated, pushed, full_name)
        direction: Sort direction (asc, desc)
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of Repository objects
    """
    params = {
        "per_page": per_page,
        "sort": sort,
        "direction": direction
    }

    if username:
        endpoint = f"/users/{username}/repos"
    else:
        endpoint = "/user/repos"
        params["type"] = type_filter

    response = await client.paginated_request(
        "GET",
        endpoint,
        params=params,
        max_pages=max_pages
    )

    return [Repository.from_json(item) for item in response]


async def list_user_starred_repositories(
    client: GitHubClient,
    username: Optional[str] = None,
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 100,
    max_pages: int = 2
) -> List[Repository]:
    """
    List repositories starred by a user

    Args:
        client: The GitHub client
        username: Username (if None, uses authenticated user)
        sort: Sort by (created, updated)
        direction: Sort direction (asc, desc)
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of Repository objects
    """
    params = {
        "per_page": per_page,
        "sort": sort,
        "direction": direction
    }

    if username:
        endpoint = f"/users/{username}/starred"
    else:
        endpoint = "/user/starred"

    response = await client.paginated_request(
        "GET",
        endpoint,
        params=params,
        max_pages=max_pages
    )

    return [Repository.from_json(item) for item in response]


async def check_starred(
    client: GitHubClient,
    owner: str,
    repo: str,
    username: Optional[str] = None
) -> bool:
    """
    Check if a user has starred a repository

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        username: Username (if None, uses authenticated user)

    Returns:
        True if starred
    """
    try:
        if username:
            # Not supported by GitHub API, need to check list of starred repos
            starred = await list_user_starred_repositories(client, username, max_pages=1)
            return any(r.full_name == f"{owner}/{repo}" for r in starred)
        else:
            # Check if authenticated user has starred the repo
            await client.get(f"/user/starred/{owner}/{repo}")
            return True
    except APIError:
        return False


async def star_repository(
    client: GitHubClient,
    owner: str,
    repo: str
) -> bool:
    """
    Star a repository (authenticated user)

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name

    Returns:
        True if successful
    """
    try:
        await client.put(f"/user/starred/{owner}/{repo}", data={})
        return True
    except APIError:
        return False


async def unstar_repository(
    client: GitHubClient,
    owner: str,
    repo: str
) -> bool:
    """
    Unstar a repository (authenticated user)

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name

    Returns:
        True if successful
    """
    try:
        await client.delete(f"/user/starred/{owner}/{repo}")
        return True
    except APIError:
        return False


async def update_user_profile(
    client: GitHubClient,
    name: Optional[str] = None,
    email: Optional[str] = None,
    blog: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    hireable: Optional[bool] = None,
    bio: Optional[str] = None,
    twitter_username: Optional[str] = None
) -> User:
    """
    Update the authenticated user's profile

    Args:
        client: The GitHub client
        name: Full name
        email: Email address (public)
        blog: Blog or website URL
        company: Company name
        location: Location
        hireable: Whether user is available for hire
        bio: Bio/description
        twitter_username: Twitter username

    Returns:
        Updated User object
    """
    data = {}

    if name is not None:
        data["name"] = name

    if email is not None:
        data["email"] = email

    if blog is not None:
        data["blog"] = blog

    if company is not None:
        data["company"] = company

    if location is not None:
        data["location"] = location

    if hireable is not None:
        data["hireable"] = str(hireable).lower()

    if bio is not None:
        data["bio"] = bio

    if twitter_username is not None:
        data["twitter_username"] = twitter_username

    if not data:
        # No changes, just return current user
        return await get_authenticated_user(client)

    response = await client.patch("/user", data=data)
    return User.from_json(response.data)


# Handler function for CLI commands
async def handle_user_command(args: Dict[str, Any], client: GitHubClient, ui: Any) -> None:
    """Handle user commands from the CLI"""
    action = args.get("user_action")

    try:
        if action == "view":
            username = args.get("name")

            if username:
                user = await get_user(client, username)
            else:
                user = await get_authenticated_user(client)

            ui.display_heading(f"User: {user.login}")

            if user.name:
                ui.display_info(f"Name: {user.name}")

            if user.bio:
                ui.display_info(f"Bio: {user.bio}")

            if user.company:
                ui.display_info(f"Company: {user.company}")

            if user.location:
                ui.display_info(f"Location: {user.location}")

            if user.email:
                ui.display_info(f"Email: {user.email}")

            if user.blog:
                ui.display_info(f"Blog: {user.blog}")

            if user.twitter_username:
                ui.display_info(f"Twitter: @{user.twitter_username}")

            ui.display_info(f"Followers: {user.followers}")
            ui.display_info(f"Following: {user.following}")
            ui.display_info(f"Public Repositories: {user.public_repos}")
            ui.display_info(f"Public Gists: {user.public_gists}")

            if user.created_date:
                ui.display_info(
                    f"Created: {user.created_date.strftime('%Y-%m-%d')}")

            ui.display_info(f"URL: {user.html_url}")

        elif action == "followers":
            username = args.get("name")

            followers = await list_followers(client, username)

            if not followers:
                if username:
                    ui.display_info(f"No followers found for {username}")
                else:
                    ui.display_info("You have no followers")
                return

            title = f"Followers of {username}" if username else "Your Followers"
            ui.display_heading(title)

            table = ui.create_table("Username", "Name", "URL")

            for follower in followers:
                table.add_row(
                    follower.login,
                    follower.name or "",
                    follower.html_url
                )

            ui.console.print(table)

        elif action == "following":
            username = args.get("name")

            following = await list_following(client, username)

            if not following:
                if username:
                    ui.display_info(f"{username} is not following anyone")
                else:
                    ui.display_info("You are not following anyone")
                return

            title = f"Users followed by {username}" if username else "Users You Follow"
            ui.display_heading(title)

            table = ui.create_table("Username", "Name", "URL")

            for user in following:
                table.add_row(
                    user.login,
                    user.name or "",
                    user.html_url
                )

            ui.console.print(table)

        elif action == "repos":
            username = args.get("name")
            type_filter = args.get("type", "owner")
            sort = args.get("sort", "updated")

            repositories = await list_user_repositories(
                client,
                username,
                type_filter=type_filter,
                sort=sort
            )

            if not repositories:
                if username:
                    ui.display_info(f"No repositories found for {username}")
                else:
                    ui.display_info("You have no repositories")
                return

            title = f"Repositories for {username}" if username else "Your Repositories"
            ui.display_heading(title)

            table = ui.create_table(
                "Name", "Description", "Language", "Stars", "Updated")

            for repo in repositories:
                updated = repo.updated_date.strftime(
                    "%Y-%m-%d") if repo.updated_date else ""

                table.add_row(
                    repo.name,
                    repo.description or "",
                    repo.language or "",
                    str(repo.stargazers_count),
                    updated
                )

            ui.console.print(table)

        elif action == "starred":
            username = args.get("name")

            repositories = await list_user_starred_repositories(client, username)

            if not repositories:
                if username:
                    ui.display_info(
                        f"{username} hasn't starred any repositories")
                else:
                    ui.display_info("You haven't starred any repositories")
                return

            title = f"Starred repositories for {username}" if username else "Your Starred Repositories"
            ui.display_heading(title)

            table = ui.create_table(
                "Repository", "Description", "Language", "Stars")

            for repo in repositories:
                table.add_row(
                    repo.full_name,
                    repo.description or "",
                    repo.language or "",
                    str(repo.stargazers_count)
                )

            ui.console.print(table)

        elif action == "follow":
            username = args.get("name")

            if not username:
                ui.display_error("Username required")
                return

            success = await follow_user(client, username)

            if success:
                ui.display_success(f"You are now following {username}")
            else:
                ui.display_error(f"Failed to follow {username}")

        elif action == "unfollow":
            username = args.get("name")

            if not username:
                ui.display_error("Username required")
                return

            success = await unfollow_user(client, username)

            if success:
                ui.display_success(f"You have unfollowed {username}")
            else:
                ui.display_error(f"Failed to unfollow {username}")

        elif action == "check-follow":
            username = args.get("name")
            target = args.get("target")

            if not username:
                ui.display_error("Username required")
                return

            if target:
                # Check if username follows target
                is_following = await check_following(client, username, target)
                if is_following:
                    ui.display_info(f"{username} follows {target}")
                else:
                    ui.display_info(f"{username} does not follow {target}")
            else:
                # Check if authenticated user follows username
                is_following = await check_following(client, username)
                if is_following:
                    ui.display_info(f"You follow {username}")
                else:
                    ui.display_info(f"You do not follow {username}")

        elif action == "update":
            # Create a dictionary of update fields
            update_fields = {}

            if args.get("name") is not None:
                update_fields["name"] = args.get("name")

            if args.get("email") is not None:
                update_fields["email"] = args.get("email")

            if args.get("blog") is not None:
                update_fields["blog"] = args.get("blog")

            if args.get("company") is not None:
                update_fields["company"] = args.get("company")

            if args.get("location") is not None:
                update_fields["location"] = args.get("location")

            if args.get("bio") is not None:
                update_fields["bio"] = args.get("bio")

            if args.get("twitter") is not None:
                update_fields["twitter_username"] = args.get("twitter")

            if args.get("hireable") is not None:
                update_fields["hireable"] = args.get("hireable")

            if not update_fields:
                ui.display_error("No update fields provided")
                return

            user = await update_user_profile(client, **update_fields)

            ui.display_success("Profile updated successfully")

            # Display updated profile
            ui.display_heading(f"Updated Profile: {user.login}")

            if user.name:
                ui.display_info(f"Name: {user.name}")

            if user.email:
                ui.display_info(f"Email: {user.email}")

            if user.blog:
                ui.display_info(f"Blog: {user.blog}")

            if user.company:
                ui.display_info(f"Company: {user.company}")

            if user.location:
                ui.display_info(f"Location: {user.location}")

            if user.bio:
                ui.display_info(f"Bio: {user.bio}")

            if user.twitter_username:
                ui.display_info(f"Twitter: @{user.twitter_username}")

            hireable_status = "Yes" if user.hireable else "No" if user.hireable is False else "Not specified"
            ui.display_info(f"Available for hire: {hireable_status}")

        else:
            ui.display_error(f"Unknown user action: {action}")
            ui.display_info(
                "Available actions: view, followers, following, repos, starred, follow, unfollow, check-follow, update")

    except APIError as e:
        ui.display_error(f"API error: {str(e)}")
    except Exception as e:
        ui.display_error(f"Error: {str(e)}")
