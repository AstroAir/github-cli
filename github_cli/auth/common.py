"""
Common imports and utilities for the authentication system.

This module provides centralized imports and utility functions to reduce
code duplication across the authentication system.
"""

from __future__ import annotations

import asyncio
import platform
import subprocess
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

# Logging setup with fallback
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Textual UI components
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Button, Static, Label, Checkbox, RadioSet, RadioButton, Select, ProgressBar
from textual.screen import Screen
from textual.binding import Binding
from textual.message import Message
from textual.events import Key, Focus, Blur

# Import authentication-related classes
from github_cli.utils.exceptions import AuthenticationError

# Define authentication enums and classes here to avoid circular imports
class AuthErrorType(Enum):
    """Types of authentication errors."""
    NETWORK = "network"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    USER_DENIED = "user_denied"
    DEVICE_CODE_EXPIRED = "device_code_expired"
    RATE_LIMITED = "rate_limited"
    BROWSER_UNAVAILABLE = "browser_unavailable"
    CLIPBOARD_UNAVAILABLE = "clipboard_unavailable"
    ENVIRONMENT_RESTRICTED = "environment_restricted"
    UNKNOWN = "unknown"


class AuthRecoveryAction(Enum):
    """Possible recovery actions for authentication errors."""
    RETRY = "retry"
    RESTART_FLOW = "restart_flow"
    MANUAL_AUTH = "manual_auth"
    WAIT_AND_RETRY = "wait_and_retry"
    CANCEL = "cancel"
    SHOW_HELP = "show_help"


@dataclass(frozen=True, slots=True)
class AuthResult:
    """Result of authentication attempt."""
    success: bool
    user_info: dict[str, Any] | None = None
    error: Exception | None = None
    retry_suggested: bool = False
    preferences_updated: bool = False
    recovery_action: AuthRecoveryAction | None = None
    error_type: AuthErrorType | None = None

# Common re-exports for convenience
__all__ = [
    # Basic types
    'Any', 'Dict', 'List', 'Optional', 'Callable', 'Enum',
    'dataclass', 'field', 'asyncio', 'platform', 'subprocess',
    # Logging
    'logger',
    # Textual components
    'ComposeResult', 'Container', 'Horizontal', 'Vertical', 'Grid',
    'Button', 'Static', 'Label', 'Checkbox', 'RadioSet', 'RadioButton',
    'Select', 'ProgressBar', 'Screen', 'Binding', 'Message', 'Key', 'Focus', 'Blur',
    # Authentication classes
    'AuthResult', 'AuthenticationError', 'AuthErrorType', 'AuthRecoveryAction',
]
