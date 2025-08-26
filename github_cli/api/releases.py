"""
GitHub Releases API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, cast
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.models.release import Release
from github_cli.utils.exceptions import APIError, ValidationError


async def list_releases(
    client: GitHubClient,
    owner: str,
    repo: str,
    per_page: int = 30,
    max_pages: int = 3
) -> List[Release]:
    """
    List releases for a repository

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        per_page: Number of results per page
        max_pages: Maximum number of pages to fetch

    Returns:
        List of Release objects
    """
    response = await client.paginated_request(
        "GET",
        f"/repos/{owner}/{repo}/releases",
        params={"per_page": per_page},
        max_pages=max_pages
    )

    return [Release.from_json(item) for item in response]


async def get_release(
    client: GitHubClient,
    owner: str,
    repo: str,
    release_id: Union[int, str]
) -> Release:
    """
    Get a specific release by ID or tag

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        release_id: Release ID or tag name

    Returns:
        Release object
    """
    try:
        if isinstance(release_id, int) or release_id.isdigit():
            # Get by ID
            response = await client.get(f"/repos/{owner}/{repo}/releases/{release_id}")
        else:
            # Get by tag
            response = await client.get(f"/repos/{owner}/{repo}/releases/tags/{release_id}")

        return Release.from_json(response.data)
    except APIError as e:
        if e.status_code == 404:
            raise ValueError(f"Release not found: {release_id}")
        raise


async def get_latest_release(
    client: GitHubClient,
    owner: str,
    repo: str
) -> Release:
    """
    Get the latest release for a repository

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name

    Returns:
        Release object
    """
    try:
        response = await client.get(f"/repos/{owner}/{repo}/releases/latest")
        return Release.from_json(response.data)
    except APIError as e:
        if e.status_code == 404:
            raise ValueError(f"No releases found for {owner}/{repo}")
        raise


async def create_release(
    client: GitHubClient,
    owner: str,
    repo: str,
    tag_name: str,
    target_commitish: Optional[str] = None,
    name: Optional[str] = None,
    body: Optional[str] = None,
    draft: bool = False,
    prerelease: bool = False,
    make_latest: Optional[bool] = None
) -> Release:
    """
    Create a new release

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        tag_name: Tag name for the release
        target_commitish: Target branch/commit (defaults to default branch)
        name: Release title
        body: Release description
        draft: Whether this is a draft release
        prerelease: Whether this is a pre-release
        make_latest: Set as latest release (true, false, or "legacy")

    Returns:
        Created Release object
    """
    data = {
        "tag_name": tag_name,
        "draft": draft,
        "prerelease": prerelease
    }

    if target_commitish:
        data["target_commitish"] = target_commitish

    if name:
        data["name"] = name

    if body:
        data["body"] = body

    if make_latest is not None:
        if make_latest is True:
            data["make_latest"] = "true"
        elif make_latest is False:
            data["make_latest"] = "false"

    response = await client.post(f"/repos/{owner}/{repo}/releases", data=data)
    return Release.from_json(response.data)


async def update_release(
    client: GitHubClient,
    owner: str,
    repo: str,
    release_id: Union[int, str],
    tag_name: Optional[str] = None,
    target_commitish: Optional[str] = None,
    name: Optional[str] = None,
    body: Optional[str] = None,
    draft: Optional[bool] = None,
    prerelease: Optional[bool] = None,
    make_latest: Optional[bool] = None
) -> Release:
    """
    Update an existing release

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        release_id: Release ID or tag name
        tag_name: New tag name
        target_commitish: New target branch/commit
        name: New release title
        body: New release description
        draft: Whether this is a draft release
        prerelease: Whether this is a pre-release
        make_latest: Set as latest release (true, false, or "legacy")

    Returns:
        Updated Release object
    """
    # Get the release ID if a tag was provided
    if not isinstance(release_id, int) and not release_id.isdigit():
        release = await get_release(client, owner, repo, release_id)
        release_id = release.id

    data = {}

    if tag_name:
        data["tag_name"] = tag_name

    if target_commitish:
        data["target_commitish"] = target_commitish

    if name:
        data["name"] = name

    if body:
        data["body"] = body

    if draft is not None:
        data["draft"] = str(draft).lower()

    if prerelease is not None:
        data["prerelease"] = str(prerelease).lower()

    if make_latest is not None:
        if make_latest is True:
            data["make_latest"] = "true"
        elif make_latest is False:
            data["make_latest"] = "false"

    if not data:
        raise ValidationError("No update parameters provided")

    response = await client.patch(f"/repos/{owner}/{repo}/releases/{release_id}", data=data)
    return Release.from_json(response.data)


async def delete_release(
    client: GitHubClient,
    owner: str,
    repo: str,
    release_id: Union[int, str]
) -> bool:
    """
    Delete a release

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        release_id: Release ID or tag name

    Returns:
        True if successful
    """
    # Get the release ID if a tag was provided
    if not isinstance(release_id, int) and not release_id.isdigit():
        release = await get_release(client, owner, repo, release_id)
        release_id = release.id

    try:
        await client.delete(f"/repos/{owner}/{repo}/releases/{release_id}")
        return True
    except APIError:
        return False


async def upload_release_asset(
    client: GitHubClient,
    owner: str,
    repo: str,
    release_id: Union[int, str],
    file_path: str,
    label: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload an asset to a release

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        release_id: Release ID or tag name
        file_path: Path to the file to upload
        label: Label for the asset

    Returns:
        Asset data
    """
    # Get the release if a tag was provided
    if not isinstance(release_id, int) and not release_id.isdigit():
        release = await get_release(client, owner, repo, release_id)
        upload_url = release.upload_url
    else:
        release = await get_release(client, owner, repo, release_id)
        upload_url = release.upload_url

    # Parse the upload URL (remove template params)
    if "{" in upload_url:
        upload_url = upload_url.split("{")[0]

    # TODO: Implement file upload logic (requires multipart form data)
    # This is a placeholder for now
    raise NotImplementedError("File upload not yet implemented")


