"""
Unit tests for the main CLI entry point.

Tests the command-line interface, argument parsing, and command dispatch.
"""

import pytest
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from argparse import Namespace

from github_cli.__main__ import (
    main,
    _handle_command,
    _handle_auth_command,
    _setup_auth_parser,
    _setup_repo_parser,
    _setup_pr_parser,
    application_context
)
from github_cli.auth.authenticator import Authenticator
from github_cli.api.client import GitHubClient
from github_cli.ui.terminal import TerminalUI
from github_cli.utils.config import Config
from github_cli.utils.exceptions import AuthenticationError


@pytest.mark.unit
class TestMainEntryPoint:
    """Test cases for main CLI entry point."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_authenticator = Mock(spec=Authenticator)
        self.mock_client = Mock(spec=GitHubClient)
        self.mock_ui = Mock(spec=TerminalUI)

    @pytest.mark.asyncio
    async def test_application_context_manager(self):
        """Test application context manager initialization."""
        with patch('github_cli.__main__.Config') as mock_config_class, \
             patch('github_cli.__main__.Authenticator') as mock_auth_class, \
             patch('github_cli.__main__.GitHubClient') as mock_client_class, \
             patch('github_cli.__main__.TerminalUI') as mock_ui_class:
            
            mock_config = Mock()
            mock_authenticator = Mock()
            mock_client = Mock()
            mock_ui = Mock()
            
            mock_config_class.return_value = mock_config
            mock_auth_class.return_value = mock_authenticator
            mock_client_class.return_value = mock_client
            mock_ui_class.return_value = mock_ui
            
            # Mock async context manager
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            async with application_context() as (config, authenticator, client, ui):
                assert config == mock_config
                assert authenticator == mock_authenticator
                assert client == mock_client
                assert ui == mock_ui

    @pytest.mark.asyncio
    async def test_main_with_no_args_authenticated(self):
        """Test main function with no arguments when authenticated."""
        with patch('sys.argv', ['github-cli']), \
             patch('github_cli.__main__.application_context') as mock_context, \
             patch('github_cli.__main__.Dashboard') as mock_dashboard_class:
            
            # Setup mocks
            mock_authenticator = Mock()
            mock_authenticator.is_authenticated.return_value = True
            mock_client = Mock()
            mock_ui = Mock()
            mock_config = Mock()
            
            mock_context.return_value.__aenter__ = AsyncMock(
                return_value=(mock_config, mock_authenticator, mock_client, mock_ui)
            )
            mock_context.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_dashboard = Mock()
            mock_dashboard.start = AsyncMock()
            mock_dashboard_class.return_value = mock_dashboard
            
            result = await main()
            
            assert result == 0
            mock_dashboard.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_no_args_not_authenticated(self):
        """Test main function with no arguments when not authenticated."""
        with patch('sys.argv', ['github-cli']), \
             patch('github_cli.__main__.application_context') as mock_context, \
             patch('argparse.ArgumentParser.print_help') as mock_print_help:
            
            # Setup mocks
            mock_authenticator = Mock()
            mock_authenticator.is_authenticated.return_value = False
            mock_client = Mock()
            mock_ui = Mock()
            mock_config = Mock()
            
            mock_context.return_value.__aenter__ = AsyncMock(
                return_value=(mock_config, mock_authenticator, mock_client, mock_ui)
            )
            mock_context.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await main()
            
            assert result == 0
            mock_print_help.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_tui_flag(self):
        """Test main function with TUI flag."""
        with patch('sys.argv', ['github-cli', '--tui']), \
             patch('github_cli.ui.tui.core.app.run_tui') as mock_run_tui, \
             patch('threading.Thread') as mock_thread_class:

            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread

            result = await main()

            assert result == 0
            mock_thread.start.assert_called_once()
            mock_thread.join.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_auth_command(self):
        """Test main function with auth command."""
        with patch('sys.argv', ['github-cli', 'auth', 'status']), \
             patch('github_cli.__main__.application_context') as mock_context, \
             patch('github_cli.__main__._handle_command') as mock_handle:
            
            mock_context.return_value.__aenter__ = AsyncMock(
                return_value=(Mock(), Mock(), Mock(), Mock())
            )
            mock_context.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_handle.return_value = 0
            
            result = await main()
            
            assert result == 0
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main function handling keyboard interrupt."""
        with patch('sys.argv', ['github-cli', 'auth', 'status']), \
             patch('github_cli.__main__.application_context') as mock_context, \
             patch('github_cli.__main__.console') as mock_console:
            
            mock_context.side_effect = KeyboardInterrupt()
            
            result = await main()
            
            assert result == 130
            mock_console.print.assert_called_with("\n[yellow]Operation cancelled by user.[/yellow]")

    @pytest.mark.asyncio
    async def test_main_unexpected_exception(self):
        """Test main function handling unexpected exception."""
        with patch('sys.argv', ['github-cli', 'auth', 'status']), \
             patch('github_cli.__main__.application_context') as mock_context, \
             patch('github_cli.__main__.console') as mock_console:
            
            test_error = Exception("Test error")
            mock_context.side_effect = test_error
            
            result = await main()
            
            assert result == 1
            mock_console.print.assert_called_with(f"[red]Unexpected error: {test_error}[/red]")


