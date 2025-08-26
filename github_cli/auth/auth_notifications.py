from __future__ import annotations

from .common import asyncio, dataclass, Enum, Any, Callable, Dict, List, Optional, logger
from typing import TYPE_CHECKING
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from github_cli.auth.token_expiration_handler import TokenState


class NotificationLevel(Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    CONSOLE = "console"
    TUI = "tui"
    LOG = "log"
    ALL = "all"


@dataclass
class AuthNotification:
    """Authentication notification data."""
    message: str
    level: NotificationLevel
    token_state: TokenState
    context: Dict[str, Any]
    timestamp: float
    channels: List[NotificationChannel]


class AuthNotificationSystem:
    """System for managing authentication state change notifications."""

    def __init__(self) -> None:
        self.console = Console()
        self._subscribers: Dict[NotificationChannel, List[Callable[[AuthNotification], None]]] = {
            NotificationChannel.CONSOLE: [],
            NotificationChannel.TUI: [],
            NotificationChannel.LOG: [],
        }
        self._notification_history: List[AuthNotification] = []
        self._max_history = 100

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

    def subscribe(self, channel: NotificationChannel, callback: Callable[[AuthNotification], None]) -> None:
        """Subscribe to authentication notifications on a specific channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []

        self._subscribers[channel].append(callback)
        logger.debug(
            f"Added subscriber to {channel.value} channel: {callback.__name__}")

    def unsubscribe(self, channel: NotificationChannel, callback: Callable[[AuthNotification], None]) -> None:
        """Unsubscribe from authentication notifications."""
        if channel in self._subscribers and callback in self._subscribers[channel]:
            self._subscribers[channel].remove(callback)
            logger.debug(
                f"Removed subscriber from {channel.value} channel: {callback.__name__}")

    def notify(
        self,
        message: str,
        token_state: TokenState,
        level: NotificationLevel = NotificationLevel.INFO,
        context: Dict[str, Any] | None = None,
        channels: List[NotificationChannel] | None = None
    ) -> None:
        """Send an authentication notification."""
        import time

        if channels is None:
            channels = [NotificationChannel.CONSOLE, NotificationChannel.LOG]

        notification = AuthNotification(
            message=message,
            level=level,
            token_state=token_state,
            context=context or {},
            timestamp=time.time(),
            channels=channels
        )

        # Add to history
        self._notification_history.append(notification)
        if len(self._notification_history) > self._max_history:
            self._notification_history.pop(0)

        # Send to appropriate channels
        for channel in channels:
            if channel == NotificationChannel.ALL:
                self._send_to_all_channels(notification)
            else:
                self._send_to_channel(channel, notification)

    def _send_to_all_channels(self, notification: AuthNotification) -> None:
        """Send notification to all available channels."""
        for channel in [NotificationChannel.CONSOLE, NotificationChannel.TUI, NotificationChannel.LOG]:
            self._send_to_channel(channel, notification)

    def _send_to_channel(self, channel: NotificationChannel, notification: AuthNotification) -> None:
        """Send notification to a specific channel."""
        try:
            # Built-in channel handlers
            if channel == NotificationChannel.CONSOLE:
                self._handle_console_notification(notification)
            elif channel == NotificationChannel.LOG:
                self._handle_log_notification(notification)

            # Custom subscribers
            if channel in self._subscribers:
                for callback in self._subscribers[channel]:
                    try:
                        callback(notification)
                    except Exception as e:
                        logger.error(
                            f"Error in notification callback {callback.__name__}: {e}")

        except Exception as e:
            logger.error(f"Error sending notification to {channel.value}: {e}")

    def _handle_console_notification(self, notification: AuthNotification) -> None:
        """Handle console notifications with rich formatting."""
        # Map notification levels to colors and icons
        level_config = {
            NotificationLevel.INFO: ("blue", "ℹ️"),
            NotificationLevel.WARNING: ("yellow", "⚠️"),
            NotificationLevel.ERROR: ("red", "❌"),
            NotificationLevel.SUCCESS: ("green", "✅"),
        }

        color, icon = level_config.get(notification.level, ("white", "📢"))

        # Create formatted message
        text = Text()
        text.append(f"{icon} ", style="bold")
        text.append(notification.message, style=f"bold {color}")

        # Add context information if available
        if notification.context:
            operation = notification.context.get("operation")
            if operation:
                text.append(f" ({operation})", style="dim")

        # Create panel for important notifications
        if notification.level in [NotificationLevel.WARNING, NotificationLevel.ERROR]:
            panel = Panel(
                text,
                title="Authentication Notice",
                border_style=color,
                padding=(0, 1)
            )
            self.console.print(panel)
        else:
            self.console.print(text)

    def _handle_log_notification(self, notification: AuthNotification) -> None:
        """Handle log notifications."""
        log_message = f"Auth notification: {notification.message} (state: {notification.token_state.value})"

        if notification.context:
            log_message += f" - Context: {notification.context}"

        # Map notification levels to log levels
        if notification.level == NotificationLevel.ERROR:
            logger.error(log_message)
        elif notification.level == NotificationLevel.WARNING:
            logger.warning(log_message)
        elif notification.level == NotificationLevel.SUCCESS:
            logger.info(log_message)
        else:
            logger.info(log_message)

    def get_recent_notifications(self, count: int = 10) -> List[AuthNotification]:
        """Get recent notifications."""
        return self._notification_history[-count:] if self._notification_history else []

    def clear_history(self) -> None:
        """Clear notification history."""
        self._notification_history.clear()
        logger.debug("Cleared notification history")

    def create_token_state_callback(self) -> Callable[[str, TokenState], None]:
        """Create a callback function for token expiration handler."""
        def callback(message: str, state: TokenState) -> None:
            # Map token states to notification levels
            level_mapping = {
                "valid": NotificationLevel.SUCCESS,
                "expired": NotificationLevel.ERROR,
                "expiring_soon": NotificationLevel.WARNING,
                "invalid": NotificationLevel.ERROR,
                "unknown": NotificationLevel.WARNING,
            }

            level = level_mapping.get(state.value, NotificationLevel.INFO)

            # Determine appropriate channels based on state
            channels = [NotificationChannel.LOG]
            if state.value in ["expired", "invalid"]:
                channels.append(NotificationChannel.CONSOLE)

            self.notify(
                message=message,
                token_state=state,
                level=level,
                channels=channels
            )

        return callback


# Global notification system instance
_notification_system: Optional[AuthNotificationSystem] = None


def get_notification_system() -> AuthNotificationSystem:
    """Get the global authentication notification system."""
    global _notification_system
    if _notification_system is None:
        _notification_system = AuthNotificationSystem()
    return _notification_system


def notify_auth_state_change(
    message: str,
    token_state: TokenState,
    level: NotificationLevel = NotificationLevel.INFO,
    context: Dict[str, Any] | None = None,
    channels: List[NotificationChannel] | None = None
) -> None:
    """Convenience function to send authentication notifications."""
    system = get_notification_system()
    system.notify(message, token_state, level, context, channels)


def subscribe_to_auth_notifications(
    channel: NotificationChannel,
    callback: Callable[[AuthNotification], None]
) -> None:
    """Convenience function to subscribe to authentication notifications."""
    system = get_notification_system()
    system.subscribe(channel, callback)


def unsubscribe_from_auth_notifications(
    channel: NotificationChannel,
    callback: Callable[[AuthNotification], None]
) -> None:
    """Convenience function to unsubscribe from authentication notifications."""
    system = get_notification_system()
    system.unsubscribe(channel, callback)
