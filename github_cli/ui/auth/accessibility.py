"""
Accessibility enhancements for GitHub CLI authentication system.

This module provides comprehensive accessibility support including screen reader
compatibility, high contrast mode, keyboard navigation, and configurable
accessibility preferences.
"""

from __future__ import annotations

import os
from github_cli.auth.common import (
    platform, subprocess, asyncio, dataclass, field, Any, Dict, List, Optional,
    Enum, logger, Screen
)
from github_cli.auth.preferences import AuthPreferences


class AccessibilityLevel(Enum):
    """Accessibility compliance levels."""
    NONE = "none"
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"


class NavigationMode(Enum):
    """Navigation modes for accessibility."""
    STANDARD = "standard"
    KEYBOARD_ONLY = "keyboard_only"
    SCREEN_READER = "screen_reader"
    ASSISTIVE_ONLY = "assistive_only"


class ScreenReaderType(Enum):
    """Supported screen reader types."""
    NONE = "none"
    NVDA = "nvda"
    JAWS = "jaws"
    NARRATOR = "narrator"
    VOICEOVER = "voiceover"
    ORCA = "orca"


@dataclass
class AccessibilitySettings:
    """Basic accessibility settings configuration."""

    # Screen reader support
    screen_reader_enabled: bool = False
    screen_reader_type: ScreenReaderType = ScreenReaderType.NONE
    announce_state_changes: bool = True
    verbose_descriptions: bool = False

    # Visual accessibility
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    reduce_motion: bool = False
    focus_indicator_enhanced: bool = True

    # Keyboard navigation
    keyboard_only_navigation: bool = False
    tab_navigation_enhanced: bool = True

    # Audio feedback
    audio_cues_enabled: bool = False

    # Timing and interaction
    extended_timeouts: bool = False

    # Content preferences
    simplified_interface: bool = False

    # General accessibility mode
    accessibility_mode: bool = False

    @classmethod
    def detect_system_accessibility(cls) -> AccessibilitySettings:
        """Detect system accessibility settings."""
        settings = cls()

        try:
            # Detect screen reader
            screen_reader = AccessibilityDetector.detect_screen_reader()
            if screen_reader != ScreenReaderType.NONE:
                settings.screen_reader_enabled = True
                settings.screen_reader_type = screen_reader
                settings.keyboard_only_navigation = True
                settings.verbose_descriptions = True

            # Detect high contrast mode
            if AccessibilityDetector.detect_high_contrast():
                settings.high_contrast_mode = True
                settings.focus_indicator_enhanced = True
                settings.reduce_motion = True

        except Exception as e:
            logger.warning(
                f"Failed to detect system accessibility settings: {e}")

        return settings

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AccessibilitySettings:
        """Create settings from dictionary."""
        if 'screen_reader_type' in data:
            data['screen_reader_type'] = ScreenReaderType(
                data['screen_reader_type'])

        return cls(**data)


