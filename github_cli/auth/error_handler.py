"""
Authentication-specific error handling for GitHub CLI.

This module provides specialized error handling for authentication flows,
including network errors, token errors, and environment-specific issues.
"""

from __future__ import annotations

import time
from .common import (
    asyncio, dataclass, Enum, Any, Callable, logger,
    Button, Label, Static, ProgressBar, Container, Horizontal, Vertical,
    AuthResult, AuthErrorType, AuthRecoveryAction
)
from typing import Literal, Protocol, runtime_checkable
from contextlib import asynccontextmanager
from textual.app import App
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual.timer import Timer

from github_cli.ui.tui.screens.error import TUIErrorHandler
from github_cli.utils.exceptions import (
    GitHubCLIError, APIError, NetworkError, AuthenticationError,
    RateLimitError, TimeoutError, NotFoundError, ValidationError
)


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    show_progress: bool = True
    cancellable: bool = True


@dataclass(frozen=True, slots=True)
class RetryState:
    """Current state of retry operation."""
    attempt: int
    max_attempts: int
    delay: float
    total_elapsed: float
    error: Exception
    can_cancel: bool = True
    progress_percentage: float = 0.0


@runtime_checkable
class AuthErrorRecoveryStrategy(Protocol):
    """Protocol for authentication error recovery strategies."""

    async def can_handle(self, error: Exception) -> bool:
        """Check if this strategy can handle the given error."""
        ...

    async def recover(self, error: Exception, context: dict[str, Any]) -> AuthRecoveryAction:
        """Attempt to recover from the error."""
        ...

    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly error message."""
        ...

    def get_suggested_actions(self, error: Exception) -> list[str]:
        """Get list of suggested actions for the user."""
        ...


class NetworkErrorRecoveryStrategy:
    """Recovery strategy for network-related authentication errors."""

    async def can_handle(self, error: Exception) -> bool:
        """Check if this is a network error."""
        return isinstance(error, (NetworkError, TimeoutError))

    async def recover(self, error: Exception, context: dict[str, Any]) -> AuthRecoveryAction:
        """Attempt to recover from network errors."""
        if isinstance(error, NetworkError):
            retry_count = error.get_context("retry_count", 0)
            if retry_count < 3:
                return AuthRecoveryAction.RETRY
            else:
                return AuthRecoveryAction.SHOW_HELP

        if isinstance(error, TimeoutError):
            return AuthRecoveryAction.RETRY

        return AuthRecoveryAction.CANCEL

    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly message for network errors."""
        if isinstance(error, TimeoutError):
            timeout = error.get_context("timeout_duration", "unknown")
            return f"🌐 Connection timed out after {timeout} seconds. Please check your internet connection."

        return "🌐 Network error occurred. Please check your internet connection and try again."

    def get_suggested_actions(self, error: Exception) -> list[str]:
        """Get suggested actions for network errors."""
        return [
            "Check your internet connection",
            "Try connecting to a different network",
            "Check if GitHub is accessible at github.com",
            "Verify proxy settings if using a corporate network"
        ]


