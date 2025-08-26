"""
GitHub Search API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.models.repository import Repository
from github_cli.models.user import User
from github_cli.utils.exceptions import APIError, ValidationError


async def search_repositories(
    client: GitHubClient,
    query: str,
    sort: Optional[str] = None,
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
    max_results: Optional[int] = None
) -> Tuple[List[Repository], Dict[str, Any]]:
    """
    Search for repositories

    Args:
        client: The GitHub client
        query: Search query
        sort: Sort field (stars, forks, updated)
        order: Sort order (asc, desc)
        per_page: Results per page
        page: Page number
        max_results: Maximum number of results to return

    Returns:
        Tuple of (List of Repository objects, search metadata)
    """
    # Validate sort field
    if sort and sort not in ["stars", "forks", "updated", "help-wanted-issues"]:
        raise ValidationError(f"Invalid sort field: {sort}")

    # Validate order
    if order not in ["asc", "desc"]:
        raise ValidationError(f"Invalid order: {order}")

    # Set up parameters
    params = {
        "q": query,
        "per_page": min(100, per_page),
        "page": page,
        "order": order
    }

    if sort:
        params["sort"] = sort

    # Make request
    response = await client.request(
        "GET",
        "/search/repositories",
        params=params
    )

    # Extract metadata
    metadata = {
        "total_count": response.data.get("total_count", 0),
        "incomplete_results": response.data.get("incomplete_results", False)
    }

    # Process results
    items = response.data.get("items", [])

    # Apply max_results limit if specified
    if max_results:
        items = items[:max_results]

    # Convert to Repository objects
    repositories = [Repository.from_json(item) for item in items]

    return repositories, metadata


async def search_code(
    client: GitHubClient,
    query: str,
    sort: Optional[str] = None,
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
    max_results: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for code

    Args:
        client: The GitHub client
        query: Search query
        sort: Sort field (indexed)
        order: Sort order (asc, desc)
        per_page: Results per page
        page: Page number
        max_results: Maximum number of results to return

    Returns:
        Tuple of (List of code matches, search metadata)
    """
    # Validate sort field
    if sort and sort not in ["indexed"]:
        raise ValidationError(f"Invalid sort field: {sort}")

    # Validate order
    if order not in ["asc", "desc"]:
        raise ValidationError(f"Invalid order: {order}")

    # Set up parameters
    params = {
        "q": query,
        "per_page": min(100, per_page),
        "page": page,
        "order": order
    }

    if sort:
        params["sort"] = sort

    # Make request
    response = await client.request(
        "GET",
        "/search/code",
        params=params,
        headers={"Accept": "application/vnd.github.v3.text-match+json"}
    )

    # Extract metadata
    metadata = {
        "total_count": response.data.get("total_count", 0),
        "incomplete_results": response.data.get("incomplete_results", False)
    }

    # Process results
    items = response.data.get("items", [])

    # Apply max_results limit if specified
    if max_results:
        items = items[:max_results]

    return items, metadata


async def search_users(
    client: GitHubClient,
    query: str,
    sort: Optional[str] = None,
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
    max_results: Optional[int] = None
) -> Tuple[List[User], Dict[str, Any]]:
    """
    Search for users

    Args:
        client: The GitHub client
        query: Search query
        sort: Sort field (followers, repositories, joined)
        order: Sort order (asc, desc)
        per_page: Results per page
        page: Page number
        max_results: Maximum number of results to return

    Returns:
        Tuple of (List of User objects, search metadata)
    """
    # Validate sort field
    if sort and sort not in ["followers", "repositories", "joined"]:
        raise ValidationError(f"Invalid sort field: {sort}")

    # Validate order
    if order not in ["asc", "desc"]:
        raise ValidationError(f"Invalid order: {order}")

    # Set up parameters
    params = {
        "q": query,
        "per_page": min(100, per_page),
        "page": page,
        "order": order
    }

    if sort:
        params["sort"] = sort

    # Make request
    response = await client.request(
        "GET",
        "/search/users",
        params=params
    )

    # Extract metadata
    metadata = {
        "total_count": response.data.get("total_count", 0),
        "incomplete_results": response.data.get("incomplete_results", False)
    }

    # Process results
    items = response.data.get("items", [])

    # Apply max_results limit if specified
    if max_results:
        items = items[:max_results]

    # Convert to User objects
    users = [User.from_json(item) for item in items]

    return users, metadata