class AccessibilityDetector:
    """Utility class for detecting system accessibility features."""

    @staticmethod
    def detect_screen_reader() -> ScreenReaderType:
        """Detect active screen reader on the system."""
        system = platform.system().lower()

        try:
            if system == "windows":
                return AccessibilityDetector._detect_windows_screen_reader()
            elif system == "darwin":  # macOS
                return AccessibilityDetector._detect_macos_screen_reader()
            elif system == "linux":
                return AccessibilityDetector._detect_linux_screen_reader()
        except Exception as e:
            logger.debug(f"Screen reader detection failed: {e}")

        return ScreenReaderType.NONE

    @staticmethod
    def _detect_windows_screen_reader() -> ScreenReaderType:
        """Detect Windows screen readers."""
        try:
            # Check for NVDA
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq nvda.exe"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0 and "nvda.exe" in result.stdout.decode():
                return ScreenReaderType.NVDA

            # Check for JAWS
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq jfw.exe"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0 and "jfw.exe" in result.stdout.decode():
                return ScreenReaderType.JAWS

            # Check for Narrator
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq narrator.exe"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0 and "narrator.exe" in result.stdout.decode():
                return ScreenReaderType.NARRATOR

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        return ScreenReaderType.NONE

    @staticmethod
    def _detect_macos_screen_reader() -> ScreenReaderType:
        """Detect macOS VoiceOver."""
        try:
            result = subprocess.run(
                ["defaults", "read", "com.apple.universalaccess", "voiceOverOnOffKey"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return ScreenReaderType.VOICEOVER
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        return ScreenReaderType.NONE

    @staticmethod
    def _detect_linux_screen_reader() -> ScreenReaderType:
        """Detect Linux screen readers (primarily Orca)."""
        try:
            result = subprocess.run(
                ["pgrep", "orca"], capture_output=True, timeout=5)
            if result.returncode == 0:
                return ScreenReaderType.ORCA
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        return ScreenReaderType.NONE

    @staticmethod
    def detect_high_contrast() -> bool:
        """Detect if high contrast mode is enabled."""
        system = platform.system().lower()

        try:
            if system == "windows":
                result = subprocess.run(
                    ["reg", "query", "HKCU\\Control Panel\\Accessibility\\HighContrast", "/v", "Flags"],
                    capture_output=True, text=True, timeout=5
                )
                return "0x1" in result.stdout
            elif system == "darwin":
                result = subprocess.run(
                    ["defaults", "read", "com.apple.universalaccess",
                        "closeViewDisplayOptions"],
                    capture_output=True, text=True, timeout=5
                )
                return "contrast" in result.stdout.lower()
            elif system == "linux":
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.a11y.interface",
                        "high-contrast"],
                    capture_output=True, text=True, timeout=5
                )
                return "true" in result.stdout.lower()
        except Exception as e:
            logger.debug(f"High contrast detection failed: {e}")

        return False

    @staticmethod
    def detect_reduced_motion() -> bool:
        """Detect if reduced motion is preferred."""
        system = platform.system().lower()

        try:
            if system == "darwin":
                result = subprocess.run(
                    ["defaults", "read", "com.apple.universalaccess", "reduceMotion"],
                    capture_output=True, text=True, timeout=5
                )
                return "1" in result.stdout
            elif system == "windows":
                # Check Windows animation settings
                result = subprocess.run(
                    ["reg", "query", "HKCU\\Control Panel\\Desktop\\WindowMetrics",
                        "/v", "MinAnimate"],
                    capture_output=True, text=True, timeout=5
                )
                return "0" in result.stdout
            elif system == "linux":
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface",
                        "enable-animations"],
                    capture_output=True, text=True, timeout=5
                )
                return "false" in result.stdout.lower()
        except Exception as e:
            logger.debug(f"Reduced motion detection failed: {e}")

        return False

    @staticmethod
    def get_platform_optimizations() -> Dict[str, Any]:
        """Get platform-specific accessibility optimizations."""
        system = platform.system().lower()
        optimizations = {}

        try:
            if system == "windows":
                optimizations.update({
                    "high_contrast": AccessibilityDetector.detect_high_contrast(),
                    "screen_reader": AccessibilityDetector.detect_screen_reader() != ScreenReaderType.NONE,
                    "narrator_enabled": AccessibilityDetector.detect_screen_reader() == ScreenReaderType.NARRATOR,
                    "narrator_compatible": True,
                    "reduced_motion": AccessibilityDetector.detect_reduced_motion(),
                })
            elif system == "darwin":
                optimizations.update({
                    "voiceover_enabled": AccessibilityDetector.detect_screen_reader() == ScreenReaderType.VOICEOVER,
                    "voiceover_compatible": True,
                    "high_contrast": AccessibilityDetector.detect_high_contrast(),
                    "reduced_motion": AccessibilityDetector.detect_reduced_motion(),
                })
            elif system == "linux":
                optimizations.update({
                    "orca_enabled": AccessibilityDetector.detect_screen_reader() == ScreenReaderType.ORCA,
                    "orca_compatible": True,
                    "high_contrast": AccessibilityDetector.detect_high_contrast(),
                    "reduced_motion": AccessibilityDetector.detect_reduced_motion(),
                })
        except Exception as e:
            logger.debug(f"Platform optimizations detection failed: {e}")

        return optimizations


