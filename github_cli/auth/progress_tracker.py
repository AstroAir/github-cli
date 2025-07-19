"""
Authentication progress tracking system for GitHub CLI.

This module provides comprehensive progress tracking for authentication flows,
including step management, visual indicators, countdown timers, and adaptive
status displays that respond to terminal size changes.
"""

from __future__ import annotations

import time
from .common import (
    asyncio, dataclass, field, Enum, Any, Callable, logger,
    Static, ProgressBar, Label, Container, Horizontal, Vertical, ComposeResult
)
from enum import auto
from typing import Protocol, runtime_checkable
from textual.widget import Widget
from textual.reactive import reactive
from textual.timer import Timer

from github_cli.ui.auth.responsive_layout import AuthLayoutConfig


class AuthStep(Enum):
    """Authentication flow steps."""
    INITIALIZING = auto()
    REQUESTING_CODE = auto()
    WAITING_FOR_USER = auto()
    POLLING_TOKEN = auto()
    VALIDATING = auto()
    COMPLETE = auto()
    ERROR = auto()


@dataclass(frozen=True, slots=True)
class AuthProgressState:
    """Immutable state for authentication progress."""
    current_step: AuthStep
    step_name: str
    step_description: str
    progress_percentage: float = 0.0
    elapsed_time: float = 0.0
    estimated_remaining: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3


@runtime_checkable
class ProgressIndicator(Protocol):
    """Protocol for progress indicator widgets."""

    def update_progress(self, state: AuthProgressState) -> None:
        """Update the progress indicator with new state."""
        ...

    def show_error(self, error_message: str) -> None:
        """Show error state in the indicator."""
        ...

    def show_success(self, message: str) -> None:
        """Show success state in the indicator."""
        ...


@runtime_checkable
class CountdownTimer(Protocol):
    """Protocol for countdown timer widgets."""

    def start_countdown(self, duration: int, message: str, callback: Callable[[], None] | None = None) -> None:
        """Start a countdown timer."""
        ...

    def stop_countdown(self) -> None:
        """Stop the current countdown."""
        ...

    def update_message(self, message: str) -> None:
        """Update the countdown message."""
        ...


@runtime_checkable
class StatusDisplay(Protocol):
    """Protocol for status display widgets."""

    def update_status(self, status: str, details: dict[str, Any] | None = None) -> None:
        """Update the status display."""
        ...

    def show_step_progress(self, current_step: int, total_steps: int, step_name: str) -> None:
        """Show step-based progress."""
        ...

    def set_adaptive_content(self, config: AuthLayoutConfig) -> None:
        """Adapt content based on layout configuration."""
        ...