async def search_issues(
    client: GitHubClient,
    query: str,
    sort: Optional[str] = None,
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
    max_results: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for issues and pull requests

    Args:
        client: The GitHub client
        query: Search query
        sort: Sort field (created, updated, comments)
        order: Sort order (asc, desc)
        per_page: Results per page
        page: Page number
        max_results: Maximum number of results to return

    Returns:
        Tuple of (List of issue/PR data, search metadata)
    """
    # Validate sort field
    if sort and sort not in ["created", "updated", "comments"]:
        raise ValidationError(f"Invalid sort field: {sort}")

    # Validate order
    if order not in ["asc", "desc"]:
        raise ValidationError(f"Invalid order: {order}")

    # Set up parameters
    params = {
        "q": query,
        "per_page": min(100, per_page),
        "page": page,
        "order": order
    }

    if sort:
        params["sort"] = sort

    # Make request
    response = await client.request(
        "GET",
        "/search/issues",
        params=params
    )

    # Extract metadata
    metadata = {
        "total_count": response.data.get("total_count", 0),
        "incomplete_results": response.data.get("incomplete_results", False)
    }

    # Process results
    items = response.data.get("items", [])

    # Apply max_results limit if specified
    if max_results:
        items = items[:max_results]

    return items, metadata


async def search_commits(
    client: GitHubClient,
    query: str,
    sort: Optional[str] = None,
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
    max_results: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for commits

    Args:
        client: The GitHub client
        query: Search query
        sort: Sort field (author-date, committer-date)
        order: Sort order (asc, desc)
        per_page: Results per page
        page: Page number
        max_results: Maximum number of results to return

    Returns:
        Tuple of (List of commit data, search metadata)
    """
    # Validate sort field
    if sort and sort not in ["author-date", "committer-date"]:
        raise ValidationError(f"Invalid sort field: {sort}")

    # Validate order
    if order not in ["asc", "desc"]:
        raise ValidationError(f"Invalid order: {order}")

    # Set up parameters
    params = {
        "q": query,
        "per_page": min(100, per_page),
        "page": page,
        "order": order
    }

    if sort:
        params["sort"] = sort

    # Make request with commits preview header
    response = await client.request(
        "GET",
        "/search/commits",
        params=params,
        headers={"Accept": "application/vnd.github.cloak-preview+json"}
    )

    # Extract metadata
    metadata = {
        "total_count": response.data.get("total_count", 0),
        "incomplete_results": response.data.get("incomplete_results", False)
    }

    # Process results
    items = response.data.get("items", [])

    # Apply max_results limit if specified
    if max_results:
        items = items[:max_results]

    return items, metadata


async def search_topics(
    client: GitHubClient,
    query: str,
    per_page: int = 30,
    page: int = 1,
    max_results: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Search for repository topics

    Args:
        client: The GitHub client
        query: Search query
        per_page: Results per page
        page: Page number
        max_results: Maximum number of results to return

    Returns:
        Tuple of (List of topic data, search metadata)
    """
    # Set up parameters
    params = {
        "q": query,
        "per_page": min(100, per_page),
        "page": page
    }

    # Make request with topics preview header
    response = await client.request(
        "GET",
        "/search/topics",
        params=params,
        headers={"Accept": "application/vnd.github.mercy-preview+json"}
    )

    # Extract metadata
    metadata = {
        "total_count": response.data.get("total_count", 0),
        "incomplete_results": response.data.get("incomplete_results", False)
    }

    # Process results
    items = response.data.get("items", [])

    # Apply max_results limit if specified
    if max_results:
        items = items[:max_results]

    return items, metadata


# Handler function for CLI commands
async def handle_search_command(args: Dict[str, Any], client: GitHubClient, ui: Any) -> None:
    """Handle search commands from the CLI"""
    action = args.get("search_action")
    query = args.get("query", "")
    sort = args.get("sort")
    limit = args.get("limit", 10)

    if not query:
        ui.display_error("Search query required")
        return

    try:
        if action == "repos":
            # Search for repositories
            results, metadata = await search_repositories(
                client,
                query,
                sort=sort,
                max_results=limit
            )

            ui.display_heading(f"Repository Search: {query}")
            ui.display_info(f"Found {metadata['total_count']} repositories")

            table = ui.create_table(
                "Name",
                "Description",
                "Stars",
                "Language",
                title=f"Results ({len(results)} of {metadata['total_count']})"
            )

            for repo in results:
                table.add_row(
                    repo.full_name,
                    repo.description or "",
                    str(repo.stargazers_count),
                    repo.language or "Unknown"
                )

            ui.console.print(table)

        elif action == "code":
            # Search for code
            code_results, metadata = await search_code(
                client,
                query,
                max_results=limit
            )

            ui.display_heading(f"Code Search: {query}")
            ui.display_info(f"Found {metadata['total_count']} code results")

            for idx, item in enumerate(code_results):
                repo = item.get("repository", {}).get("full_name", "Unknown")
                path = item.get("path", "")

                ui.display_heading(f"{idx+1}. {repo}/{path}", level=2)

                # Display code snippets if available
                text_matches = item.get("text_matches", [])
                for match in text_matches:
                    fragment = match.get("fragment", "")
                    if fragment:
                        ui.display_code(fragment, language="")

                ui.display_link(item.get("html_url", ""))
                ui.console.print("")

        elif action == "users":
            # Search for users
            user_results, metadata = await search_users(
                client,
                query,
                sort=sort,
                max_results=limit
            )

            ui.display_heading(f"User Search: {query}")
            ui.display_info(f"Found {metadata['total_count']} users")

            table = ui.create_table(
                "Username",
                "Type",
                "Profile",
                title=f"Results ({len(results)} of {metadata['total_count']})"
            )

            for user in user_results:
                table.add_row(
                    user.login,
                    user.type,
                    user.html_url
                )

            ui.console.print(table)

        elif action == "issues":
            # Search for issues
            issue_results, metadata = await search_issues(
                client,
                query,
                sort=sort,
                max_results=limit
            )

            ui.display_heading(f"Issues Search: {query}")
            ui.display_info(f"Found {metadata['total_count']} issues/PRs")

            table = ui.create_table(
                "Repository",
                "Title",
                "State",
                "Created By",
                title=f"Results ({len(results)} of {metadata['total_count']})"
            )

            for item in issue_results:
                repo = item.get("repository_url", "").split("/repos/")[-1]
                table.add_row(
                    repo,
                    item.get("title", ""),
                    item.get("state", "unknown"),
                    item.get("user", {}).get("login", "Unknown")
                )

            ui.console.print(table)

        elif action == "commits":
            # Search for commits
            commit_results, metadata = await search_commits(
                client,
                query,
                sort=sort,
                max_results=limit
            )

            ui.display_heading(f"Commits Search: {query}")
            ui.display_info(f"Found {metadata['total_count']} commits")

            for idx, item in enumerate(commit_results):
                commit = item.get("commit", {})
                repo = item.get("repository", {}).get("full_name", "Unknown")

                ui.display_heading(
                    f"{idx+1}. {repo}: {commit.get('message', '')[:60]}...", level=2)

                # Display commit info
                ui.display_info(
                    f"Author: {commit.get('author', {}).get('name', 'Unknown')}")
                ui.display_info(
                    f"Date: {commit.get('author', {}).get('date', 'Unknown')}")
                ui.display_link(item.get("html_url", ""))
                ui.console.print("")

        elif action == "topics":
            # Search for topics
            topic_results, metadata = await search_topics(
                client,
                query,
                max_results=limit
            )

            ui.display_heading(f"Topics Search: {query}")
            ui.display_info(f"Found {metadata['total_count']} topics")

            table = ui.create_table(
                "Name",
                "Description",
                "Created By",
                title=f"Results ({len(results)} of {metadata['total_count']})"
            )

            for item in topic_results:
                table.add_row(
                    item.get("name", ""),
                    item.get("description", "") or "",
                    item.get("created_by", "") or "GitHub"
                )

            ui.console.print(table)

        else:
            ui.display_error(f"Unknown search action: {action}")
            ui.display_info(
                "Available search types: repos, code, users, issues, commits, topics")

    except APIError as e:
        ui.display_error(f"Search error: {str(e)}")
    except ValidationError as e:
        ui.display_error(f"Invalid search parameters: {str(e)}")
