"""
GitHub Gists API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError


class GistsAPI:
    """API for working with GitHub Gists"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def list_gists(self, username: Optional[str] = None, per_page: int = 30) -> List[Dict[str, Any]]:
        """List gists for user or authenticated user"""
        if username:
            endpoint = f"users/{username}/gists"
        else:
            endpoint = "gists"

        params = {"per_page": per_page}

        try:
            response = await self.client.get(endpoint, params=params)
            return response
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list gists: {str(e)}")

    async def get_gist(self, gist_id: str) -> Dict[str, Any]:
        """Get a specific gist"""
        endpoint = f"gists/{gist_id}"

        try:
            response = await self.client.get(endpoint)
            return response
        except NotFoundError:
            raise GitHubCLIError(f"Gist {gist_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get gist: {str(e)}")

    async def create_gist(self, files: Dict[str, Dict[str, str]],
                          description: Optional[str] = None,
                          public: bool = True) -> Dict[str, Any]:
        """Create a new gist"""
        endpoint = "gists"

        data: Dict[str, Any] = {
            "files": files,
            "public": public
        }

        if description:
            data["description"] = description

        try:
            response = await self.client.post(endpoint, data=data)
            return response
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create gist: {str(e)}")

    async def update_gist(self, gist_id: str, files: Optional[Dict[str, Dict[str, str]]] = None,
                          description: Optional[str] = None) -> Dict[str, Any]:
        """Update a gist"""
        endpoint = f"gists/{gist_id}"

        data: Dict[str, Any] = {}

        if files:
            data["files"] = files
        if description is not None:
            data["description"] = description

        try:
            response = await self.client.patch(endpoint, data=data)
            return response
        except NotFoundError:
            raise GitHubCLIError(f"Gist {gist_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to update gist: {str(e)}")

    async def delete_gist(self, gist_id: str) -> None:
        """Delete a gist"""
        endpoint = f"gists/{gist_id}"

        try:
            await self.client.delete(endpoint)
        except NotFoundError:
            raise GitHubCLIError(f"Gist {gist_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to delete gist: {str(e)}")

    async def star_gist(self, gist_id: str) -> None:
        """Star a gist"""
        endpoint = f"gists/{gist_id}/star"

        try:
            await self.client.put(endpoint)
        except NotFoundError:
            raise GitHubCLIError(f"Gist {gist_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to star gist: {str(e)}")

    async def unstar_gist(self, gist_id: str) -> None:
        """Unstar a gist"""
        endpoint = f"gists/{gist_id}/star"

        try:
            await self.client.delete(endpoint)
        except NotFoundError:
            raise GitHubCLIError(f"Gist {gist_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to unstar gist: {str(e)}")

    async def is_gist_starred(self, gist_id: str) -> bool:
        """Check if gist is starred"""
        endpoint = f"gists/{gist_id}/star"

        try:
            await self.client.get(endpoint)
            return True
        except NotFoundError:
            return False
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to check gist star status: {str(e)}")


class GistCommands:
    """High-level gist commands"""

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.api = GistsAPI(client, terminal)

    async def list_gists(self, username: Optional[str] = None) -> None:
        """List gists command"""
        try:
            gists = await self.api.list_gists(username)
            self.terminal.display_gists(gists)
        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to list gists: {e}")

    async def view_gist(self, gist_id: str) -> None:
        """View gist command"""
        try:
            gist = await self.api.get_gist(gist_id)
            self.terminal.display_gist_detail(gist)
        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to view gist: {e}")

    async def create_gist_from_file(self, file_path: str, description: Optional[str] = None,
                                    public: bool = True) -> None:
        """Create gist from file"""
        import os
        from pathlib import Path

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                self.terminal.display_error(f"File not found: {file_path}")
                return

            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()

            files = {
                file_path_obj.name: {
                    "content": content
                }
            }

            gist = await self.api.create_gist(files, description, public)
            self.terminal.display_success(f"Created gist: {gist['html_url']}")

        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to create gist: {e}")
        except OSError as e:
            self.terminal.display_error(f"File error: {e}")


# Add display methods to TerminalUI if they don't exist
def _add_gist_methods_to_terminal():
    """Add gist display methods to TerminalUI class"""
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import box

    def display_gists(self, gists: List[Dict[str, Any]]) -> None:
        """Display a list of gists"""
        if not gists:
            self.display_info("No gists found")
            return

        table = Table(title="Gists", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Files", style="yellow")
        table.add_column("Public", style="green")
        table.add_column("Created", style="blue")

        for gist in gists:
            files_count = len(gist.get("files", {}))
            created_at = gist.get("created_at", "").split("T")[0]
            public_status = "Yes" if gist.get("public", False) else "No"
            description = gist.get("description", "No description")[:50]

            table.add_row(
                gist["id"][:8],
                description,
                str(files_count),
                public_status,
                created_at
            )

        self.console.print(table)

    def display_gist_detail(self, gist: Dict[str, Any]) -> None:
        """Display detailed gist information"""
        # Gist header
        header = f"Gist: {gist['id']}"
        if gist.get("description"):
            header += f" - {gist['description']}"

        panel_content = []
        panel_content.append(f"Owner: {gist['owner']['login']}")
        panel_content.append(
            f"Public: {'Yes' if gist.get('public', False) else 'No'}")
        panel_content.append(
            f"Created: {gist.get('created_at', '').split('T')[0]}")
        panel_content.append(
            f"Updated: {gist.get('updated_at', '').split('T')[0]}")
        panel_content.append(f"URL: {gist.get('html_url', '')}")

        self.console.print(Panel("\n".join(panel_content),
                           title=header, box=box.ROUNDED))

        # Display files
        for filename, file_info in gist.get("files", {}).items():
            content = file_info.get("content", "")
            language = file_info.get("language", "text").lower()

            syntax = Syntax(content, language,
                            theme="monokai", line_numbers=True)
            self.console.print(Panel(syntax, title=filename, box=box.ROUNDED))

    # Add methods to TerminalUI class
    TerminalUI.display_gists = display_gists
    TerminalUI.display_gist_detail = display_gist_detail


# Initialize the methods
_add_gist_methods_to_terminal()
