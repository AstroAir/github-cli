"""
Enhanced error handling and user feedback patterns for GitHub CLI TUI.

This module provides utilities for displaying user-friendly error messages,
retry mechanisms, and contextual feedback in the terminal interface.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar, ParamSpec
from contextlib import asynccontextmanager

from textual.app import App
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, LoadingIndicator, Static, ProgressBar
from loguru import logger

from github_cli.utils.exceptions import (
    GitHubCLIError, APIError, NetworkError, AuthenticationError,
    RateLimitError, TimeoutError, NotFoundError, ValidationError
)

T = TypeVar('T')
P = ParamSpec('P')


class ErrorDetailScreen(ModalScreen[None]):
    """Modal screen for displaying detailed error information."""

    def __init__(self, error: GitHubCLIError, show_technical_details: bool = False) -> None:
        super().__init__()
        self.error = error
        self.show_technical_details = show_technical_details

    def compose(self) -> Any:
        with Container(id="error-modal", classes="error-modal"):
            yield Static("⚠️ Error Details", id="error-title", classes="error-title")

            # Main error message
            yield Static(str(self.error), id="error-message", classes="error-message")

            # Contextual information
            if self.error.context:
                yield Static("Context Information:", classes="error-section-title")
                for key, value in self.error.context.items():
                    yield Label(f"{key}: {value}", classes="error-context-item")

            # Specific error type information
            yield Static(f"Error Type: {self.error.__class__.__name__}", classes="error-type")

            # Technical details (if enabled)
            if self.show_technical_details and self.error.cause:
                yield Static("Technical Details:", classes="error-section-title")
                yield Static(str(self.error.cause), classes="error-technical")

            # Action buttons
            with Horizontal(classes="error-actions"):
                yield Button("📋 Copy Error", id="copy-error", variant="primary")
                yield Button("🔄 Retry", id="retry-action", variant="success")
                yield Button("❌ Close", id="close-error", variant="error")

    def action_copy_error(self) -> None:
        """Copy error details to clipboard."""
        try:
            import pyperclip
            error_text = f"Error: {self.error}\nType: {self.error.__class__.__name__}\nContext: {self.error.context}"
            if self.error.cause:
                error_text += f"\nCause: {self.error.cause}"
            pyperclip.copy(error_text)
            self.app.notify("Error details copied to clipboard",
                            severity="information")
        except ImportError:
            self.app.notify(
                "pyperclip not available for clipboard support", severity="warning")
        except Exception as e:
            self.app.notify(f"Failed to copy error: {e}", severity="error")

    def action_close_error(self) -> None:
        """Close the error dialog."""
        self.dismiss()

    def action_retry_action(self) -> None:
        """Signal that the user wants to retry the failed operation."""
        self.dismiss("retry")  # type: ignore


class RetryIndicatorWidget(Container):
    """Widget showing retry progress with countdown and cancel option."""

    def __init__(self, attempt: int, max_attempts: int, delay: float) -> None:
        super().__init__()
        self.attempt = attempt
        self.max_attempts = max_attempts
        self.delay = delay
        self.cancelled = False

    def compose(self) -> Any:
        yield Static(f"Retry {self.attempt}/{self.max_attempts}", classes="retry-title")
        yield ProgressBar(total=int(self.delay), show_eta=True, id="retry-progress")
        yield Button("Cancel", id="cancel-retry", variant="error")

    async def start_countdown(self) -> bool:
        """Start countdown and return True if not cancelled."""
        progress_bar = self.query_one("#retry-progress", ProgressBar)

        for i in range(int(self.delay)):
            if self.cancelled:
                return False
            progress_bar.advance(1)
            await asyncio.sleep(1)

        return not self.cancelled

    def action_cancel_retry(self) -> None:
        """Cancel the retry operation."""
        self.cancelled = True


class TUIErrorHandler:
    """Enhanced error handler for TUI applications with user-friendly feedback."""

    def __init__(self, app: App) -> None:
        self.app = app
        self.retry_config = {
            'max_attempts': 3,
            'base_delay': 1.0,
            'exponential_backoff': True,
            'show_progress': True
        }

    def get_user_friendly_message(self, error: GitHubCLIError) -> str:
        """Convert technical errors into user-friendly messages."""
        if isinstance(error, AuthenticationError):
            return "❌ Authentication failed. Please check your GitHub token and try logging in again."

        elif isinstance(error, RateLimitError):
            reset_time = error.reset_time
            remaining = error.remaining
            if reset_time:
                return f"⏳ GitHub API rate limit exceeded. Resets at {reset_time}. Remaining: {remaining}"
            return "⏳ GitHub API rate limit exceeded. Please wait before making more requests."

        elif isinstance(error, TimeoutError):
            timeout = error.get_context('timeout_duration', 'unknown')
            return f"⏰ Request timed out after {timeout} seconds. Please check your connection and try again."

        elif isinstance(error, NotFoundError):
            resource_type = error.get_context('resource_type', 'resource')
            resource_id = error.get_context('resource_id', '')
            return f"🔍 {resource_type.title()} not found: {resource_id}. Please check the name and your permissions."

        elif isinstance(error, ValidationError):
            field_name = error.get_context('field_name', 'field')
            return f"📝 Invalid {field_name}. Please check the format and try again."

        elif isinstance(error, NetworkError):
            return "🌐 Network error occurred. Please check your internet connection and try again."

        elif isinstance(error, APIError):
            if error.status_code == 403:
                return "🚫 Access denied. You may not have permission to perform this action."
            elif error.status_code == 500:
                return "🛠️ GitHub server error. Please try again in a few moments."
            elif error.status_code >= 400:
                return f"⚠️ API error ({error.status_code}). Please check your request and try again."

        # Fallback for unknown errors
        return f"❓ An unexpected error occurred: {str(error)}"

    def get_suggested_actions(self, error: GitHubCLIError) -> list[str]:
        """Get suggested actions for resolving the error."""
        actions = []

        if isinstance(error, AuthenticationError):
            actions.extend([
                "Run 'github-cli auth login' to authenticate",
                "Check if your token has expired",
                "Verify your token has the required scopes"
            ])

        elif isinstance(error, RateLimitError):
            actions.extend([
                "Wait for the rate limit to reset",
                "Use authentication to get higher rate limits",
                "Reduce the frequency of API calls"
            ])

        elif isinstance(error, TimeoutError):
            actions.extend([
                "Check your internet connection",
                "Try again with a longer timeout",
                "Use a VPN if GitHub is blocked"
            ])

        elif isinstance(error, NotFoundError):
            actions.extend([
                "Verify the resource name is correct",
                "Check if you have access permissions",
                "Ensure the repository/resource exists"
            ])

        elif isinstance(error, NetworkError):
            actions.extend([
                "Check your internet connection",
                "Try again in a few moments",
                "Check GitHub's status at status.github.com"
            ])

        return actions

    async def show_error_dialog(self, error: GitHubCLIError, show_technical: bool = False) -> str | None:
        """Show detailed error dialog and return user choice."""
        try:
            # type: ignore[func-returns-value]
            result = await self.app.push_screen(ErrorDetailScreen(error, show_technical))
            return result
        except Exception as e:
            logger.error(f"Failed to show error dialog: {e}")
            return None

    def notify_error(self, error: GitHubCLIError, duration: float = 5.0) -> None:
        """Show error notification with user-friendly message."""
        message = self.get_user_friendly_message(error)
        self.app.notify(message, severity="error", timeout=duration)

    def notify_with_suggestions(self, error: GitHubCLIError) -> None:
        """Show error with suggested actions."""
        message = self.get_user_friendly_message(error)
        suggestions = self.get_suggested_actions(error)

        if suggestions:
            suggestion_text = "\n💡 Suggestions:\n" + \
                "\n".join(f"  • {action}" for action in suggestions[:3])
            full_message = f"{message}{suggestion_text}"
        else:
            full_message = message

        self.app.notify(full_message, severity="error", timeout=10.0)

    @asynccontextmanager
    async def error_boundary(self, operation_name: str = "operation") -> Any:
        """Context manager for handling errors with automatic user feedback."""
        try:
            yield
        except GitHubCLIError as e:
            logger.error(f"Error in {operation_name}: {e}")
            self.notify_with_suggestions(e)

            # For certain error types, show detailed dialog
            if isinstance(e, (AuthenticationError, RateLimitError)):
                await self.show_error_dialog(e)
        except Exception as e:
            logger.exception(f"Unexpected error in {operation_name}")
            github_error = GitHubCLIError(
                f"Unexpected error in {operation_name}",
                cause=e,
                context={"operation": operation_name}
            )
            self.notify_error(github_error)

    def configure_retry(self, max_attempts: int = 3, base_delay: float = 1.0,
                        exponential_backoff: bool = True, show_progress: bool = True) -> None:
        """Configure retry behavior."""
        self.retry_config.update({
            'max_attempts': max_attempts,
            'base_delay': base_delay,
            'exponential_backoff': exponential_backoff,
            'show_progress': show_progress
        })

    async def with_retry(self,
                         operation: Callable[P, T],
                         *args: P.args,
                         **kwargs: P.kwargs) -> T:
        """Execute operation with retry logic and user feedback."""
        last_error: GitHubCLIError | None = None

        for attempt in range(1, int(self.retry_config['max_attempts']) + 1):
            try:
                if attempt > 1:
                    # Calculate delay
                    if self.retry_config['exponential_backoff']:
                        delay = self.retry_config['base_delay'] * \
                            (2 ** (attempt - 2))
                    else:
                        delay = self.retry_config['base_delay']

                    # Show retry indicator if configured
                    if self.retry_config['show_progress']:
                        retry_widget = RetryIndicatorWidget(
                            attempt, int(self.retry_config['max_attempts']), delay)
                        # Mount retry widget temporarily
                        self.app.mount(retry_widget)
                        try:
                            should_continue = await retry_widget.start_countdown()
                            if not should_continue:
                                raise asyncio.CancelledError(
                                    "Retry cancelled by user")
                        finally:
                            retry_widget.remove()
                    else:
                        await asyncio.sleep(delay)

                # Execute the operation
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)  # type: ignore
                else:
                    return operation(*args, **kwargs)

            except (NetworkError, TimeoutError, APIError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {e}")

                # Don't retry for certain errors
                if isinstance(e, (AuthenticationError, NotFoundError, ValidationError)):
                    break

                if attempt == self.retry_config['max_attempts']:
                    break

                # Show retry notification
                self.app.notify(
                    f"Attempt {attempt} failed, retrying...", timeout=2.0)

            except Exception as e:
                # Don't retry for unexpected errors
                last_error = GitHubCLIError("Unexpected error", cause=e)
                break

        # All attempts failed
        if last_error:
            self.notify_with_suggestions(last_error)
            raise last_error
        else:
            raise GitHubCLIError("Operation failed after all retry attempts")


# Factory function for easy integration
def create_error_handler(app: App) -> TUIErrorHandler:
    """Create and configure an error handler for the given app."""
    return TUIErrorHandler(app)


# Decorator for automatic error handling
def handle_errors(error_handler: TUIErrorHandler, operation_name: str = "operation") -> Any:
    """Decorator for automatic error handling with user feedback."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async with error_handler.error_boundary(operation_name):
                return await func(*args, **kwargs)  # type: ignore

        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # For sync functions, we can't use async context manager
            try:
                return func(*args, **kwargs)
            except GitHubCLIError as e:
                error_handler.notify_with_suggestions(e)
                raise
            except Exception as e:
                github_error = GitHubCLIError(
                    f"Unexpected error in {operation_name}",
                    cause=e,
                    context={"operation": operation_name}
                )
                error_handler.notify_error(github_error)
                raise github_error

        # type: ignore
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