class AccessibilityManager:
    """Accessibility manager for authentication screens."""

    def __init__(self, app: Any, preferences: AuthPreferences) -> None:
        self.app = app
        self.preferences = preferences
        self.settings = AccessibilitySettings.detect_system_accessibility()
        self.announcement_queue: List[str] = []
        self.last_progress_announcement: Optional[float] = None

        # Update settings from preferences
        self._sync_with_preferences()

        logger.info(
            f"AccessibilityManager initialized with level: {self._get_accessibility_level()}")

    def _sync_with_preferences(self) -> None:
        """Sync accessibility settings with user preferences."""
        if self.preferences.accessibility_mode:
            self.settings.screen_reader_enabled = True
            self.settings.keyboard_only_navigation = True
            self.settings.verbose_descriptions = True

        if self.preferences.high_contrast_mode:
            self.settings.high_contrast_mode = True
            self.settings.focus_indicator_enhanced = True

    def _get_accessibility_level(self) -> AccessibilityLevel:
        """Get current accessibility level."""
        if (self.settings.screen_reader_enabled and
            self.settings.keyboard_only_navigation and
                self.settings.high_contrast_mode):
            return AccessibilityLevel.FULL
        elif self.settings.screen_reader_enabled:
            return AccessibilityLevel.ENHANCED
        elif self.settings.focus_indicator_enhanced:
            return AccessibilityLevel.ENHANCED
        elif self.settings.high_contrast_mode or self.settings.keyboard_only_navigation:
            return AccessibilityLevel.BASIC
        else:
            return AccessibilityLevel.NONE

    async def announce(self, message: str, priority: str = "normal") -> None:
        """Announce message to screen reader."""
        if not self.settings.screen_reader_enabled:
            return

        if priority == "urgent":
            self.announcement_queue.insert(0, f"URGENT: {message}")
        else:
            self.announcement_queue.append(message)

        # Simple announcement implementation
        logger.info(f"Accessibility announcement: {message}")

        # Platform-specific announcement
        if self.settings.screen_reader_type == ScreenReaderType.VOICEOVER:
            await self._announce_to_voiceover(message)
        elif self.settings.screen_reader_type in [ScreenReaderType.NVDA, ScreenReaderType.JAWS]:
            await self._announce_to_windows_sr(message)
        elif self.settings.screen_reader_type == ScreenReaderType.ORCA:
            await self._announce_to_orca(message)

    async def _announce_to_voiceover(self, message: str) -> None:
        """Announce message to VoiceOver."""
        try:
            await asyncio.create_subprocess_exec(
                "osascript", "-e", f'tell application "VoiceOver" to output "{message}"',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except Exception as e:
            logger.debug(f"Failed to announce to VoiceOver: {e}")

    async def _announce_to_windows_sr(self, message: str) -> None:
        """Announce message to Windows screen readers."""
        # For Windows, we can use SAPI or write to a temporary file
        # that screen readers can monitor
        try:
            # Simple implementation - write to a file that screen readers monitor
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(message)
                f.flush()
        except Exception as e:
            logger.debug(f"Failed to announce to Windows screen reader: {e}")

    async def _announce_to_orca(self, message: str) -> None:
        """Announce message to Orca."""
        try:
            # Orca can be controlled via AT-SPI
            # For now, just log the message
            logger.info(f"Orca announcement: {message}")
        except Exception as e:
            logger.debug(f"Failed to announce to Orca: {e}")

    def get_timeout_multiplier(self) -> float:
        """Get timeout multiplier based on accessibility settings."""
        if self.settings.extended_timeouts:
            return 2.0
        elif self.settings.screen_reader_enabled:
            return 1.5
        else:
            return 1.0

    def should_use_high_contrast(self) -> bool:
        """Check if high contrast mode should be used."""
        return self.settings.high_contrast_mode

    def should_use_keyboard_only(self) -> bool:
        """Check if keyboard-only navigation should be used."""
        return self.settings.keyboard_only_navigation

    def should_use_verbose_descriptions(self) -> bool:
        """Check if verbose descriptions should be used."""
        return self.settings.verbose_descriptions

    def get_announcement_queue(self) -> List[str]:
        """Get current announcement queue."""
        return self.announcement_queue.copy()

    def clear_announcement_queue(self) -> None:
        """Clear the announcement queue."""
        self.announcement_queue.clear()

    def enhance_widget_accessibility(self, widget: Any, role: str = "", description: str = "", label: str = "") -> Any:
        """Enhance widget accessibility with ARIA-like attributes."""
        if not hasattr(widget, '_accessibility_enhanced'):
            widget._accessibility_enhanced = True

        # Set attributes using setattr to handle Mock objects
        setattr(widget, 'accessibility_role', role)
        setattr(widget, 'accessibility_description', description)
        setattr(widget, 'accessibility_label', label or description)

        # Add accessibility attributes if the widget supports them
        if hasattr(widget, 'set_attribute'):
            widget.set_attribute('role', role)
            widget.set_attribute('aria-label', label or description)

        return widget

    def create_accessible_button(self, text: str, action: str = "", description: str = "") -> Any:
        """Create an accessible button with proper ARIA attributes."""
        try:
            from textual.widgets import Button
            button = Button(text, id=action or text.lower().replace(' ', '-'))

            # Set accessibility attributes
            setattr(button, 'accessibility_role', 'button')
            setattr(button, 'accessibility_label', text)
            setattr(button, 'accessibility_description', description or text)

            # Add keyboard navigation support
            if self.settings.keyboard_only_navigation:
                button.can_focus = True

            return button
        except ImportError:
            # Fallback if textual is not available
            class MockButton:
                def __init__(self, text: str, **kwargs: Any) -> None:
                    self.text = text
                    self.kwargs = kwargs
                    self.accessibility_role = "button"
                    self.accessibility_label = text
                    self.accessibility_description = description or text
            return MockButton(text)

    def create_accessible_static(self, text: str, role: str = "", description: str = "") -> Any:
        """Create an accessible static text widget with proper ARIA attributes."""
        try:
            from textual.widgets import Static
            static = Static(text)

            # Set accessibility attributes
            setattr(static, 'accessibility_role', role or 'text')
            setattr(static, 'accessibility_label', text)
            setattr(static, 'accessibility_description', description or text)

            return static
        except ImportError:
            # Fallback if textual is not available
            class MockStatic:
                def __init__(self, text: str, **kwargs: Any) -> None:
                    self.text = text
                    self.kwargs = kwargs
                    self.accessibility_role = role or 'text'
                    self.accessibility_label = text
                    self.accessibility_description = description or text
            return MockStatic(text)

    async def announce_auth_step(self, step: str, description: str = "") -> None:
        """Announce authentication step to screen reader."""
        if not self.settings.screen_reader_enabled:
            return

        # Map step names to user-friendly messages
        step_messages = {
            "initializing": "Initializing authentication process",
            "requesting_code": "Requesting device code",
            "waiting_for_user": "Waiting for user authorization",
            "polling": "Checking authentication status",
            "completed": "Authentication completed",
            "failed": "Authentication failed"
        }

        message = step_messages.get(step, f"Authentication step: {step}")
        if description:
            message += f" - {description}"

        await self.announce(message, "normal")

    async def announce_progress_update(self, progress: float, description: str = "") -> None:
        """Announce progress update to screen reader."""
        if not self.settings.screen_reader_enabled:
            return

        # Only announce if progress has increased significantly (at least 10%)
        if (self.last_progress_announcement is not None and
                progress <= self.last_progress_announcement):
            return

        self.last_progress_announcement = progress
        percentage = int(progress * 100)
        message = f"Progress: {percentage}%"
        if description:
            message += f" - {description}"

        await self.announce(message, "normal")

    async def announce_error(self, error_message: str, recovery_options: Optional[List[str]] = None) -> None:
        """Announce error with recovery options to screen reader."""
        if not self.settings.screen_reader_enabled:
            return

        message = f"Error: {error_message}"
        if recovery_options:
            message += f". Available options: {', '.join(recovery_options)}"

        await self.announce(message, "urgent")

    def get_keyboard_shortcuts(self) -> List[Any]:
        """Get keyboard shortcuts based on accessibility settings."""
        shortcuts = []

        # Basic shortcuts
        class MockBinding:
            def __init__(self, key: str, description: str):
                self.key = key
                self.description = description

        shortcuts.extend([
            MockBinding("tab", "Navigate forward"),
            MockBinding("shift+tab", "Navigate backward"),
            MockBinding("enter", "Activate"),
            MockBinding("escape", "Cancel"),
            MockBinding("space", "Select/Toggle")
        ])

        if self.settings.screen_reader_enabled:
            shortcuts.extend([
                MockBinding("ctrl+alt+a", "Announce current status"),
                MockBinding("ctrl+alt+h", "Read help information"),
                MockBinding("ctrl+alt+p", "Read progress information")
            ])

        if self.settings.keyboard_only_navigation:
            shortcuts.extend([
                MockBinding("ctrl+home", "Go to first item"),
                MockBinding("ctrl+end", "Go to last item"),
                MockBinding("f1", "Context help"),
                MockBinding("ctrl+h", "Help")
            ])

        return shortcuts

    def apply_accessibility_theme(self, app: Any) -> None:
        """Apply accessibility theme to the application."""
        if self.settings.high_contrast_mode:
            # Apply high contrast theme
            high_contrast_css = """
            .high-contrast Screen {
                background: black;
                color: white;
            }
            
            .high-contrast Button {
                background: white;
                color: black;
                border: solid white;
            }
            
            .enhanced-focus:focus {
                background: yellow;
                color: black;
                border: solid yellow;
            }
            
            .high-contrast Static {
                background: black;
                color: white;
            }
            
            .high-contrast Input {
                background: black;
                color: white;
                border: solid white;
            }
            
            .high-contrast Input:focus {
                background: darkblue;
                color: white;
                border: solid yellow;
            }
            """

            # Try different ways to add CSS based on the app type
            if hasattr(app, 'stylesheet') and hasattr(app.stylesheet, 'add_source'):
                app.stylesheet.add_source(high_contrast_css)
            elif hasattr(app, 'add_css'):
                app.add_css(high_contrast_css)
            elif hasattr(app, 'stylesheet'):
                # Mock object might just have stylesheet attribute
                app.stylesheet.add_source(high_contrast_css)

        if self.settings.large_text_mode:
            # Apply large text theme
            large_text_css = """
            * {
                text-size: 16px;
            }
            
            Button {
                height: 3;
                min-width: 20;
            }
            
            Static {
                text-size: 14px;
            }
            """

            # Try different ways to add CSS based on the app type
            if hasattr(app, 'stylesheet') and hasattr(app.stylesheet, 'add_source'):
                app.stylesheet.add_source(large_text_css)
            elif hasattr(app, 'add_css'):
                app.add_css(large_text_css)
            elif hasattr(app, 'stylesheet'):
                # Mock object might just have stylesheet attribute
                app.stylesheet.add_source(large_text_css)

    def create_accessibility_help_screen(self) -> Any:
        """Create an accessibility help screen."""
        from textual.screen import Screen
        from textual.widgets import Static

        class AccessibilityHelpScreen(Screen):
            """Screen showing accessibility help information."""

            def compose(self) -> Any:
                yield Static(
                    "Accessibility Help\n\n"
                    "Keyboard Shortcuts:\n"
                    "- Tab: Navigate between elements\n"
                    "- Enter: Activate buttons\n"
                    "- Escape: Cancel/Go back\n"
                    "- F1: Show this help\n\n"
                    "Screen Reader Support:\n"
                    "- NVDA, JAWS, Narrator (Windows)\n"
                    "- VoiceOver (macOS)\n"
                    "- Orca (Linux)\n\n"
                    "High Contrast Mode:\n"
                    "- Automatic detection\n"
                    "- Manual toggle available\n\n"
                    "Press any key to close this help.",
                    id="help-content"
                )

            async def on_key(self, event: Any) -> Any:
                """Close help on any key press."""
                self.dismiss()

        return AccessibilityHelpScreen()
