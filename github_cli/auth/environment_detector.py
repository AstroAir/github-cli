"""Environment detection and adaptation for authentication flows."""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
from loguru import logger


@dataclass
class EnvironmentCapabilities:
    """Detected environment capabilities."""

    has_display: bool
    has_browser: bool
    has_clipboard: bool
    is_headless: bool
    is_ssh_session: bool
    is_container: bool
    network_restricted: bool
    terminal_type: str
    platform_info: str
    available_browsers: list[str]
    clipboard_commands: dict[str, str]


class EnvironmentDetector:
    """Detects environment capabilities and provides adaptation strategies."""

    def __init__(self):
        self._capabilities: Optional[EnvironmentCapabilities] = None
        self._network_diagnostics: dict[str, Any] = {}

    async def detect_capabilities(self) -> EnvironmentCapabilities:
        """Detect current environment capabilities."""
        if self._capabilities is None:
            self._capabilities = await self._perform_detection()
        return self._capabilities

    async def _perform_detection(self) -> EnvironmentCapabilities:
        """Perform comprehensive environment detection."""
        logger.debug("Starting environment capability detection")

        # Detect display availability
        has_display = self._detect_display()

        # Detect browser availability
        available_browsers = await self._detect_browsers()
        has_browser = len(available_browsers) > 0

        # Detect clipboard capabilities
        clipboard_commands = self._detect_clipboard()
        has_clipboard = len(clipboard_commands) > 0

        # Detect headless environment
        is_headless = self._detect_headless()

        # Detect SSH session
        is_ssh_session = self._detect_ssh_session()

        # Detect container environment
        is_container = self._detect_container()

        # Detect network restrictions
        network_restricted = await self._detect_network_restrictions()

        # Get terminal and platform info
        terminal_type = self._detect_terminal_type()
        platform_info = self._get_platform_info()

        capabilities = EnvironmentCapabilities(
            has_display=has_display,
            has_browser=has_browser,
            has_clipboard=has_clipboard,
            is_headless=is_headless,
            is_ssh_session=is_ssh_session,
            is_container=is_container,
            network_restricted=network_restricted,
            terminal_type=terminal_type,
            platform_info=platform_info,
            available_browsers=available_browsers,
            clipboard_commands=clipboard_commands
        )

        logger.info(f"Environment detection complete: {capabilities}")
        return capabilities

    def _detect_display(self) -> bool:
        """Detect if a display server is available."""
        try:
            # Check for X11 display
            if os.environ.get('DISPLAY'):
                return True

            # Check for Wayland
            if os.environ.get('WAYLAND_DISPLAY'):
                return True

            # Check for Windows display
            if platform.system() == 'Windows':
                return True

            # Check for macOS display
            if platform.system() == 'Darwin':
                return True

            return False
        except Exception as e:
            logger.warning(f"Error detecting display: {e}")
            return False

    async def _detect_browsers(self) -> list[str]:
        """Detect available web browsers."""
        browsers = []

        # Common browser executables by platform
        if platform.system() == 'Windows':
            browser_candidates = [
                'chrome.exe', 'firefox.exe', 'msedge.exe', 'iexplore.exe',
                'opera.exe', 'brave.exe'
            ]
        elif platform.system() == 'Darwin':
            browser_candidates = [
                'open',  # macOS default browser opener
                'google-chrome', 'firefox', 'safari', 'opera', 'brave'
            ]
        else:  # Linux and other Unix-like systems
            browser_candidates = [
                'google-chrome', 'chromium', 'firefox', 'opera', 'brave-browser',
                'epiphany', 'konqueror', 'lynx', 'w3m', 'links'
            ]

        for browser in browser_candidates:
            if shutil.which(browser):
                browsers.append(browser)

        # Special handling for macOS
        if platform.system() == 'Darwin' and 'open' in browsers:
            # 'open' is always available on macOS and can open default browser
            browsers = ['open'] + [b for b in browsers if b != 'open']

        logger.debug(f"Detected browsers: {browsers}")
        return browsers

    def _detect_clipboard(self) -> dict[str, str]:
        """Detect clipboard access methods."""
        clipboard_commands = {}

        if platform.system() == 'Windows':
            # Windows clipboard
            if shutil.which('clip'):
                clipboard_commands['copy'] = 'clip'
            if shutil.which('powershell'):
                clipboard_commands['paste'] = 'powershell -command "Get-Clipboard"'

        elif platform.system() == 'Darwin':
            # macOS clipboard
            if shutil.which('pbcopy'):
                clipboard_commands['copy'] = 'pbcopy'
            if shutil.which('pbpaste'):
                clipboard_commands['paste'] = 'pbpaste'

        else:
            # Linux/Unix clipboard
            if shutil.which('xclip'):
                clipboard_commands['copy'] = 'xclip -selection clipboard'
                clipboard_commands['paste'] = 'xclip -selection clipboard -o'
            elif shutil.which('xsel'):
                clipboard_commands['copy'] = 'xsel --clipboard --input'
                clipboard_commands['paste'] = 'xsel --clipboard --output'
            elif shutil.which('wl-copy') and shutil.which('wl-paste'):
                # Wayland clipboard
                clipboard_commands['copy'] = 'wl-copy'
                clipboard_commands['paste'] = 'wl-paste'

        logger.debug(f"Detected clipboard commands: {clipboard_commands}")
        return clipboard_commands

    def _detect_headless(self) -> bool:
        """Detect if running in a headless environment."""
        # Check common headless indicators
        headless_indicators = [
            not self._detect_display(),
            os.environ.get('CI') is not None,
            os.environ.get('GITHUB_ACTIONS') is not None,
            os.environ.get('JENKINS_URL') is not None,
            os.environ.get('BUILDKITE') is not None,
            os.environ.get('TRAVIS') is not None,
            'headless' in os.environ.get('DISPLAY', '').lower(),
        ]

        return any(headless_indicators)

    def _detect_ssh_session(self) -> bool:
        """Detect if running in an SSH session."""
        return any([
            os.environ.get('SSH_CLIENT') is not None,
            os.environ.get('SSH_CONNECTION') is not None,
            os.environ.get('SSH_TTY') is not None,
        ])

    def _detect_container(self) -> bool:
        """Detect if running in a container environment."""
        container_indicators = [
            os.path.exists('/.dockerenv'),
            os.environ.get('container') is not None,
            os.environ.get('KUBERNETES_SERVICE_HOST') is not None,
            'docker' in os.environ.get('HOSTNAME', '').lower(),
        ]

        # Check for container-specific cgroup
        try:
            with open('/proc/1/cgroup', 'r') as f:
                cgroup_content = f.read()
                if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                    container_indicators.append(True)
        except (FileNotFoundError, PermissionError):
            pass

        return any(container_indicators)

    async def _detect_network_restrictions(self) -> bool:
        """Detect network restrictions that might affect authentication."""
        try:
            # Test connectivity to GitHub
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get('https://api.github.com') as response:
                    if response.status == 200:
                        self._network_diagnostics['github_accessible'] = True
                        return False
                    else:
                        self._network_diagnostics['github_accessible'] = False
                        self._network_diagnostics['github_status'] = response.status
                        return True
        except Exception as e:
            logger.warning(f"Network connectivity test failed: {e}")
            self._network_diagnostics['github_accessible'] = False
            self._network_diagnostics['error'] = str(e)
            return True

    def _detect_terminal_type(self) -> str:
        """Detect the terminal type."""
        return os.environ.get('TERM', 'unknown')

    def _get_platform_info(self) -> str:
        """Get platform information."""
        return f"{platform.system()} {platform.release()} ({platform.machine()})"

    async def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard if available."""
        capabilities = await self.detect_capabilities()

        if not capabilities.has_clipboard:
            return False

        copy_command = capabilities.clipboard_commands.get('copy')
        if not copy_command:
            return False

        try:
            process = await asyncio.create_subprocess_shell(
                copy_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate(text.encode())

            if process.returncode == 0:
                logger.debug("Successfully copied to clipboard")
                return True
            else:
                logger.warning(f"Clipboard copy failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False

    async def open_browser(self, url: str) -> bool:
        """Attempt to open URL in browser."""
        capabilities = await self.detect_capabilities()

        if not capabilities.has_browser:
            return False

        for browser in capabilities.available_browsers:
            try:
                if platform.system() == 'Darwin' and browser == 'open':
                    # macOS default browser
                    process = await asyncio.create_subprocess_exec(
                        'open', url,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif platform.system() == 'Windows':
                    # Windows browser
                    process = await asyncio.create_subprocess_exec(
                        browser, url,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    # Linux/Unix browser
                    process = await asyncio.create_subprocess_exec(
                        browser, url,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    logger.info(f"Successfully opened browser: {browser}")
                    return True
                else:
                    logger.warning(
                        f"Browser {browser} failed: {stderr.decode()}")
                    continue

            except Exception as e:
                logger.warning(f"Error opening browser {browser}: {e}")
                continue

        return False

    async def get_network_diagnostics(self) -> dict[str, Any]:
        """Get network diagnostics information."""
        await self.detect_capabilities()  # Ensure diagnostics are populated
        return self._network_diagnostics.copy()

    async def get_troubleshooting_info(self) -> dict[str, Any]:
        """Get comprehensive troubleshooting information."""
        capabilities = await self.detect_capabilities()
        diagnostics = await self.get_network_diagnostics()

        return {
            'environment': {
                'platform': capabilities.platform_info,
                'terminal': capabilities.terminal_type,
                'headless': capabilities.is_headless,
                'ssh_session': capabilities.is_ssh_session,
                'container': capabilities.is_container,
            },
            'capabilities': {
                'display': capabilities.has_display,
                'browser': capabilities.has_browser,
                'clipboard': capabilities.has_clipboard,
                'available_browsers': capabilities.available_browsers,
            },
            'network': diagnostics,
            'recommendations': self._generate_recommendations(capabilities, diagnostics)
        }

    def _generate_recommendations(self, capabilities: EnvironmentCapabilities, diagnostics: dict[str, Any]) -> list[str]:
        """Generate troubleshooting recommendations."""
        recommendations = []

        if capabilities.is_headless:
            recommendations.append(
                "Running in headless mode - manual URL entry required")

        if not capabilities.has_browser:
            recommendations.append(
                "No browser detected - use manual authentication flow")

        if not capabilities.has_clipboard:
            recommendations.append(
                "Clipboard not available - URLs must be copied manually")

        if capabilities.network_restricted:
            recommendations.append(
                "Network restrictions detected - check firewall/proxy settings")

        if capabilities.is_ssh_session:
            recommendations.append(
                "SSH session detected - consider port forwarding for browser access")

        if capabilities.is_container:
            recommendations.append(
                "Container environment - ensure network access to GitHub")

        if not diagnostics.get('github_accessible', True):
            recommendations.append(
                "GitHub API not accessible - check network connectivity")

        return recommendations
