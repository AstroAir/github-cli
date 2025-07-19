"""
Enhanced visual feedback system for GitHub CLI authentication.

This module provides comprehensive visual feedback components including animated
progress indicators, emphasized displays for important information, success/failure
states, and accessibility-compliant focus indicators.
"""

from __future__ import annotations

import time
from github_cli.auth.common import (
    asyncio, dataclass, field, Enum, Any, Callable, logger,
    Static, Label, Button, ProgressBar, Container, Horizontal, Vertical, Grid,
    ComposeResult, Binding, Message
)
from enum import auto
from typing import Literal, Protocol, runtime_checkable
from textual.widget import Widget
from textual.reactive import reactive, var
from textual.timer import Timer
from rich.text import Text
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from github_cli.ui.auth.responsive_layout import AuthLayoutConfig


class FeedbackState(Enum):
    """Visual feedback states."""
    IDLE = auto()
    LOADING = auto()
    SUCCESS = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass(frozen=True, slots=True)
class VisualFeedbackConfig:
    """Configuration for visual feedback components."""
    enable_animations: bool = True
    animation_speed: float = 1.0
    use_colors: bool = True
    high_contrast: bool = False
    accessibility_mode: bool = False
    show_progress_percentage: bool = True
    show_elapsed_time: bool = True
    emphasis_style: Literal["border", "highlight", "animation"] = "highlight"
    focus_indicator_style: Literal["outline",
                                   "background", "underline"] = "outline"


@runtime_checkable
class AnimatedIndicator(Protocol):
    """Protocol for animated visual indicators."""

    def start_animation(self) -> None:
        """Start the animation."""
        ...

    def stop_feedback_animation(self) -> None:
        """Stop the animation."""
        ...

    def update_state(self, state: FeedbackState, message: str = "") -> None:
        """Update the indicator state."""
        ...