async def list_release_assets(
    client: GitHubClient,
    owner: str,
    repo: str,
    release_id: Union[int, str]
) -> List[Dict[str, Any]]:
    """
    List assets for a release

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        release_id: Release ID or tag name

    Returns:
        List of asset data
    """
    # Get the release ID if a tag was provided
    if not isinstance(release_id, int) and not release_id.isdigit():
        release = await get_release(client, owner, repo, release_id)
        release_id = release.id

    response = await client.get(
        f"/repos/{owner}/{repo}/releases/{release_id}/assets"
    )

    return cast(List[Dict[str, Any]], response.data)


async def delete_release_asset(
    client: GitHubClient,
    owner: str,
    repo: str,
    asset_id: int
) -> bool:
    """
    Delete a release asset

    Args:
        client: The GitHub client
        owner: Repository owner
        repo: Repository name
        asset_id: Asset ID

    Returns:
        True if successful
    """
    try:
        await client.delete(f"/repos/{owner}/{repo}/releases/assets/{asset_id}")
        return True
    except APIError:
        return False


# Handler function for CLI commands
async def handle_releases_command(args: Dict[str, Any], client: GitHubClient, ui: Any) -> None:
    """Handle release commands from the CLI"""
    action = args.get("releases_action")

    try:
        if action == "list":
            repo = args.get("repo")
            if not repo or "/" not in repo:
                ui.display_error("Repository required in format owner/repo")
                return

            owner, repo_name = repo.split("/", 1)

            releases = await list_releases(client, owner, repo_name)

            if not releases:
                ui.display_info(f"No releases found for {repo}")
                return

            ui.display_heading(f"Releases for {repo}")

            table = ui.create_table(
                "Tag",
                "Name",
                "Published",
                "Downloads",
                "Status"
            )

            for release in releases:
                status = []
                if release.draft:
                    status.append("Draft")
                if release.prerelease:
                    status.append("Pre-release")
                if not release.draft and not release.prerelease:
                    status.append("Release")

                published = release.published_date.strftime(
                    "%Y-%m-%d") if release.published_date else "Unpublished"

                table.add_row(
                    release.tag_name,
                    release.name or "(No title)",
                    published,
                    str(release.download_count),
                    ", ".join(status)
                )

            ui.console.print(table)

        elif action == "view":
            repo = args.get("repo")
            tag = args.get("tag")

            if not repo or "/" not in repo:
                ui.display_error("Repository required in format owner/repo")
                return

            owner, repo_name = repo.split("/", 1)

            if not tag:
                # Get latest release
                try:
                    release = await get_latest_release(client, owner, repo_name)
                except ValueError as e:
                    ui.display_error(str(e))
                    return
            else:
                # Get specific release
                try:
                    release = await get_release(client, owner, repo_name, tag)
                except ValueError as e:
                    ui.display_error(str(e))
                    return

            # Display release details
            ui.display_heading(f"{release.name or release.tag_name}")
            ui.display_info(f"Tag: {release.tag_name}")

            # Display status
            status = []
            if release.draft:
                status.append("Draft")
            if release.prerelease:
                status.append("Pre-release")

            if status:
                ui.display_info(f"Status: {', '.join(status)}")

            # Display dates
            if release.published_date:
                ui.display_info(
                    f"Published: {release.published_date.strftime('%Y-%m-%d %H:%M:%S')}")
            ui.display_info(
                f"Created: {release.created_date.strftime('%Y-%m-%d %H:%M:%S')}")

            # Display author
            ui.display_info(f"Author: {release.author_name}")

            # Display body
            if release.body:
                ui.console.print("\n")
                ui.display_markdown(release.body)

            # Display assets
            if release.assets:
                ui.console.print("\n")
                ui.display_heading("Assets", level=2)

                assets_table = ui.create_table(
                    "Name",
                    "Size",
                    "Downloads",
                    "Created At"
                )

                for asset in release.assets:
                    size = f"{asset.get('size', 0) / 1024:.1f} KB"
                    created_at = datetime.fromisoformat(
                        asset.get('created_at', '').replace('Z', '+00:00')).strftime('%Y-%m-%d')

                    assets_table.add_row(
                        asset.get('name', 'Unknown'),
                        size,
                        str(asset.get('download_count', 0)),
                        created_at
                    )

                ui.console.print(assets_table)

            # Display links
            ui.console.print("\n")
            ui.display_info(f"URL: {release.html_url}")

        elif action == "create":
            repo = args.get("repo")
            tag = args.get("tag")
            name = args.get("name")
            body = args.get("body")
            target = args.get("target")
            draft = args.get("draft", False)
            prerelease = args.get("prerelease", False)

            if not repo or "/" not in repo:
                ui.display_error("Repository required in format owner/repo")
                return

            if not tag:
                ui.display_error("Tag name is required")
                return

            owner, repo_name = repo.split("/", 1)

            # Create release
            release = await create_release(
                client,
                owner,
                repo_name,
                tag_name=tag,
                target_commitish=target,
                name=name,
                body=body,
                draft=draft,
                prerelease=prerelease
            )

            ui.display_success(f"Created release: {release.tag_name}")
            ui.display_info(f"URL: {release.html_url}")

        elif action == "delete":
            repo = args.get("repo")
            tag = args.get("tag")

            if not repo or "/" not in repo:
                ui.display_error("Repository required in format owner/repo")
                return

            if not tag:
                ui.display_error("Tag name or release ID is required")
                return

            owner, repo_name = repo.split("/", 1)

            # Delete release
            success = await delete_release(client, owner, repo_name, tag)

            if success:
                ui.display_success(f"Deleted release: {tag}")
            else:
                ui.display_error(f"Failed to delete release: {tag}")

        else:
            ui.display_error(f"Unknown releases action: {action}")
            ui.display_info("Available actions: list, view, create, delete")

    except APIError as e:
        ui.display_error(f"API error: {str(e)}")
    except Exception as e:
        ui.display_error(f"Error: {str(e)}")