class ResponsiveProgressIndicator(Static):
    """Responsive progress indicator that adapts to terminal size."""

    progress_state = reactive(None, layout=True)

    def __init__(self, config: AuthLayoutConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.progress_bar: ProgressBar | None = None
        self.status_label: Label | None = None
        self._setup_widgets()

    def _setup_widgets(self) -> None:
        """Setup progress widgets based on configuration."""
        if self.config.show_progress_details:
            self.progress_bar = ProgressBar(
                show_percentage=True, show_eta=True)
            self.status_label = Label("Initializing...")
        else:
            # Compact mode - simple indicator
            self.status_label = Label("⏳ Initializing...")

    def compose(self) -> ComposeResult:
        """Compose the progress indicator widgets."""
        if self.config.layout_type == "compact":
            if self.status_label:
                yield self.status_label
        else:
            with Vertical():
                if self.status_label:
                    yield self.status_label
                if self.progress_bar:
                    yield self.progress_bar

    def update_progress(self, state: AuthProgressState) -> None:
        """Update the progress indicator with new state."""
        self.progress_state = state

        if self.status_label:
            if self.config.layout_type == "compact":
                # Compact status with emoji
                emoji = self._get_step_emoji(state.current_step)
                self.status_label.update(f"{emoji} {state.step_name}")
            else:
                # Detailed status
                elapsed = f"{state.elapsed_time:.1f}s"
                if state.estimated_remaining:
                    remaining = f"{state.estimated_remaining:.1f}s"
                    self.status_label.update(
                        f"{state.step_description} ({elapsed} elapsed, ~{remaining} remaining)")
                else:
                    self.status_label.update(
                        f"{state.step_description} ({elapsed} elapsed)")

        if self.progress_bar and state.progress_percentage > 0:
            self.progress_bar.update(progress=state.progress_percentage)

    def show_error(self, error_message: str) -> None:
        """Show error state in the indicator."""
        if self.status_label:
            if self.config.layout_type == "compact":
                self.status_label.update(f"❌ Error")
            else:
                self.status_label.update(f"❌ Error: {error_message}")

        if self.progress_bar:
            self.progress_bar.update(progress=0)

    def show_success(self, message: str) -> None:
        """Show success state in the indicator."""
        if self.status_label:
            if self.config.layout_type == "compact":
                self.status_label.update(f"✅ Complete")
            else:
                self.status_label.update(f"✅ {message}")

        if self.progress_bar:
            self.progress_bar.update(progress=100)

    def _get_step_emoji(self, step: AuthStep) -> str:
        """Get emoji for authentication step."""
        emoji_map = {
            AuthStep.INITIALIZING: "🚀",
            AuthStep.REQUESTING_CODE: "📋",
            AuthStep.WAITING_FOR_USER: "⏳",
            AuthStep.POLLING_TOKEN: "🔄",
            AuthStep.VALIDATING: "🔍",
            AuthStep.COMPLETE: "✅",
            AuthStep.ERROR: "❌"
        }
        return emoji_map.get(step, "⏳")


class ResponsiveCountdownTimer(Static):
    """Responsive countdown timer with adaptive display."""

    remaining_time = reactive(0)
    is_active = reactive(False)

    def __init__(self, config: AuthLayoutConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.timer: Timer | None = None
        self.callback: Callable[[], None] | None = None
        self.message = ""
        self.total_duration = 0

    def compose(self):
        """Compose the countdown timer display."""
        if self.config.show_countdown_timer:
            yield Label(self._format_countdown(), id="countdown-label")

    def start_countdown(self, duration: int, message: str, callback: Callable[[], None] | None = None) -> None:
        """Start a countdown timer."""
        self.stop_countdown()  # Stop any existing timer

        self.total_duration = duration
        self.remaining_time = duration
        self.message = message
        self.callback = callback
        self.is_active = True

        # Start the timer
        self.timer = self.set_interval(1.0, self._tick)

        logger.debug(f"Started countdown timer: {duration}s - {message}")

    def stop_countdown(self) -> None:
        """Stop the current countdown."""
        if self.timer:
            self.timer.stop()
            self.timer = None

        self.is_active = False
        self.remaining_time = 0

        logger.debug("Stopped countdown timer")

    def update_message(self, message: str) -> None:
        """Update the countdown message."""
        self.message = message
        self._update_display()

    def _tick(self) -> None:
        """Timer tick handler."""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self._update_display()
        else:
            # Timer finished
            self.stop_countdown()
            if self.callback:
                self.callback()

    def _update_display(self) -> None:
        """Update the countdown display."""
        countdown_label = self.query_one("#countdown-label", Label)
        if countdown_label:
            countdown_label.update(self._format_countdown())

    def _format_countdown(self) -> str:
        """Format the countdown display based on layout configuration."""
        if not self.is_active:
            return ""

        if self.config.layout_type == "compact":
            # Compact format: "⏱ 30s"
            return f"⏱ {self.remaining_time}s"
        else:
            # Detailed format with progress bar
            progress = ((self.total_duration - self.remaining_time) /
                        self.total_duration) * 100
            minutes, seconds = divmod(self.remaining_time, 60)

            if minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"

            return f"{self.message} ({time_str} remaining) [{progress:.0f}%]"


class AdaptiveStatusDisplay(Static):
    """Adaptive status display that changes content based on terminal size."""

    current_status = reactive("")
    current_details = reactive({})

    def __init__(self, config: AuthLayoutConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.step_progress: tuple[int, int, str] | None = None

    def compose(self):
        """Compose the status display."""
        with Vertical():
            yield Label(self.current_status, id="status-main")
            if self.config.show_detailed_instructions:
                yield Label("", id="status-details")
                yield Label("", id="status-steps")

    def update_status(self, status: str, details: dict[str, Any] | None = None) -> None:
        """Update the status display."""
        self.current_status = status
        self.current_details = details or {}

        # Update main status if widget is available
        try:
            status_main = self.query_one("#status-main", Label)
            status_main.update(status)
        except Exception:
            # Widget not available (e.g., during testing)
            pass

        # Update details if available and layout supports it
        if self.config.show_detailed_instructions and details:
            try:
                status_details = self.query_one("#status-details", Label)
                details_text = self._format_details(details)
                status_details.update(details_text)
            except Exception:
                # Widget not available (e.g., during testing)
                pass

        logger.debug(f"Status updated: {status}")

    def show_step_progress(self, current_step: int, total_steps: int, step_name: str) -> None:
        """Show step-based progress."""
        self.step_progress = (current_step, total_steps, step_name)

        if self.config.show_progress_details:
            try:
                status_steps = self.query_one("#status-steps", Label)
                progress_text = f"Step {current_step}/{total_steps}: {step_name}"
                status_steps.update(progress_text)
            except Exception:
                # Widget not available (e.g., during testing)
                pass

    def set_adaptive_content(self, config: AuthLayoutConfig) -> None:
        """Adapt content based on layout configuration."""
        self.config = config
        # Re-render with new configuration
        self.refresh(layout=True)

    def _format_details(self, details: dict[str, Any]) -> str:
        """Format details based on layout configuration."""
        if self.config.layout_type == "compact":
            # Show only essential details
            essential_keys = ["user_code", "verification_uri", "error"]
            filtered_details = {k: v for k,
                                v in details.items() if k in essential_keys}
            return " | ".join(f"{k}: {v}" for k, v in filtered_details.items())
        else:
            # Show all details with formatting
            formatted_lines = []
            for key, value in details.items():
                formatted_key = key.replace("_", " ").title()
                formatted_lines.append(f"{formatted_key}: {value}")
            return "\n".join(formatted_lines)


class AuthProgressTracker:
    """Comprehensive authentication progress tracking system."""

    # Step definitions with metadata
    STEP_DEFINITIONS = {
        AuthStep.INITIALIZING: {
            "name": "Initializing",
            "description": "Setting up authentication flow",
            "estimated_duration": 2.0,
            "progress_weight": 5
        },
        AuthStep.REQUESTING_CODE: {
            "name": "Requesting Code",
            "description": "Contacting GitHub for device code",
            "estimated_duration": 3.0,
            "progress_weight": 10
        },
        AuthStep.WAITING_FOR_USER: {
            "name": "Waiting for Authorization",
            "description": "User needs to authorize in browser",
            "estimated_duration": 60.0,
            "progress_weight": 20
        },
        AuthStep.POLLING_TOKEN: {
            "name": "Checking Authorization",
            "description": "Checking for authorization completion",
            "estimated_duration": 30.0,
            "progress_weight": 50
        },
        AuthStep.VALIDATING: {
            "name": "Validating Token",
            "description": "Verifying token and fetching user info",
            "estimated_duration": 5.0,
            "progress_weight": 10
        },
        AuthStep.COMPLETE: {
            "name": "Complete",
            "description": "Authentication successful",
            "estimated_duration": 1.0,
            "progress_weight": 5
        }
    }

    def __init__(self, layout_config: AuthLayoutConfig) -> None:
        """Initialize the progress tracker."""
        self.layout_config = layout_config
        self.current_state = AuthProgressState(
            current_step=AuthStep.INITIALIZING,
            step_name=self.STEP_DEFINITIONS[AuthStep.INITIALIZING]["name"],
            step_description=self.STEP_DEFINITIONS[AuthStep.INITIALIZING]["description"]
        )

        # Create responsive widgets
        self.progress_indicator = ResponsiveProgressIndicator(layout_config)
        self.countdown_timer = ResponsiveCountdownTimer(layout_config)
        self.status_display = AdaptiveStatusDisplay(layout_config)

        # Tracking state
        self.start_time = time.time()
        self.step_start_time = time.time()
        self.step_history: list[tuple[AuthStep, float]] = []
        self.callbacks: list[Callable[[AuthProgressState], None]] = []

        logger.info("AuthProgressTracker initialized")

    def add_progress_callback(self, callback: Callable[[AuthProgressState], None]) -> None:
        """Add a callback to be called when progress updates."""
        self.callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[AuthProgressState], None]) -> None:
        """Remove a progress callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def update_step(self, step: AuthStep, details: dict[str, Any] | None = None) -> None:
        """Update current authentication step with details."""
        if step == self.current_state.current_step:
            # Same step, just update details
            if details:
                new_details = {**self.current_state.details, **details}
                self.current_state = AuthProgressState(
                    current_step=self.current_state.current_step,
                    step_name=self.current_state.step_name,
                    step_description=self.current_state.step_description,
                    progress_percentage=self.current_state.progress_percentage,
                    elapsed_time=time.time() - self.start_time,
                    estimated_remaining=self._calculate_estimated_remaining(
                        step),
                    details=new_details,
                    error_message=self.current_state.error_message,
                    retry_count=self.current_state.retry_count,
                    max_retries=self.current_state.max_retries
                )
        else:
            # New step
            self._record_step_completion(self.current_state.current_step)
            self.step_start_time = time.time()

            step_def = self.STEP_DEFINITIONS.get(step, {})
            self.current_state = AuthProgressState(
                current_step=step,
                step_name=step_def.get("name", step.name.title()),
                step_description=step_def.get("description", "Processing..."),
                progress_percentage=self._calculate_progress_percentage(step),
                elapsed_time=time.time() - self.start_time,
                estimated_remaining=self._calculate_estimated_remaining(step),
                details=details or {},
                retry_count=0,
                max_retries=3
            )

        # Update widgets
        self.progress_indicator.update_progress(self.current_state)
        self.status_display.update_status(
            self.current_state.step_description,
            self.current_state.details
        )

        # Update step progress
        current_step_num = list(self.STEP_DEFINITIONS.keys()).index(step) + 1
        total_steps = len(self.STEP_DEFINITIONS)
        self.status_display.show_step_progress(
            current_step_num, total_steps, self.current_state.step_name
        )

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.current_state)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

        logger.debug(f"Progress updated to step: {step.name}")

    def show_waiting_indicator(self, message: str, timeout: int | None = None) -> None:
        """Show waiting indicator with optional timeout."""
        self.status_display.update_status(f"⏳ {message}")

        if timeout and self.layout_config.show_countdown_timer:
            self.countdown_timer.start_countdown(
                timeout,
                message,
                lambda: self.status_display.update_status("⏰ Timeout reached")
            )

    def show_countdown(self, duration: int, message: str, callback: Callable[[], None] | None = None) -> None:
        """Show countdown timer for delays."""
        if self.layout_config.show_countdown_timer:
            self.countdown_timer.start_countdown(duration, message, callback)
        else:
            # Fallback for compact layouts
            self.status_display.update_status(f"⏱ {message} ({duration}s)")

    def show_error(self, error_message: str, retry_count: int = 0) -> None:
        """Show error state with retry information."""
        self.current_state = AuthProgressState(
            current_step=AuthStep.ERROR,
            step_name="Error",
            step_description=error_message,
            progress_percentage=0.0,
            elapsed_time=time.time() - self.start_time,
            error_message=error_message,
            retry_count=retry_count,
            max_retries=self.current_state.max_retries
        )

        self.progress_indicator.show_error(error_message)

        if retry_count > 0:
            retry_msg = f"Retry {retry_count}/{self.current_state.max_retries}"
            self.status_display.update_status(
                f"❌ {error_message} ({retry_msg})")
        else:
            self.status_display.update_status(f"❌ {error_message}")

        logger.error(f"Progress error: {error_message} (retry {retry_count})")

    def show_success(self, message: str = "Authentication successful") -> None:
        """Show success state."""
        self.update_step(AuthStep.COMPLETE, {"success_message": message})
        self.progress_indicator.show_success(message)
        self.countdown_timer.stop_countdown()

        logger.info(f"Progress completed successfully: {message}")

    def get_progress_widgets(self) -> dict[str, Widget]:
        """Get all progress tracking widgets for layout composition."""
        widgets = {
            "progress_indicator": self.progress_indicator,
            "status_display": self.status_display
        }

        if self.layout_config.show_countdown_timer:
            widgets["countdown_timer"] = self.countdown_timer

        return widgets

    def update_layout_config(self, new_config: AuthLayoutConfig) -> None:
        """Update layout configuration and adapt widgets."""
        self.layout_config = new_config

        # Update widget configurations
        self.progress_indicator.config = new_config
        self.countdown_timer.config = new_config
        self.status_display.set_adaptive_content(new_config)

        # Refresh current state display
        self.progress_indicator.update_progress(self.current_state)

        logger.debug(
            f"Progress tracker layout updated to: {new_config.layout_type}")

    def _calculate_progress_percentage(self, step: AuthStep) -> float:
        """Calculate overall progress percentage based on step weights."""
        total_weight = sum(def_data["progress_weight"]
                           for def_data in self.STEP_DEFINITIONS.values())
        completed_weight = 0

        for completed_step in self.STEP_DEFINITIONS:
            if list(self.STEP_DEFINITIONS.keys()).index(completed_step) < list(self.STEP_DEFINITIONS.keys()).index(step):
                completed_weight += self.STEP_DEFINITIONS[completed_step]["progress_weight"]

        return (completed_weight / total_weight) * 100

    def _calculate_estimated_remaining(self, step: AuthStep) -> float | None:
        """Calculate estimated remaining time based on step history."""
        if not self.step_history:
            # No history, use step definition estimates
            remaining_steps = list(self.STEP_DEFINITIONS.keys())[
                list(self.STEP_DEFINITIONS.keys()).index(step):]
            return sum(self.STEP_DEFINITIONS[s]["estimated_duration"] for s in remaining_steps)

        # Use historical data to improve estimates
        avg_step_time = sum(
            duration for _, duration in self.step_history) / len(self.step_history)
        remaining_step_count = len(
            self.STEP_DEFINITIONS) - list(self.STEP_DEFINITIONS.keys()).index(step)

        return avg_step_time * remaining_step_count

    def _record_step_completion(self, completed_step: AuthStep) -> None:
        """Record completion of a step for timing analysis."""
        if completed_step != AuthStep.INITIALIZING:  # Don't record the initial step
            step_duration = time.time() - self.step_start_time
            self.step_history.append((completed_step, step_duration))

            # Keep only recent history to adapt to current conditions
            if len(self.step_history) > 10:
                self.step_history = self.step_history[-10:]

    def get_current_state(self) -> AuthProgressState:
        """Get the current progress state."""
        return self.current_state

    def cleanup(self) -> None:
        """Clean up resources when tracker is destroyed."""
        self.countdown_timer.stop_countdown()
        self.callbacks.clear()
        logger.debug("AuthProgressTracker cleaned up")