@pytest.mark.unit
class TestCommandHandling:
    """Test cases for command handling functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_authenticator = Mock(spec=Authenticator)
        self.mock_client = Mock(spec=GitHubClient)
        self.mock_ui = Mock(spec=TerminalUI)

    @pytest.mark.asyncio
    async def test_handle_auth_status_authenticated(self):
        """Test auth status command when authenticated."""
        args = Namespace(action='status')
        
        # Mock user info
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        
        self.mock_authenticator.is_authenticated.return_value = True
        self.mock_authenticator.fetch_user_info = AsyncMock(return_value=mock_user)
        
        with patch('github_cli.__main__.console') as mock_console:
            result = await _handle_auth_command(args, self.mock_authenticator, self.mock_ui)
            
            assert result == 0
            mock_console.print.assert_any_call("[green]�Logged in as testuser[/green]")

    @pytest.mark.asyncio
    async def test_handle_auth_status_not_authenticated(self):
        """Test auth status command when not authenticated."""
        args = Namespace(action='status')
        
        self.mock_authenticator.is_authenticated.return_value = False
        
        with patch('github_cli.__main__.console') as mock_console:
            result = await _handle_auth_command(args, self.mock_authenticator, self.mock_ui)
            
            assert result == 0
            mock_console.print.assert_called_with("[red]�Not logged in.[/red]")

    @pytest.mark.asyncio
    async def test_handle_auth_login(self):
        """Test auth login command."""
        args = Namespace(action='login', scopes=None, sso=None)
        
        self.mock_authenticator.login_interactive = AsyncMock()
        
        result = await _handle_auth_command(args, self.mock_authenticator, self.mock_ui)
        
        assert result == 0
        self.mock_authenticator.login_interactive.assert_called_once_with(scopes=None, sso=None)

    @pytest.mark.asyncio
    async def test_handle_auth_logout(self):
        """Test auth logout command."""
        args = Namespace(action='logout')
        
        self.mock_authenticator.logout = AsyncMock()
        
        result = await _handle_auth_command(args, self.mock_authenticator, self.mock_ui)
        
        assert result == 0
        self.mock_authenticator.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_auth_authentication_error(self):
        """Test auth command with authentication error."""
        args = Namespace(action='login', scopes=None, sso=None)
        
        auth_error = AuthenticationError("Authentication failed")
        self.mock_authenticator.login_interactive = AsyncMock(side_effect=auth_error)
        
        with patch('github_cli.__main__.console') as mock_console:
            result = await _handle_auth_command(args, self.mock_authenticator, self.mock_ui)
            
            assert result == 1
            mock_console.print.assert_called_with("[red]Authentication error: Authentication failed[/red]")


@pytest.mark.unit
class TestArgumentParsers:
    """Test cases for argument parser setup functions."""

    def test_setup_auth_parser(self):
        """Test auth parser setup."""
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        auth_parser = _setup_auth_parser(subparsers)
        
        assert auth_parser is not None
        
        # Test parsing auth commands
        args = parser.parse_args(['auth', 'login'])
        assert args.action == 'login'

    def test_setup_repo_parser(self):
        """Test repo parser setup."""
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        repo_parser = _setup_repo_parser(subparsers)
        
        assert repo_parser is not None
        
        # Test parsing repo commands
        args = parser.parse_args(['repo', 'list'])
        assert args.action == 'list'

    def test_setup_pr_parser(self):
        """Test PR parser setup."""
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        pr_parser = _setup_pr_parser(subparsers)
        
        assert pr_parser is not None
        
        # Test parsing PR commands
        args = parser.parse_args(['pr', 'list', '--state', 'open'])
        assert args.action == 'list'
        assert args.state == 'open'
