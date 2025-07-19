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
]
