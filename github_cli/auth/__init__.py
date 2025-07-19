"""
GitHub CLI authentication modules
"""

# Import only lightweight modules by default to avoid dependency issues
# Heavy modules with external dependencies should be imported explicitly

__all__ = [
    'EnvironmentDetector',
    'EnvironmentCapabilities',
    'EnvironmentAdapter',
    'AuthStrategy',
    'AuthInstructions',
    'AccessibilityManager',
    'AccessibilitySettings',
    'AuthPreferences'
]


def get_environment_detector():
    """Lazy import of EnvironmentDetector to avoid dependency issues."""
    from .environment_detector import EnvironmentDetector, EnvironmentCapabilities
    return EnvironmentDetector, EnvironmentCapabilities


def get_environment_adapter():
    """Lazy import of EnvironmentAdapter to avoid dependency issues."""
    from .environment_adapter import EnvironmentAdapter, AuthStrategy, AuthInstructions
    return EnvironmentAdapter, AuthStrategy, AuthInstructions


def get_accessibility_components():
    """Get accessibility components."""
    from .accessibility import AccessibilityManager, AccessibilitySettings
    return AccessibilityManager, AccessibilitySettings


def get_preferences():
    """Get preferences component."""
    from .preferences import AuthPreferences
    return AuthPreferences
