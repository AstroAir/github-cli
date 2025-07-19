from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, Optional, TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field

from github_cli.utils.exceptions import AuthenticationError, TokenExpiredError

if TYPE_CHECKING:
    from github_cli.auth.authenticator import Authenticator
    from github_cli.api.client import GitHubClient


class TokenState(Enum):
    """Token state enumeration."""
    VALID = "valid"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class AuthenticationContext(BaseModel):
    """Context information for re-authentication."""
    operation: str = Field(description="Current operation being performed")
    endpoint: str = Field(description="API endpoint being accessed")
    user_message: str = Field(description="User-friendly context message")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    preserve_state: Dict[str, Any] = Field(
        default_factory=dict, description="State to preserve during re-auth")


@dataclass
class TokenExpirationConfig:
    """Configuration for token expiration handling."""
    expiration_warning_threshold: int = 300  # 5 minutes in seconds
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    auto_refresh_enabled: bool = True
    notification_enabled: bool = True


class TokenExpirationHandler:
    """Handles token expiration detection and seamless re-authentication."""

    def __init__(self, authenticator: Authenticator, config: TokenExpirationConfig | None = None):
        self.authenticator = authenticator
        self.config = config or TokenExpirationConfig()
        self._notification_callbacks: list[Callable[[
            str, TokenState], None]] = []
        self._context_stack: list[AuthenticationContext] = []

        # Setup notification system integration
        if self.config.notification_enabled:
            self._setup_notifications()

        # Setup logging
        logger.configure(
            handlers=[
                {
                    "sink": "logs/auth.log",
                    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
                    "rotation": "5 MB",
                    "retention": "3 days",
                    "level": "INFO"
                }
            ]
        )

    def _setup_notifications(self) -> None:
        """Setup integration with the notification system."""
        try:
            from github_cli.auth.auth_notifications import get_notification_system
            notification_system = get_notification_system()
            callback = notification_system.create_token_state_callback()
            self.add_notification_callback(callback)
            logger.debug("Integrated with notification system")
        except ImportError as e:
            logger.warning(f"Could not setup notifications: {e}")
        except Exception as e:
            logger.error(f"Error setting up notifications: {e}")

    def add_notification_callback(self, callback: Callable[[str, TokenState], None]) -> None:
        """Add a callback for authentication state change notifications."""
        self._notification_callbacks.append(callback)
        logger.debug(f"Added notification callback: {callback.__name__}")

    def remove_notification_callback(self, callback: Callable[[str, TokenState], None]) -> None:
        """Remove a notification callback."""
        if callback in self._notification_callbacks:
            self._notification_callbacks.remove(callback)
            logger.debug(f"Removed notification callback: {callback.__name__}")

    def _notify_state_change(self, message: str, state: TokenState) -> None:
        """Notify all registered callbacks about authentication state changes."""
        logger.info(f"Token state change: {state.value} - {message}")
        for callback in self._notification_callbacks:
            try:
                callback(message, state)
            except Exception as e:
                logger.error(
                    f"Error in notification callback {callback.__name__}: {e}")

    def check_token_state(self) -> TokenState:
        """Check the current state of the authentication token."""
        if not self.authenticator.token:
            return TokenState.INVALID

        # Get token data from token manager
        token_data = self._get_token_data()
        if not token_data:
            return TokenState.UNKNOWN

        # Check if token has expiration information
        if "expires_in" not in token_data or "created_at" not in token_data:
            # Token doesn't have expiration info, assume it's valid
            return TokenState.VALID

        current_time = int(time.time())
        created_at = token_data["created_at"]
        expires_in = token_data["expires_in"]
        expiry_time = created_at + expires_in

        if current_time >= expiry_time:
            return TokenState.EXPIRED
        elif (expiry_time - current_time) <= self.config.expiration_warning_threshold:
            return TokenState.EXPIRING_SOON
        else:
            return TokenState.VALID

    def _get_token_data(self) -> Dict[str, Any] | None:
        """Get token data from the token manager."""
        try:
            # Access the token manager's internal data
            if not self.authenticator.token_manager.active_token_file.exists():
                return None

            with open(self.authenticator.token_manager.active_token_file, 'r') as f:
                token_file_path = f.read().strip()

            if not token_file_path:
                return None

            import json
            from pathlib import Path

            token_file = Path(token_file_path)
            if not token_file.exists():
                return None

            with open(token_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting token data: {e}")
            return None

    def get_time_until_expiry(self) -> int | None:
        """Get the time in seconds until token expiry."""
        token_data = self._get_token_data()
        if not token_data or "expires_in" not in token_data or "created_at" not in token_data:
            return None

        current_time = int(time.time())
        created_at = token_data["created_at"]
        expires_in = token_data["expires_in"]
        expiry_time = created_at + expires_in

        return max(0, expiry_time - current_time)

    async def handle_token_expiration(self, context: AuthenticationContext) -> bool:
        """Handle token expiration with seamless re-authentication."""
        logger.info(
            f"Handling token expiration for operation: {context.operation}")

        # Add context to stack for preservation
        self._context_stack.append(context)

        try:
            # Notify about expiration
            self._notify_state_change(
                f"Token expired during {context.operation}. Re-authenticating...",
                TokenState.EXPIRED
            )

            # Attempt re-authentication
            success = await self._attempt_reauth(context)

            if success:
                self._notify_state_change(
                    f"Successfully re-authenticated for {context.operation}",
                    TokenState.VALID
                )
                logger.info(
                    f"Re-authentication successful for operation: {context.operation}")
                return True
            else:
                self._notify_state_change(
                    f"Re-authentication failed for {context.operation}",
                    TokenState.INVALID
                )
                logger.error(
                    f"Re-authentication failed for operation: {context.operation}")
                return False

        finally:
            # Remove context from stack
            if context in self._context_stack:
                self._context_stack.remove(context)

    async def _attempt_reauth(self, context: AuthenticationContext) -> bool:
        """Attempt re-authentication with exponential backoff."""
        for attempt in range(self.config.max_retry_attempts):
            try:
                logger.debug(
                    f"Re-authentication attempt {attempt + 1}/{self.config.max_retry_attempts}")

                # Clear the expired token
                self.authenticator._token = None

                # Start interactive login with context preservation
                await self.authenticator.login_interactive()

                # Verify the new token is valid
                if self.authenticator.token and self.check_token_state() == TokenState.VALID:
                    return True

            except Exception as e:
                logger.warning(
                    f"Re-authentication attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.debug(f"Waiting {delay}s before next attempt")
                    await asyncio.sleep(delay)

        return False

    @asynccontextmanager
    async def with_token_validation(
        self,
        operation: str,
        endpoint: str = "",
        user_message: str = ""
    ) -> AsyncGenerator[None, None]:
        """Context manager that validates token before and handles expiration during operations."""
        context = AuthenticationContext(
            operation=operation,
            endpoint=endpoint,
            user_message=user_message or f"Performing {operation}"
        )

        # Check token state before operation
        initial_state = self.check_token_state()

        if initial_state == TokenState.EXPIRED:
            logger.info(
                f"Token expired before {operation}, attempting re-authentication")
            success = await self.handle_token_expiration(context)
            if not success:
                raise TokenExpiredError(
                    f"Cannot perform {operation}: authentication failed")

        elif initial_state == TokenState.EXPIRING_SOON:
            if self.config.auto_refresh_enabled:
                logger.info(
                    f"Token expiring soon, proactively refreshing before {operation}")
                await self.handle_token_expiration(context)

        elif initial_state == TokenState.INVALID:
            raise AuthenticationError(
                f"Cannot perform {operation}: no valid authentication token")

        try:
            yield
        except Exception as e:
            # Check if the error is due to token expiration
            if self._is_token_expiration_error(e):
                logger.info(
                    f"Token expired during {operation}, attempting recovery")
                success = await self.handle_token_expiration(context)
                if success:
                    # Re-raise the original exception to allow the caller to retry
                    raise TokenExpiredError(
                        f"Token expired during {operation}, please retry") from e
                else:
                    raise AuthenticationError(
                        f"Re-authentication failed for {operation}") from e
            else:
                # Re-raise non-token-related errors
                raise

    def _is_token_expiration_error(self, error: Exception) -> bool:
        """Check if an error is likely due to token expiration."""
        error_str = str(error).lower()

        # Common patterns that indicate token expiration
        expiration_indicators = [
            "401",
            "unauthorized",
            "authentication failed",
            "invalid token",
            "expired token",
            "token has expired",
            "bad credentials"
        ]

        return any(indicator in error_str for indicator in expiration_indicators)

    async def refresh_token_if_needed(self) -> bool:
        """Proactively refresh token if it's expiring soon."""
        state = self.check_token_state()

        if state == TokenState.EXPIRING_SOON and self.config.auto_refresh_enabled:
            logger.info("Token expiring soon, attempting proactive refresh")
            context = AuthenticationContext(
                operation="proactive_refresh",
                endpoint="",
                user_message="Refreshing authentication token"
            )
            return await self.handle_token_expiration(context)

        return state == TokenState.VALID

    def get_current_context(self) -> AuthenticationContext | None:
        """Get the current authentication context if any."""
        return self._context_stack[-1] if self._context_stack else None

    def preserve_context_state(self, key: str, value: Any) -> None:
        """Preserve state in the current context."""
        if self._context_stack:
            self._context_stack[-1].preserve_state[key] = value

    def get_preserved_state(self, key: str) -> Any:
        """Get preserved state from the current context."""
        if self._context_stack:
            return self._context_stack[-1].preserve_state.get(key)
        return None
