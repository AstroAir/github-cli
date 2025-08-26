"""
GitHub Projects API module
"""

import asyncio
from typing import List, Dict, Any, Optional, Union, cast
from datetime import datetime

from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.exceptions import GitHubCLIError, NotFoundError


class ProjectsAPI:
    """API for working with GitHub Projects"""

    def __init__(self, client: GitHubClient, ui: Optional[TerminalUI] = None):
        self.client = client
        self.ui = ui

    async def list_repo_projects(self, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """List projects for a repository"""
        endpoint = f"repos/{repo}/projects"
        params = {"state": state}

        try:
            response = await self.client.get(endpoint, params=params)
            return cast(List[Dict[str, Any]], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list projects: {str(e)}")

    async def list_org_projects(self, org: str, state: str = "open") -> List[Dict[str, Any]]:
        """List projects for an organization"""
        endpoint = f"orgs/{org}/projects"
        params = {"state": state}

        try:
            response = await self.client.get(endpoint, params=params)
            return cast(List[Dict[str, Any]], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to list organization projects: {str(e)}")

    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get a specific project"""
        endpoint = f"projects/{project_id}"

        try:
            response = await self.client.get(endpoint)
            return cast(Dict[str, Any], response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Project {project_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to get project: {str(e)}")

    async def create_repo_project(self, repo: str, name: str, body: Optional[str] = None) -> Dict[str, Any]:
        """Create a new repository project"""
        endpoint = f"repos/{repo}/projects"

        data: Dict[str, Any] = {"name": name}
        if body:
            data["body"] = body

        try:
            response = await self.client.post(endpoint, data=data)
            return cast(Dict[str, Any], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create project: {str(e)}")

    async def create_org_project(self, org: str, name: str, body: Optional[str] = None) -> Dict[str, Any]:
        """Create a new organization project"""
        endpoint = f"orgs/{org}/projects"

        data: Dict[str, Any] = {"name": name}
        if body:
            data["body"] = body

        try:
            response = await self.client.post(endpoint, data=data)
            return cast(Dict[str, Any], response.data)
        except GitHubCLIError as e:
            raise GitHubCLIError(
                f"Failed to create organization project: {str(e)}")

    async def update_project(self, project_id: int, name: Optional[str] = None,
                             body: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """Update a project"""
        endpoint = f"projects/{project_id}"

        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if body is not None:
            data["body"] = body
        if state:
            data["state"] = state

        try:
            response = await self.client.patch(endpoint, data=data)
            return cast(Dict[str, Any], response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Project {project_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to update project: {str(e)}")

    async def delete_project(self, project_id: int) -> None:
        """Delete a project"""
        endpoint = f"projects/{project_id}"

        try:
            await self.client.delete(endpoint)
        except NotFoundError:
            raise GitHubCLIError(f"Project {project_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to delete project: {str(e)}")

    async def list_project_columns(self, project_id: int) -> List[Dict[str, Any]]:
        """List columns in a project"""
        endpoint = f"projects/{project_id}/columns"

        try:
            response = await self.client.get(endpoint)
            return cast(List[Dict[str, Any]], response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Project {project_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list project columns: {str(e)}")

    async def create_project_column(self, project_id: int, name: str) -> Dict[str, Any]:
        """Create a new project column"""
        endpoint = f"projects/{project_id}/columns"

        data = {"name": name}

        try:
            response = await self.client.post(endpoint, data=data)
            return cast(Dict[str, Any], response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Project {project_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to create project column: {str(e)}")

    async def list_column_cards(self, column_id: int) -> List[Dict[str, Any]]:
        """List cards in a project column"""
        endpoint = f"projects/columns/{column_id}/cards"

        try:
            response = await self.client.get(endpoint)
            return cast(List[Dict[str, Any]], response.data)
        except NotFoundError:
            raise GitHubCLIError(f"Column {column_id} not found")
        except GitHubCLIError as e:
            raise GitHubCLIError(f"Failed to list column cards: {str(e)}")


class ProjectCommands:
    """High-level project commands"""

    def __init__(self, client: GitHubClient, terminal: TerminalUI):
        self.client = client
        self.terminal = terminal
        self.api = ProjectsAPI(client, terminal)

    async def list_projects(self, repo: Optional[str] = None, org: Optional[str] = None) -> None:
        """List projects command"""
        try:
            if repo:
                projects = await self.api.list_repo_projects(repo)
            elif org:
                projects = await self.api.list_org_projects(org)
            else:
                self.terminal.display_error(
                    "Must specify either --repo or --org")
                return

            # type: ignore[attr-defined]
            self.terminal.display_projects(projects)
        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to list projects: {e}")

    async def view_project(self, project_id: int) -> None:
        """View project command"""
        try:
            project = await self.api.get_project(project_id)
            columns = await self.api.list_project_columns(project_id)
            self.terminal.display_project_detail(
                project, columns)  # type: ignore[attr-defined]
        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to view project: {e}")

    async def create_project(self, repo: Optional[str] = None, org: Optional[str] = None,
                             name: str = "", body: Optional[str] = None) -> None:
        """Create project command"""
        try:
            if not name:
                self.terminal.display_error("Project name is required")
                return

            if repo:
                project = await self.api.create_repo_project(repo, name, body)
            elif org:
                project = await self.api.create_org_project(org, name, body)
            else:
                self.terminal.display_error(
                    "Must specify either --repo or --org")
                return

            self.terminal.display_success(
                f"Created project: {project['name']} ({project['id']})")
        except GitHubCLIError as e:
            self.terminal.display_error(f"Failed to create project: {e}")


# Add display methods to TerminalUI
def _add_project_methods_to_terminal() -> None:
    """Add project display methods to TerminalUI class"""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box

    def display_projects(self: Any, projects: List[Dict[str, Any]]) -> None:
        """Display a list of projects"""
        if not projects:
            self.display_info("No projects found")
            return

        table = Table(title="Projects", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("State", style="yellow")
        table.add_column("Created", style="blue")
        table.add_column("Updated", style="blue")

        for project in projects:
            created_at = project.get("created_at", "").split("T")[0]
            updated_at = project.get("updated_at", "").split("T")[0]

            table.add_row(
                str(project.get("id", "")),
                project.get("name", ""),
                project.get("state", ""),
                created_at,
                updated_at
            )

        self.console.print(table)

    def display_project_detail(self: Any, project: Dict[str, Any], columns: List[Dict[str, Any]]) -> None:
        """Display detailed project information"""
        # Project header
        header = f"Project: {project.get('name', 'Unknown')}"

        panel_content = []
        panel_content.append(f"ID: {project.get('id', '')}")
        panel_content.append(f"State: {project.get('state', '')}")
        panel_content.append(
            f"Created: {project.get('created_at', '').split('T')[0]}")
        panel_content.append(
            f"Updated: {project.get('updated_at', '').split('T')[0]}")
        if project.get("body"):
            panel_content.append(f"Description: {project['body']}")
        if project.get("html_url"):
            panel_content.append(f"URL: {project['html_url']}")

        self.console.print(Panel("\n".join(panel_content),
                           title=header, box=box.ROUNDED))

        # Display columns
        if columns:
            table = Table(title="Project Columns", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Created", style="blue")
            table.add_column("Updated", style="blue")

            for column in columns:
                created_at = column.get("created_at", "").split("T")[0]
                updated_at = column.get("updated_at", "").split("T")[0]

                table.add_row(
                    str(column.get("id", "")),
                    column.get("name", ""),
                    created_at,
                    updated_at
                )

            self.console.print(table)

    # Add methods to TerminalUI class
    # type: ignore[attr-defined]
    TerminalUI.display_projects = display_projects
    # type: ignore[attr-defined]
    TerminalUI.display_project_detail = display_project_detail


# Initialize the methods
_add_project_methods_to_terminal()