class AnimatedProgressIndicator(Static):
    """Animated progress indicator with responsive sizing and accessibility support."""

    progress_value = reactive(0.0)
    current_state = reactive(FeedbackState.IDLE)
    animation_frame = reactive(0)
    is_animating = reactive(False)

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("space", "toggle_details", "Toggle Details", show=False),
    ]

    def __init__(self, config: AuthLayoutConfig, feedback_config: VisualFeedbackConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.feedback_config = feedback_config
        self.animation_timer: Timer | None = None
        self.progress_text = ""
        self.details_text = ""
        self.show_details = False
        self.console = Console()

        # Animation frames for different states
        self.loading_frames = ["⠋", "⠙", "⠹",
                               "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.success_frames = ["✓", "✅"]
        self.error_frames = ["✗", "❌"]
        self.warning_frames = ["⚠", "⚠️"]

        self.start_time = time.time()

    def compose(self) -> ComposeResult:
        """Compose the animated progress indicator."""
        with Container(classes="animated-progress-container"):
            if self.config.layout_type == "compact":
                yield Static(self._get_compact_display(), id="progress-display", classes="progress-compact")
            else:
                with Vertical():
                    yield Static(self._get_main_display(), id="progress-main", classes="progress-main")
                    if self.config.show_progress_details:
                        yield ProgressBar(id="progress-bar", classes="progress-bar")
                        yield Static("", id="progress-details", classes="progress-details")
                    if self.feedback_config.show_elapsed_time:
                        yield Static("", id="progress-time", classes="progress-time")

    def start_animation(self) -> None:
        """Start the progress animation."""
        if not self.feedback_config.enable_animations:
            return

        self.is_animating = True
        self.animation_frame = 0

        # Start animation timer based on speed
        interval = 0.1 / self.feedback_config.animation_speed
        self.animation_timer = self.set_interval(interval, self._animate_frame)

        logger.debug("Started progress animation")

    def stop_feedback_animation(self) -> None:
        """Stop the progress animation."""
        self.is_animating = False

        if self.animation_timer:
            self.animation_timer.stop()
            self.animation_timer = None

        logger.debug("Stopped progress animation")

    def update_state(self, state: FeedbackState, message: str = "") -> None:
        """Update the indicator state and message."""
        old_state = self.current_state
        self.current_state = state
        self.progress_text = message

        # Start/stop animation based on state
        if state == FeedbackState.LOADING and not self.is_animating:
            self.start_animation()
        elif state in (FeedbackState.SUCCESS, FeedbackState.ERROR) and self.is_animating:
            self.stop_feedback_animation()

        # Update display
        self._update_display()

        # Announce state change for screen readers
        if self.feedback_config.accessibility_mode and old_state != state:
            self._announce_state_change(state, message)

        logger.debug(
            f"Progress state updated: {old_state.name} -> {state.name}")

    def update_progress(self, value: float, details: str = "") -> None:
        """Update progress value and optional details."""
        self.progress_value = max(0.0, min(100.0, value))
        self.details_text = details

        # Update progress bar if available
        try:
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=self.progress_value)
        except Exception:
            pass  # Widget not available

        self._update_display()

    def _animate_frame(self) -> None:
        """Animate a single frame."""
        if not self.is_animating:
            return

        frames = self._get_animation_frames()
        self.animation_frame = (self.animation_frame + 1) % len(frames)
        self._update_display()

    def _get_animation_frames(self) -> list[str]:
        """Get animation frames for current state."""
        frame_map = {
            FeedbackState.LOADING: self.loading_frames,
            FeedbackState.SUCCESS: self.success_frames,
            FeedbackState.ERROR: self.error_frames,
            FeedbackState.WARNING: self.warning_frames,
        }
        return frame_map.get(self.current_state, ["⏳"])

    def _get_compact_display(self) -> str:
        """Get compact display text."""
        frames = self._get_animation_frames()
        current_frame = frames[self.animation_frame % len(frames)]

        if self.config.layout_type == "compact":
            # Very compact: just icon and short text
            short_text = self.progress_text[:20] + "..." if len(
                self.progress_text) > 20 else self.progress_text
            return f"{current_frame} {short_text}"
        else:
            return f"{current_frame} {self.progress_text}"

    def _get_main_display(self) -> str:
        """Get main display text with full formatting."""
        frames = self._get_animation_frames()
        current_frame = frames[self.animation_frame % len(frames)]

        # Create rich text with styling
        if self.feedback_config.use_colors and not self.feedback_config.high_contrast:
            color_map = {
                FeedbackState.LOADING: "blue",
                FeedbackState.SUCCESS: "green",
                FeedbackState.ERROR: "red",
                FeedbackState.WARNING: "yellow",
                FeedbackState.INFO: "cyan"
            }
            color = color_map.get(self.current_state, "white")

            if self.feedback_config.show_progress_percentage and self.progress_value > 0:
                return f"[{color}]{current_frame}[/{color}] {self.progress_text} ({self.progress_value:.1f}%)"
            else:
                return f"[{color}]{current_frame}[/{color}] {self.progress_text}"
        else:
            # High contrast or no color mode
            if self.feedback_config.show_progress_percentage and self.progress_value > 0:
                return f"{current_frame} {self.progress_text} ({self.progress_value:.1f}%)"
            else:
                return f"{current_frame} {self.progress_text}"

    def _update_display(self) -> None:
        """Update all display elements."""
        try:
            # Update main display
            if self.config.layout_type == "compact":
                display = self.query_one("#progress-display", Static)
                display.update(self._get_compact_display())
            else:
                main_display = self.query_one("#progress-main", Static)
                main_display.update(self._get_main_display())

                # Update details if available
                if self.details_text and self.config.show_progress_details:
                    details_display = self.query_one(
                        "#progress-details", Static)
                    details_display.update(self.details_text)

                # Update elapsed time
                if self.feedback_config.show_elapsed_time:
                    elapsed = time.time() - self.start_time
                    time_display = self.query_one("#progress-time", Static)
                    time_display.update(f"Elapsed: {elapsed:.1f}s")

        except Exception as e:
            logger.debug(f"Error updating progress display: {e}")

    def _announce_state_change(self, state: FeedbackState, message: str) -> None:
        """Announce state change for accessibility."""
        announcements = {
            FeedbackState.LOADING: f"Loading: {message}",
            FeedbackState.SUCCESS: f"Success: {message}",
            FeedbackState.ERROR: f"Error: {message}",
            FeedbackState.WARNING: f"Warning: {message}",
            FeedbackState.INFO: f"Information: {message}"
        }

        announcement = announcements.get(state, message)
        # In a real implementation, this would use screen reader APIs
        logger.info(f"Accessibility announcement: {announcement}")

    def action_cancel(self) -> None:
        """Handle cancel action."""
        self.post_message(self.Cancelled())

    def action_toggle_details(self) -> None:
        """Toggle detailed progress information."""
        self.show_details = not self.show_details
        self._update_display()

    class Cancelled(Message):
        """Message sent when progress is cancelled."""
        pass


class EmphasizedDisplay(Static):
    """Display widget with visual emphasis for important information."""

    emphasis_level = reactive(1)
    is_highlighted = reactive(False)

    def __init__(self, content: str, config: AuthLayoutConfig,
                 feedback_config: VisualFeedbackConfig, **kwargs) -> None:
        super().__init__(content, **kwargs)
        self.config = config
        self.feedback_config = feedback_config
        self.original_content = content
        self.highlight_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        """Compose the emphasized display."""
        with Container(classes=f"emphasized-display {self.config.layout_type}"):
            if self.feedback_config.emphasis_style == "border":
                yield Static(self._get_bordered_content(), classes="emphasized-content bordered")
            elif self.feedback_config.emphasis_style == "animation":
                yield Static(self._get_animated_content(), classes="emphasized-content animated")
            else:  # highlight
                yield Static(self._get_highlighted_content(), classes="emphasized-content highlighted")

    def set_emphasis_level(self, level: int) -> None:
        """Set the emphasis level (1-3, higher is more emphasized)."""
        self.emphasis_level = max(1, min(3, level))
        self._update_display()

    def start_highlight_animation(self, duration: float = 2.0) -> None:
        """Start highlight animation for the specified duration."""
        if not self.feedback_config.enable_animations:
            return

        self.is_highlighted = True
        self._update_display()

        # Stop highlighting after duration
        if self.highlight_timer:
            self.highlight_timer.stop()

        self.highlight_timer = self.set_timer(duration, self._stop_highlight)

    def _stop_highlight(self) -> None:
        """Stop highlight animation."""
        self.is_highlighted = False
        self._update_display()

    def _get_bordered_content(self) -> str:
        """Get content with border emphasis."""
        if self.config.layout_type == "compact":
            return f"[{self.original_content}]"
        else:
            border_chars = {1: "─", 2: "═", 3: "━"}
            border_char = border_chars.get(self.emphasis_level, "─")
            border_line = border_char * (len(self.original_content) + 4)

            return f"{border_line}\n  {self.original_content}  \n{border_line}"

    def _get_highlighted_content(self) -> str:
        """Get content with highlight emphasis."""
        if self.feedback_config.high_contrast:
            # High contrast mode - use text formatting
            if self.emphasis_level >= 3:
                return f">>> {self.original_content} <<<"
            elif self.emphasis_level >= 2:
                return f">> {self.original_content} <<"
            else:
                return f"> {self.original_content} <"
        else:
            # Color highlighting
            if self.is_highlighted:
                bg_color = "on_yellow" if not self.feedback_config.accessibility_mode else "on_white"
                return f"[black {bg_color}]{self.original_content}[/black {bg_color}]"
            else:
                emphasis_colors = {1: "bright_white",
                                   2: "bright_cyan", 3: "bright_yellow"}
                color = emphasis_colors.get(
                    self.emphasis_level, "bright_white")
                return f"[{color}]{self.original_content}[/{color}]"

    def _get_animated_content(self) -> str:
        """Get content with animation emphasis."""
        if not self.feedback_config.enable_animations:
            return self.original_content

        # Simple blinking effect for high emphasis
        if self.emphasis_level >= 3 and self.is_highlighted:
            return f"✨ {self.original_content} ✨"
        elif self.emphasis_level >= 2:
            return f"⭐ {self.original_content} ⭐"
        else:
            return f"• {self.original_content} •"

    def _update_display(self) -> None:
        """Update the display with current emphasis."""
        try:
            content_widget = self.query_one(".emphasized-content", Static)

            if self.feedback_config.emphasis_style == "border":
                content_widget.update(self._get_bordered_content())
            elif self.feedback_config.emphasis_style == "animation":
                content_widget.update(self._get_animated_content())
            else:
                content_widget.update(self._get_highlighted_content())

        except Exception as e:
            logger.debug(f"Error updating emphasized display: {e}")


class StateIndicator(Static):
    """Visual indicator for success/failure states with clear messaging."""

    current_state = reactive(FeedbackState.IDLE)

    def __init__(self, config: AuthLayoutConfig, feedback_config: VisualFeedbackConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.feedback_config = feedback_config
        self.state_message = ""
        self.additional_info = ""

    def compose(self) -> ComposeResult:
        """Compose the state indicator."""
        with Container(classes=f"state-indicator {self.config.layout_type}"):
            yield Static("", id="state-icon", classes="state-icon")
            yield Static("", id="state-message", classes="state-message")
            if self.config.show_detailed_instructions:
                yield Static("", id="state-details", classes="state-details")

    def show_success(self, message: str, details: str = "") -> None:
        """Show success state with message."""
        self.current_state = FeedbackState.SUCCESS
        self.state_message = message
        self.additional_info = details
        self._update_display()

        # Announce for accessibility
        if self.feedback_config.accessibility_mode:
            logger.info(f"Success: {message}")

    def show_error(self, message: str, details: str = "") -> None:
        """Show error state with message."""
        self.current_state = FeedbackState.ERROR
        self.state_message = message
        self.additional_info = details
        self._update_display()

        # Announce for accessibility
        if self.feedback_config.accessibility_mode:
            logger.info(f"Error: {message}")

    def show_warning(self, message: str, details: str = "") -> None:
        """Show warning state with message."""
        self.current_state = FeedbackState.WARNING
        self.state_message = message
        self.additional_info = details
        self._update_display()

        # Announce for accessibility
        if self.feedback_config.accessibility_mode:
            logger.info(f"Warning: {message}")

    def show_info(self, message: str, details: str = "") -> None:
        """Show info state with message."""
        self.current_state = FeedbackState.INFO
        self.state_message = message
        self.additional_info = details
        self._update_display()

    def clear(self) -> None:
        """Clear the state indicator."""
        self.current_state = FeedbackState.IDLE
        self.state_message = ""
        self.additional_info = ""
        self._update_display()

    def _update_display(self) -> None:
        """Update the state indicator display."""
        try:
            icon_widget = self.query_one("#state-icon", Static)
            message_widget = self.query_one("#state-message", Static)

            # Update icon
            icon_widget.update(self._get_state_icon())

            # Update message
            message_widget.update(self._get_formatted_message())

            # Update details if available
            if self.config.show_detailed_instructions and self.additional_info:
                details_widget = self.query_one("#state-details", Static)
                details_widget.update(self.additional_info)

        except Exception as e:
            logger.debug(f"Error updating state indicator: {e}")

    def _get_state_icon(self) -> str:
        """Get icon for current state."""
        if self.feedback_config.high_contrast:
            # Text-based icons for high contrast
            icon_map = {
                FeedbackState.SUCCESS: "[OK]",
                FeedbackState.ERROR: "[ERROR]",
                FeedbackState.WARNING: "[WARNING]",
                FeedbackState.INFO: "[INFO]",
                FeedbackState.IDLE: ""
            }
        else:
            # Emoji icons
            icon_map = {
                FeedbackState.SUCCESS: "✅",
                FeedbackState.ERROR: "❌",
                FeedbackState.WARNING: "⚠️",
                FeedbackState.INFO: "ℹ️",
                FeedbackState.IDLE: ""
            }

        return icon_map.get(self.current_state, "")

    def _get_formatted_message(self) -> str:
        """Get formatted message with appropriate styling."""
        if not self.state_message:
            return ""

        if self.feedback_config.use_colors and not self.feedback_config.high_contrast:
            color_map = {
                FeedbackState.SUCCESS: "green",
                FeedbackState.ERROR: "red",
                FeedbackState.WARNING: "yellow",
                FeedbackState.INFO: "blue"
            }
            color = color_map.get(self.current_state, "white")
            return f"[{color}]{self.state_message}[/{color}]"
        else:
            return self.state_message


class AccessibleFocusIndicator(Static):
    """Accessibility-compliant focus indicator for navigation."""

    is_focused = reactive(False)
    focus_style = reactive("outline")

    def __init__(self, target_widget: Widget, feedback_config: VisualFeedbackConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.target_widget = target_widget
        self.feedback_config = feedback_config
        self.focus_style = feedback_config.focus_indicator_style

    def compose(self) -> ComposeResult:
        """Compose the focus indicator."""
        yield Static("", id="focus-indicator", classes=f"focus-indicator {self.focus_style}")

    def set_focused(self, focused: bool) -> None:
        """Set focus state."""
        self.is_focused = focused
        self._update_indicator()

        # Announce focus change for screen readers
        if self.feedback_config.accessibility_mode and focused:
            widget_name = getattr(self.target_widget, 'name', 'element')
            logger.info(f"Focus: {widget_name}")

    def _update_indicator(self) -> None:
        """Update the focus indicator display."""
        try:
            indicator = self.query_one("#focus-indicator", Static)

            if not self.is_focused:
                indicator.update("")
                return

            if self.focus_style == "outline":
                # Outline style focus indicator
                if self.feedback_config.high_contrast:
                    indicator.update(">>> FOCUSED <<<")
                else:
                    indicator.update("┌─ FOCUSED ─┐")
            elif self.focus_style == "background":
                # Background highlight
                if self.feedback_config.high_contrast:
                    indicator.update("[FOCUSED]")
                else:
                    indicator.update("[reverse]FOCUSED[/reverse]")
            else:  # underline
                # Underline style
                indicator.update("▔▔▔▔▔▔▔▔")

        except Exception as e:
            logger.debug(f"Error updating focus indicator: {e}")


class VisualFeedbackManager:
    """Manager for coordinating all visual feedback components."""

    def __init__(self, config: AuthLayoutConfig, feedback_config: VisualFeedbackConfig | None = None) -> None:
        """Initialize the visual feedback manager."""
        self.config = config
        self.feedback_config = feedback_config or VisualFeedbackConfig()

        # Create feedback components
        self.progress_indicator = AnimatedProgressIndicator(
            config, self.feedback_config)
        self.state_indicator = StateIndicator(config, self.feedback_config)
        self.emphasized_displays: dict[str, EmphasizedDisplay] = {}
        self.focus_indicators: dict[str, AccessibleFocusIndicator] = {}

        logger.debug("VisualFeedbackManager initialized")

    def create_emphasized_display(self, key: str, content: str, emphasis_level: int = 2) -> EmphasizedDisplay:
        """Create an emphasized display for important information."""
        display = EmphasizedDisplay(content, self.config, self.feedback_config)
        display.set_emphasis_level(emphasis_level)
        self.emphasized_displays[key] = display
        return display

    def create_focus_indicator(self, key: str, target_widget: Widget) -> AccessibleFocusIndicator:
        """Create a focus indicator for a widget."""
        indicator = AccessibleFocusIndicator(
            target_widget, self.feedback_config)
        self.focus_indicators[key] = indicator
        return indicator

    def update_progress(self, step: str, progress: float = 0.0, details: str = "") -> None:
        """Update progress indicator."""
        self.progress_indicator.update_state(FeedbackState.LOADING, step)
        if progress > 0:
            self.progress_indicator.update_progress(progress, details)

    def show_success(self, message: str, details: str = "") -> None:
        """Show success state across all indicators."""
        self.progress_indicator.update_state(FeedbackState.SUCCESS, message)
        self.state_indicator.show_success(message, details)

    def show_error(self, message: str, details: str = "") -> None:
        """Show error state across all indicators."""
        self.progress_indicator.update_state(FeedbackState.ERROR, message)
        self.state_indicator.show_error(message, details)

    def show_warning(self, message: str, details: str = "") -> None:
        """Show warning state across all indicators."""
        self.progress_indicator.update_state(FeedbackState.WARNING, message)
        self.state_indicator.show_warning(message, details)

    def emphasize_content(self, key: str, duration: float = 2.0) -> None:
        """Emphasize content by key."""
        if key in self.emphasized_displays:
            self.emphasized_displays[key].start_highlight_animation(duration)

    def set_focus(self, key: str, focused: bool) -> None:
        """Set focus state for a widget."""
        if key in self.focus_indicators:
            self.focus_indicators[key].set_focused(focused)

    def get_feedback_widgets(self) -> dict[str, Widget]:
        """Get all feedback widgets for layout composition."""
        widgets = {
            "progress_indicator": self.progress_indicator,
            "state_indicator": self.state_indicator
        }

        # Add emphasized displays
        for key, display in self.emphasized_displays.items():
            widgets[f"emphasized_{key}"] = display

        # Add focus indicators
        for key, indicator in self.focus_indicators.items():
            widgets[f"focus_{key}"] = indicator

        return widgets

    def update_config(self, new_config: AuthLayoutConfig, new_feedback_config: VisualFeedbackConfig | None = None) -> None:
        """Update configuration for all feedback components."""
        self.config = new_config
        if new_feedback_config:
            self.feedback_config = new_feedback_config

        # Update component configurations
        self.progress_indicator.config = new_config
        self.progress_indicator.feedback_config = self.feedback_config
        self.state_indicator.config = new_config
        self.state_indicator.feedback_config = self.feedback_config

        for display in self.emphasized_displays.values():
            display.config = new_config
            display.feedback_config = self.feedback_config

        for indicator in self.focus_indicators.values():
            indicator.feedback_config = self.feedback_config

        logger.debug("Visual feedback configuration updated")

    def cleanup(self) -> None:
        """Clean up all feedback components."""
        self.progress_indicator.stop_feedback_animation()

        for display in self.emphasized_displays.values():
            if display.highlight_timer:
                display.highlight_timer.stop()

        self.emphasized_displays.clear()
        self.focus_indicators.clear()

        logger.debug("VisualFeedbackManager cleaned up")
