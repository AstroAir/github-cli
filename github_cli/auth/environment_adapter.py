"""Environment adaptation strategies for authentication flows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .environment_detector import EnvironmentDetector, EnvironmentCapabilities


class AuthStrategy(Enum):
    """Available authentication strategies."""

    BROWSER_AUTO = "browser_auto"      # Automatic browser opening
    BROWSER_MANUAL = "browser_manual"  # Manual browser with URL copy
    TEXT_ONLY = "text_only"           # Text-only instructions
    QR_CODE = "qr_code"               # QR code display
    FALLBACK = "fallback"             # Basic fallback method


@dataclass
class AuthInstructions:
    """Authentication instructions for different environments."""

    strategy: AuthStrategy
    primary_message: str
    detailed_steps: list[str]
    url: str
    device_code: str
    clipboard_available: bool
    qr_code_data: Optional[str] = None
    troubleshooting_info: Optional[dict[str, Any]] = None


class EnvironmentAdapter:
    """Adapts authentication flow based on environment capabilities."""

    def __init__(self, detector: Optional[EnvironmentDetector] = None):
        self.detector = detector or EnvironmentDetector()
        self.console = Console()
        self._capabilities: Optional[EnvironmentCapabilities] = None

    async def get_capabilities(self) -> EnvironmentCapabilities:
        """Get cached environment capabilities."""
        if self._capabilities is None:
            self._capabilities = await self.detector.detect_capabilities()
        return self._capabilities

    async def determine_auth_strategy(self) -> AuthStrategy:
        """Determine the best authentication strategy for current environment."""
        capabilities = await self.get_capabilities()

        # Headless environments need text-only instructions
        if capabilities.is_headless:
            logger.info("Using text-only strategy for headless environment")
            return AuthStrategy.TEXT_ONLY

        # For SSH sessions or containers, prefer manual approach
        if capabilities.is_ssh_session or capabilities.is_container:
            logger.info(
                "Using manual browser strategy for SSH/container environment")
            return AuthStrategy.BROWSER_MANUAL

        # If browser is available and display exists, try automatic browser
        if capabilities.has_browser and capabilities.has_display:
            logger.info("Using automatic browser strategy")
            return AuthStrategy.BROWSER_AUTO

        # If no browser but display exists, use manual browser with instructions
        if capabilities.has_display and not capabilities.has_browser:
            logger.info("Using manual browser strategy (no browser detected)")
            return AuthStrategy.BROWSER_MANUAL

        # Fallback to text-only for unknown environments
        logger.info("Using text-only fallback strategy")
        return AuthStrategy.TEXT_ONLY

    async def create_auth_instructions(self, url: str, device_code: str) -> AuthInstructions:
        """Create authentication instructions based on environment."""
        strategy = await self.determine_auth_strategy()
        capabilities = await self.get_capabilities()

        # Try to copy URL to clipboard if available
        clipboard_success = False
        if capabilities.has_clipboard:
            clipboard_success = await self.detector.copy_to_clipboard(url)

        # Generate QR code data if needed
        qr_code_data = None
        if strategy in [AuthStrategy.QR_CODE, AuthStrategy.TEXT_ONLY]:
            qr_code_data = self._generate_qr_code_ascii(url)

        # Get troubleshooting info for complex environments
        troubleshooting_info = None
        if capabilities.network_restricted or capabilities.is_container:
            troubleshooting_info = await self.detector.get_troubleshooting_info()

        return AuthInstructions(
            strategy=strategy,
            primary_message=self._get_primary_message(
                strategy, clipboard_success),
            detailed_steps=self._get_detailed_steps(
                strategy, url, device_code, capabilities),
            url=url,
            device_code=device_code,
            clipboard_available=clipboard_success,
            qr_code_data=qr_code_data,
            troubleshooting_info=troubleshooting_info
        )

    def _get_primary_message(self, strategy: AuthStrategy, clipboard_success: bool) -> str:
        """Get the primary message for the authentication strategy."""
        messages = {
            AuthStrategy.BROWSER_AUTO: "Opening browser for GitHub authentication...",
            AuthStrategy.BROWSER_MANUAL: "Manual browser authentication required",
            AuthStrategy.TEXT_ONLY: "Text-only authentication mode",
            AuthStrategy.QR_CODE: "QR code authentication available",
            AuthStrategy.FALLBACK: "Basic authentication mode"
        }

        base_message = messages.get(strategy, "GitHub authentication required")

        if clipboard_success:
            base_message += " (URL copied to clipboard)"

        return base_message

    def _get_detailed_steps(self, strategy: AuthStrategy, url: str, device_code: str,
                            capabilities: EnvironmentCapabilities) -> list[str]:
        """Get detailed steps for the authentication strategy."""
        steps = []

        if strategy == AuthStrategy.BROWSER_AUTO:
            steps.extend([
                "1. Browser should open automatically",
                f"2. If browser doesn't open, visit: {url}",
                f"3. Enter device code: {device_code}",
                "4. Authorize the GitHub CLI application",
                "5. Return to this terminal when complete"
            ])

        elif strategy == AuthStrategy.BROWSER_MANUAL:
            steps.extend([
                "1. Open your web browser",
                f"2. Navigate to: {url}",
                f"3. Enter device code: {device_code}",
                "4. Authorize the GitHub CLI application",
                "5. Return to this terminal when complete"
            ])

            if capabilities.has_clipboard:
                steps.insert(1, "   (URL has been copied to clipboard)")

        elif strategy == AuthStrategy.TEXT_ONLY:
            steps.extend([
                "HEADLESS AUTHENTICATION MODE",
                "",
                f"Device Code: {device_code}",
                f"Verification URL: {url}",
                "",
                "Instructions:",
                "1. Copy the verification URL above",
                "2. Open it in a browser on any device",
                "3. Enter the device code when prompted",
                "4. Authorize the GitHub CLI application",
                "5. Authentication will complete automatically"
            ])

        elif strategy == AuthStrategy.QR_CODE:
            steps.extend([
                "1. Scan the QR code below with your mobile device",
                f"2. Or manually visit: {url}",
                f"3. Enter device code: {device_code}",
                "4. Authorize the GitHub CLI application"
            ])

        else:  # FALLBACK
            steps.extend([
                f"1. Visit: {url}",
                f"2. Enter code: {device_code}",
                "3. Authorize the application"
            ])

        return steps

    def _generate_qr_code_ascii(self, url: str) -> Optional[str]:
        """Generate ASCII QR code for the URL."""
        try:
            import qrcode

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=1,
                border=1,
            )
            qr.add_data(url)
            qr.make(fit=True)

            # Generate ASCII representation
            qr_ascii = []
            matrix = qr.get_matrix()

            for row in matrix:
                line = ""
                for cell in row:
                    line += "██" if cell else "  "
                qr_ascii.append(line)

            return "\n".join(qr_ascii)

        except ImportError:
            logger.warning(
                "qrcode library not available for QR code generation")
            return None
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None

    async def attempt_browser_open(self, url: str) -> bool:
        """Attempt to open URL in browser."""
        return await self.detector.open_browser(url)

    async def display_auth_instructions(self, instructions: AuthInstructions) -> None:
        """Display authentication instructions using Rich formatting."""

        # Create main instruction panel
        instruction_text = Text()
        instruction_text.append(
            instructions.primary_message, style="bold blue")
        instruction_text.append("\n\n")

        for step in instructions.detailed_steps:
            if step.startswith("HEADLESS") or step == "":
                instruction_text.append(
                    step + "\n", style="bold yellow" if step.startswith("HEADLESS") else "")
            elif step.startswith(("Device Code:", "Verification URL:")):
                instruction_text.append(step + "\n", style="bold green")
            elif step == "Instructions:":
                instruction_text.append(step + "\n", style="bold")
            else:
                instruction_text.append(step + "\n")

        panel = Panel(
            instruction_text,
            title="GitHub Authentication",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)

        # Display QR code if available
        if instructions.qr_code_data:
            qr_panel = Panel(
                instructions.qr_code_data,
                title="QR Code",
                border_style="green",
                padding=(1, 1)
            )
            self.console.print("\n")
            self.console.print(qr_panel)

        # Display troubleshooting info if available
        if instructions.troubleshooting_info:
            await self._display_troubleshooting_info(instructions.troubleshooting_info)

    async def _display_troubleshooting_info(self, info: dict[str, Any]) -> None:
        """Display troubleshooting information."""
        troubleshooting_text = Text()

        # Environment info
        env = info.get('environment', {})
        troubleshooting_text.append("Environment:\n", style="bold")
        troubleshooting_text.append(
            f"  Platform: {env.get('platform', 'Unknown')}\n")
        troubleshooting_text.append(
            f"  Terminal: {env.get('terminal', 'Unknown')}\n")
        troubleshooting_text.append(
            f"  Headless: {env.get('headless', False)}\n")
        troubleshooting_text.append(
            f"  SSH Session: {env.get('ssh_session', False)}\n")
        troubleshooting_text.append(
            f"  Container: {env.get('container', False)}\n\n")

        # Capabilities
        caps = info.get('capabilities', {})
        troubleshooting_text.append("Capabilities:\n", style="bold")
        troubleshooting_text.append(
            f"  Display: {caps.get('display', False)}\n")
        troubleshooting_text.append(
            f"  Browser: {caps.get('browser', False)}\n")
        troubleshooting_text.append(
            f"  Clipboard: {caps.get('clipboard', False)}\n\n")

        # Recommendations
        recommendations = info.get('recommendations', [])
        if recommendations:
            troubleshooting_text.append(
                "Recommendations:\n", style="bold yellow")
            for rec in recommendations:
                troubleshooting_text.append(f"  • {rec}\n")

        panel = Panel(
            troubleshooting_text,
            title="Troubleshooting Information",
            border_style="yellow",
            padding=(1, 2)
        )

        self.console.print("\n")
        self.console.print(panel)

    async def handle_auth_timeout(self, timeout_seconds: int) -> bool:
        """Handle authentication timeout with environment-appropriate messaging."""
        capabilities = await self.get_capabilities()

        if capabilities.is_headless:
            self.console.print(
                f"\n[yellow]Authentication timeout ({timeout_seconds}s). Please complete authentication in browser.[/yellow]")
        else:
            self.console.print(
                f"\n[yellow]Authentication timeout after {timeout_seconds} seconds.[/yellow]")
            self.console.print(
                "[yellow]Please check your browser and complete the authorization.[/yellow]")

        # Offer to restart or continue waiting
        if capabilities.has_display:
            self.console.print(
                "\n[blue]Press Enter to continue waiting, or Ctrl+C to cancel[/blue]")
            try:
                await asyncio.get_event_loop().run_in_executor(None, input)
                return True  # Continue waiting
            except KeyboardInterrupt:
                return False  # Cancel
        else:
            # In headless mode, continue waiting automatically
            return True

    async def handle_network_error(self, error: Exception) -> dict[str, Any]:
        """Handle network errors with environment-specific guidance."""
        capabilities = await self.get_capabilities()
        diagnostics = await self.detector.get_network_diagnostics()

        error_info = {
            'error': str(error),
            'environment': {
                'container': capabilities.is_container,
                'ssh_session': capabilities.is_ssh_session,
                'network_restricted': capabilities.network_restricted
            },
            'diagnostics': diagnostics,
            'suggestions': []
        }

        # Add environment-specific suggestions
        if capabilities.is_container:
            error_info['suggestions'].extend([
                "Check container network configuration",
                "Ensure GitHub API access is allowed",
                "Verify DNS resolution works"
            ])

        if capabilities.is_ssh_session:
            error_info['suggestions'].extend([
                "Check SSH tunnel configuration",
                "Verify network access from SSH host",
                "Consider using local authentication"
            ])

        if capabilities.network_restricted:
            error_info['suggestions'].extend([
                "Check firewall settings",
                "Verify proxy configuration",
                "Test GitHub API connectivity"
            ])

        return error_info