class TokenErrorRecoveryStrategy:
    """Recovery strategy for token-related authentication errors."""

    async def can_handle(self, error: Exception) -> bool:
        """Check if this is a token error."""
        return isinstance(error, AuthenticationError) or (
            isinstance(error, APIError) and error.status_code in [401, 403]
        )

    async def recover(self, error: Exception, context: dict[str, Any]) -> AuthRecoveryAction:
        """Attempt to recover from token errors."""
        if isinstance(error, AuthenticationError):
            auth_type = error.get_context("auth_type", "")

            if "device_code" in auth_type.lower():
                return AuthRecoveryAction.RESTART_FLOW
            elif "expired" in str(error).lower():
                return AuthRecoveryAction.RESTART_FLOW
            else:
                return AuthRecoveryAction.MANUAL_AUTH

        if isinstance(error, APIError):
            if error.status_code == 401:
                return AuthRecoveryAction.RESTART_FLOW
            elif error.status_code == 403:
                if error.is_rate_limited:
                    return AuthRecoveryAction.WAIT_AND_RETRY
                else:
                    return AuthRecoveryAction.SHOW_HELP

        return AuthRecoveryAction.CANCEL

    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly message for token errors."""
        if isinstance(error, AuthenticationError):
            if "expired" in str(error).lower():
                return "🔑 Your authentication has expired. Please log in again."
            elif "denied" in str(error).lower():
                return "❌ Authentication was denied. You can try again or use manual authentication."
            else:
                return "🔑 Authentication failed. Please check your credentials and try again."

        if isinstance(error, APIError):
            if error.status_code == 401:
                return "🔑 Authentication required. Please log in to continue."
            elif error.status_code == 403:
                # Check if it's rate limited by looking at rate_limit_remaining
                rate_limit_remaining = error.get_context(
                    "rate_limit_remaining")
                if rate_limit_remaining is not None and rate_limit_remaining == 0:
                    return f"⏳ Rate limit exceeded. {rate_limit_remaining} requests remaining."
                else:
                    return "🚫 Access denied. You may not have permission for this action."

        return "🔑 Authentication error occurred. Please try logging in again."

    def get_suggested_actions(self, error: Exception) -> list[str]:
        """Get suggested actions for token errors."""
        if isinstance(error, AuthenticationError):
            return [
                "Restart the authentication flow",
                "Check if you have the required permissions",
                "Try manual authentication if automatic fails",
                "Verify your GitHub account is active"
            ]

        if isinstance(error, APIError) and error.is_rate_limited:
            return [
                "Wait for the rate limit to reset",
                "Use authentication to get higher limits",
                "Reduce the frequency of requests"
            ]

        return [
            "Log in with a valid GitHub account",
            "Check your account permissions",
            "Verify your token hasn't been revoked"
        ]


class EnvironmentErrorRecoveryStrategy:
    """Recovery strategy for environment-specific authentication errors."""

    async def can_handle(self, error: Exception) -> bool:
        """Check if this is an environment error."""
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in [
            "browser", "display", "clipboard", "headless", "x11", "wayland"
        ])

    async def recover(self, error: Exception, context: dict[str, Any]) -> AuthRecoveryAction:
        """Attempt to recover from environment errors."""
        error_msg = str(error).lower()

        if "browser" in error_msg:
            return AuthRecoveryAction.MANUAL_AUTH
        elif "clipboard" in error_msg:
            return AuthRecoveryAction.MANUAL_AUTH
        elif any(term in error_msg for term in ["display", "headless", "x11"]):
            return AuthRecoveryAction.MANUAL_AUTH

        return AuthRecoveryAction.SHOW_HELP

    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly message for environment errors."""
        error_msg = str(error).lower()

        if "browser" in error_msg:
            return "🌐 Cannot open browser automatically. You'll need to open the URL manually."
        elif "clipboard" in error_msg:
            return "📋 Cannot access clipboard. You'll need to copy the URL manually."
        elif "display" in error_msg or "headless" in error_msg:
            return "🖥️ Running in headless environment. Manual authentication required."

        return "⚙️ Environment limitation detected. Manual authentication may be required."

    def get_suggested_actions(self, error: Exception) -> list[str]:
        """Get suggested actions for environment errors."""
        error_msg = str(error).lower()

        if "browser" in error_msg:
            return [
                "Copy the verification URL manually",
                "Open the URL in your browser",
                "Complete authentication in the browser",
                "Return to the CLI to continue"
            ]
        elif "clipboard" in error_msg:
            return [
                "Note down the verification URL",
                "Open the URL in your browser manually",
                "Complete the authentication process"
            ]

        return [
            "Use manual authentication method",
            "Copy URLs and codes manually",
            "Complete authentication in a browser"
        ]


class RetryProgressIndicator(Static):
    """Progress indicator for retry operations with cancel option."""

    retry_state = reactive(None, layout=True)
    is_cancelled = reactive(False)

    def __init__(self, config: RetryConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.cancel_callback: Callable[[], None] | None = None
        self.timer: Timer | None = None
        self.start_time = time.time()

    def compose(self) -> Any:
        """Compose the retry progress indicator."""
        with Vertical():
            yield Label("", id="retry-status")
            if self.config.show_progress:
                yield ProgressBar(id="retry-progress")
            if self.config.cancellable:
                yield Button("Cancel", id="cancel-retry", variant="error")

    def start_retry(self, state: RetryState, cancel_callback: Callable[[], None] | None = None) -> None:
        """Start showing retry progress."""
        self.retry_state = state  # type: ignore[assignment]
        self.cancel_callback = cancel_callback
        self.is_cancelled = False
        self.start_time = time.time()

        # Update display
        self._update_display()

        # Start countdown timer
        if self.config.show_progress:
            self.timer = self.set_interval(0.1, self._update_countdown)

        logger.debug(
            f"Started retry progress for attempt {state.attempt}/{state.max_attempts}")

    def stop_retry(self) -> None:
        """Stop the retry progress indicator."""
        if self.timer:
            self.timer.stop()
            self.timer = None

        self.retry_state = None
        logger.debug("Stopped retry progress indicator")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "cancel-retry" and not self.is_cancelled:
            self.is_cancelled = True
            if self.cancel_callback:
                self.cancel_callback()

            # Update display to show cancellation
            status_label = self.query_one("#retry-status", Label)
            status_label.update("❌ Retry cancelled by user")

            logger.info("Retry cancelled by user")

    def _update_display(self) -> None:
        """Update the retry progress display."""
        if not self.retry_state:
            return

        state = self.retry_state  # type: ignore[unreachable]

        # Update status label
        status_label = self.query_one("#retry-status", Label)
        error_type = type(state.error).__name__
        status_text = f"🔄 Retrying after {error_type} (attempt {state.attempt}/{state.max_attempts})"

        if state.delay > 0:
            remaining = max(0, state.delay - (time.time() - self.start_time))
            status_text += f" - {remaining:.1f}s remaining"

        status_label.update(status_text)

        # Update progress bar if available
        if self.config.show_progress:
            try:
                progress_bar = self.query_one("#retry-progress", ProgressBar)
                if state.delay > 0:
                    elapsed = time.time() - self.start_time
                    progress = min(100, (elapsed / state.delay) * 100)
                    progress_bar.update(progress=progress)
                else:
                    progress_bar.update(progress=state.progress_percentage)
            except Exception:
                # Progress bar not available
                pass

    def _update_countdown(self) -> None:
        """Update countdown display."""
        if self.retry_state and not self.is_cancelled:  # type: ignore[unreachable]
            self._update_display()  # type: ignore[unreachable]


class ExponentialBackoffCalculator:
    """Calculator for exponential backoff delays with jitter."""

    def __init__(self, config: RetryConfig) -> None:
        self.config = config

    def calculate_delay(self, attempt: int, error: Exception | None = None) -> float:
        """Calculate delay for the given attempt number."""
        if not self.config.exponential_backoff:
            return self.config.base_delay

        # Calculate exponential backoff
        delay = self.config.base_delay * (2 ** (attempt - 1))

        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        # Special handling for rate limiting
        if error and hasattr(error, 'retry_after'):
            rate_limit_delay = getattr(error, 'retry_after', 0)
            if rate_limit_delay > 0:
                delay = max(delay, rate_limit_delay)

        return max(0.1, delay)  # type: ignore[no-any-return]

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if we should retry based on attempt count and error type."""
        if attempt >= self.config.max_attempts:
            return False

        # Don't retry certain error types
        if isinstance(error, AuthenticationError):
            error_msg = str(error).lower()
            if "denied" in error_msg or "invalid" in error_msg:
                return False

        # Always retry network and timeout errors
        if isinstance(error, (NetworkError, TimeoutError)):
            return True

        # Retry rate limit errors
        if isinstance(error, (RateLimitError, APIError)) and getattr(error, 'is_rate_limited', False):
            return True

        return True


class RateLimitDetector:
    """Detector for rate limiting with automatic wait handling."""

    def __init__(self) -> None:
        self.rate_limit_history: list[tuple[float, int]] = []

    def detect_rate_limit(self, error: Exception) -> tuple[bool, float]:
        """Detect if error is due to rate limiting and return wait time."""
        is_rate_limited = False
        wait_time = 0.0

        if isinstance(error, RateLimitError):
            is_rate_limited = True
            wait_time = getattr(error, 'retry_after', 60.0)

        elif isinstance(error, APIError):
            if error.status_code == 403 and error.is_rate_limited:
                is_rate_limited = True
                # Try to get retry-after header or rate limit reset time
                retry_after = error.get_context('retry_after')
                rate_limit_reset = error.get_context('rate_limit_reset')

                if retry_after:
                    wait_time = float(retry_after)
                elif rate_limit_reset:
                    wait_time = max(0, rate_limit_reset - time.time())
                else:
                    wait_time = 60.0  # Default wait time

        # Record rate limit event
        if is_rate_limited:
            self.rate_limit_history.append((time.time(), int(wait_time)))
            # Keep only recent history
            cutoff_time = time.time() - 3600  # 1 hour
            self.rate_limit_history = [
                (timestamp, wait) for timestamp, wait in self.rate_limit_history
                if timestamp > cutoff_time
            ]

        return is_rate_limited, wait_time

    def get_recommended_wait_time(self, error: Exception) -> float:
        """Get recommended wait time based on rate limit history."""
        is_rate_limited, base_wait_time = self.detect_rate_limit(error)

        if not is_rate_limited:
            return 0.0

        # If we have recent rate limit history, be more conservative
        recent_rate_limits = [
            wait for timestamp, wait in self.rate_limit_history
            if time.time() - timestamp < 300  # Last 5 minutes
        ]

        if recent_rate_limits:
            # Increase wait time if we've been rate limited recently
            multiplier = min(2.0, 1.0 + len(recent_rate_limits) * 0.2)
            return base_wait_time * multiplier

        return base_wait_time


class AutomaticRetryManager:
    """Manager for automatic retry mechanisms with progress tracking."""

    def __init__(self, app: App, config: RetryConfig | None = None) -> None:
        self.app = app
        self.config = config or RetryConfig()
        self.backoff_calculator = ExponentialBackoffCalculator(self.config)
        self.rate_limit_detector = RateLimitDetector()
        self.progress_indicator: RetryProgressIndicator | None = None
        self.is_cancelled = False

    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str = "operation",
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute operation with automatic retry logic."""
        last_error = None
        self.is_cancelled = False

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Execute the operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                # Success - clean up and return
                if self.progress_indicator:
                    self.progress_indicator.stop_retry()

                logger.info(
                    f"Operation '{operation_name}' succeeded on attempt {attempt}")
                return result

            except Exception as error:
                last_error = error
                logger.warning(
                    f"Operation '{operation_name}' failed on attempt {attempt}: {error}")

                # Check if we should retry
                if not self.backoff_calculator.should_retry(attempt, error):
                    logger.info(
                        f"Not retrying operation '{operation_name}' due to error type")
                    break

                if attempt >= self.config.max_attempts:
                    logger.error(
                        f"Operation '{operation_name}' failed after {attempt} attempts")
                    break

                # Handle rate limiting
                is_rate_limited, wait_time = self.rate_limit_detector.detect_rate_limit(
                    error)
                if is_rate_limited:
                    await self._handle_rate_limit(error, wait_time, attempt)
                    if self.is_cancelled:
                        break
                    continue

                # Calculate retry delay
                delay = self.backoff_calculator.calculate_delay(attempt, error)

                # Show retry progress
                await self._show_retry_progress(
                    RetryState(
                        attempt=attempt,
                        max_attempts=self.config.max_attempts,
                        delay=delay,
                        total_elapsed=0.0,
                        error=error,
                        can_cancel=self.config.cancellable
                    )
                )

                # Wait for retry delay
                await asyncio.sleep(delay)

                if self.is_cancelled:
                    logger.info(
                        f"Operation '{operation_name}' cancelled by user")
                    break

        # All attempts failed or cancelled
        if self.progress_indicator:
            self.progress_indicator.stop_retry()

        if self.is_cancelled:
            raise AuthenticationError(
                f"Operation '{operation_name}' was cancelled by user")
        elif last_error:
            raise AuthenticationError(
                f"Operation '{operation_name}' failed after {self.config.max_attempts} attempts",
                cause=last_error
            )
        else:
            raise AuthenticationError(
                f"Operation '{operation_name}' failed for unknown reasons")

    async def _handle_rate_limit(self, error: Exception, wait_time: float, attempt: int) -> None:
        """Handle rate limiting with user notification and progress."""
        logger.info(
            f"Rate limited, waiting {wait_time}s before retry {attempt}")

        # Show rate limit notification
        self.app.notify(
            f"⏳ Rate limited by GitHub. Waiting {wait_time:.0f} seconds before retry...",
            severity="warning",
            timeout=min(wait_time, 10.0)
        )

        # Show progress indicator for rate limit wait
        if self.config.show_progress:
            await self._show_retry_progress(
                RetryState(
                    attempt=attempt,
                    max_attempts=self.config.max_attempts,
                    delay=wait_time,
                    total_elapsed=0.0,
                    error=error,
                    can_cancel=self.config.cancellable
                )
            )

        # Wait for rate limit to reset
        await asyncio.sleep(wait_time)

    async def _show_retry_progress(self, state: RetryState) -> None:
        """Show retry progress indicator."""
        if not self.config.show_progress:
            return

        # Create progress indicator if needed
        if self.progress_indicator is None:
            self.progress_indicator = RetryProgressIndicator(
                self.config,
                id="retry-progress-indicator"
            )

        # Start progress display
        self.progress_indicator.start_retry(
            state,
            cancel_callback=self._cancel_retry
        )

    def _cancel_retry(self) -> None:
        """Cancel the current retry operation."""
        self.is_cancelled = True
        logger.info("Retry operation cancelled by user")

    def update_config(self, config: RetryConfig) -> None:
        """Update retry configuration."""
        self.config = config
        self.backoff_calculator = ExponentialBackoffCalculator(config)

    def get_retry_statistics(self) -> dict[str, Any]:
        """Get statistics about retry operations."""
        return {
            "rate_limit_events": len(self.rate_limit_detector.rate_limit_history),
            "recent_rate_limits": len([
                event for event in self.rate_limit_detector.rate_limit_history
                if time.time() - event[0] < 300
            ]),
            "config": {
                "max_attempts": self.config.max_attempts,
                "base_delay": self.config.base_delay,
                "max_delay": self.config.max_delay,
                "exponential_backoff": self.config.exponential_backoff
            }
        }


class AuthErrorHandler(TUIErrorHandler):
    """Enhanced error handling for authentication flows."""

    def __init__(self, app: App, auth_screen: Any = None) -> None:
        super().__init__(app)
        self.auth_screen = auth_screen
        self.retry_strategies = self._init_retry_strategies()

        # Initialize automatic retry manager
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=60.0,
            exponential_backoff=True,
            jitter=True,
            show_progress=True,
            cancellable=True
        )
        self.retry_manager = AutomaticRetryManager(app, retry_config)

        # Authentication-specific retry configuration
        self.configure_retry(
            max_attempts=3,
            base_delay=2.0,
            exponential_backoff=True,
            show_progress=True
        )

        logger.debug(
            "AuthErrorHandler initialized with automatic retry mechanisms")

    def _init_retry_strategies(self) -> list[AuthErrorRecoveryStrategy]:
        """Initialize error recovery strategies."""
        return [
            NetworkErrorRecoveryStrategy(),
            TokenErrorRecoveryStrategy(),
            EnvironmentErrorRecoveryStrategy()
        ]

    def classify_auth_error(self, error: Exception) -> AuthErrorType:
        """Classify the authentication error type."""
        if isinstance(error, NetworkError):
            return AuthErrorType.NETWORK
        elif isinstance(error, TimeoutError):
            return AuthErrorType.NETWORK
        elif isinstance(error, AuthenticationError):
            error_msg = str(error).lower()
            if "expired" in error_msg and "device" in error_msg:
                return AuthErrorType.DEVICE_CODE_EXPIRED
            elif "expired" in error_msg:
                return AuthErrorType.TOKEN_EXPIRED
            elif "denied" in error_msg:
                return AuthErrorType.USER_DENIED
            elif "invalid" in error_msg:
                return AuthErrorType.TOKEN_INVALID
            else:
                return AuthErrorType.TOKEN_INVALID
        elif isinstance(error, RateLimitError):
            return AuthErrorType.RATE_LIMITED
        elif isinstance(error, APIError):
            if error.status_code == 401:
                return AuthErrorType.TOKEN_INVALID
            elif error.status_code == 403:
                if error.is_rate_limited:
                    return AuthErrorType.RATE_LIMITED
                else:
                    return AuthErrorType.TOKEN_INVALID

        # Check for environment-specific errors
        error_msg = str(error).lower()
        if "browser" in error_msg:
            return AuthErrorType.BROWSER_UNAVAILABLE
        elif "clipboard" in error_msg:
            return AuthErrorType.CLIPBOARD_UNAVAILABLE
        elif any(term in error_msg for term in ["display", "headless", "x11"]):
            return AuthErrorType.ENVIRONMENT_RESTRICTED

        return AuthErrorType.UNKNOWN

    async def handle_auth_error(self, error: Exception, context: dict[str, Any] | None = None) -> AuthResult:
        """Handle authentication-specific errors with recovery options."""
        if context is None:
            context = {}

        error_type = self.classify_auth_error(error)
        logger.error(
            f"Authentication error classified as {error_type.value}: {error}")

        # Find appropriate recovery strategy
        recovery_strategy = None
        for strategy in self.retry_strategies:
            if await strategy.can_handle(error):
                recovery_strategy = strategy
                break

        if recovery_strategy is None:
            logger.warning(f"No recovery strategy found for error: {error}")
            return AuthResult(
                success=False,
                error=error,
                error_type=error_type,
                recovery_action=AuthRecoveryAction.CANCEL
            )

        # Get recovery action
        recovery_action = await recovery_strategy.recover(error, context)

        # Show user-friendly error message
        user_message = recovery_strategy.get_user_message(error)
        suggested_actions = recovery_strategy.get_suggested_actions(error)

        # Display error with suggestions
        if suggested_actions:
            suggestion_text = "\n💡 Try these solutions:\n" + \
                "\n".join(f"  • {action}" for action in suggested_actions[:3])
            full_message = f"{user_message}{suggestion_text}"
        else:
            full_message = user_message

        self.app.notify(full_message, severity="error", timeout=10.0)

        return AuthResult(
            success=False,
            error=error,
            error_type=error_type,
            recovery_action=recovery_action,
            retry_suggested=recovery_action in [
                AuthRecoveryAction.RETRY,
                AuthRecoveryAction.WAIT_AND_RETRY,
                AuthRecoveryAction.RESTART_FLOW
            ]
        )

    async def handle_network_error(self, error: NetworkError, context: dict[str, Any] | None = None) -> bool:
        """Handle network errors with automatic retry logic."""
        if context is None:
            context = {}

        # Use the automatic retry manager for network errors
        try:
            await self.retry_manager.execute_with_retry(
                lambda: None,  # Dummy operation since we're just handling the error
                "network_error_recovery"
            )
            return True
        except Exception:
            logger.error(f"Network error could not be recovered: {error}")
            self.notify_error(error)
            return False

    async def handle_token_error(self, error: AuthenticationError, context: dict[str, Any] | None = None) -> bool:
        """Handle token-related errors with user guidance."""
        if context is None:
            context = {}

        error_msg = str(error).lower()

        if "expired" in error_msg:
            self.app.notify(
                "🔑 Authentication expired. Starting new login flow...",
                severity="warning",
                timeout=3.0
            )
            return True  # Indicate that restart is needed

        elif "denied" in error_msg:
            self.app.notify(
                "❌ Authentication was denied. You can try again or cancel.",
                severity="error",
                timeout=5.0
            )
            return False

        else:
            self.app.notify(
                "🔑 Authentication failed. Please try logging in again.",
                severity="error",
                timeout=5.0
            )
            return False

    async def execute_auth_operation_with_retry(
        self,
        operation: Callable,
        operation_name: str = "authentication_operation",
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute authentication operation with specialized retry logic."""
        return await self.retry_manager.execute_with_retry(
            operation,
            operation_name,
            *args,
            **kwargs
        )

    async def handle_auth_flow_restart(self, error: Exception) -> bool:
        """Handle automatic authentication flow restart for expired tokens."""
        error_type = self.classify_auth_error(error)

        if error_type in [AuthErrorType.TOKEN_EXPIRED, AuthErrorType.DEVICE_CODE_EXPIRED]:
            logger.info(
                f"Automatically restarting auth flow due to {error_type.value}")

            # Show user notification
            self.app.notify(
                "🔄 Authentication expired. Automatically restarting login flow...",
                severity="information",
                timeout=3.0
            )

            # Use retry manager to handle the restart
            try:
                await self.retry_manager.execute_with_retry(
                    self._restart_auth_flow,
                    "auth_flow_restart"
                )
                return True
            except Exception as restart_error:
                logger.error(f"Failed to restart auth flow: {restart_error}")
                return False

        return False

    async def _restart_auth_flow(self) -> None:
        """Internal method to restart the authentication flow."""
        if self.auth_screen and hasattr(self.auth_screen, 'restart_auth_flow'):
            await self.auth_screen.restart_auth_flow()
        else:
            logger.warning(
                "Cannot restart auth flow - no auth screen or restart method available")
            raise AuthenticationError("Auth flow restart not available")

    def get_retry_progress_widget(self) -> RetryProgressIndicator | None:
        """Get the retry progress indicator widget for UI integration."""
        return self.retry_manager.progress_indicator

    def update_retry_config(self, config: RetryConfig) -> None:
        """Update the retry configuration."""
        self.retry_manager.update_config(config)
        logger.debug(
            f"Updated retry config: max_attempts={config.max_attempts}, base_delay={config.base_delay}")

    def get_retry_statistics(self) -> dict[str, Any]:
        """Get statistics about retry operations."""
        return self.retry_manager.get_retry_statistics()

    @asynccontextmanager
    async def auth_error_boundary(self, operation_name: str = "authentication") -> Any:
        """Context manager for handling authentication errors."""
        try:
            yield
        except (NetworkError, TimeoutError) as e:
            logger.error(f"Network error in {operation_name}: {e}")
            result = await self.handle_auth_error(e, {"operation": operation_name})

            # Convert to AuthResult exception for caller
            auth_error = AuthenticationError(
                f"Authentication failed in {operation_name}",
                cause=e
            )
            auth_error.add_context("auth_result", result)
            raise auth_error

        except AuthenticationError as e:
            logger.error(f"Authentication error in {operation_name}: {e}")
            result = await self.handle_auth_error(e, {"operation": operation_name})

            # Add result to error context
            e.add_context("auth_result", result)
            raise

        except Exception as e:
            logger.exception(f"Unexpected error in {operation_name}")
            auth_error = AuthenticationError(
                f"Unexpected authentication error in {operation_name}",
                cause=e
            )
            result = await self.handle_auth_error(auth_error, {"operation": operation_name})
            auth_error.add_context("auth_result", result)
            raise auth_error

    async def with_auth_retry(self, operation: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute authentication operation with specialized retry logic."""
        return await self.execute_auth_operation_with_retry(
            operation,
            "auth_operation",
            *args,
            **kwargs
        )


# Factory function for creating auth error handlers
def create_auth_error_handler(app: App, auth_screen: Any = None) -> AuthErrorHandler:
    """Create and configure an authentication error handler."""
    return AuthErrorHandler(app, auth_screen)
