# Authentication System

The GitHub CLI authentication system provides secure, user-friendly OAuth device flow authentication with comprehensive token management, SSO support, and adaptive user interfaces.

## 🏗️ Architecture Overview

The authentication system is built with a modular architecture:

```
github_cli/auth/
├── authenticator.py           # Core OAuth device flow
├── token_manager.py          # Token storage and lifecycle
├── sso_handler.py           # Single Sign-On support
├── environment_detector.py  # Environment capability detection
├── environment_adapter.py   # Adaptive authentication strategies
├── token_expiration_handler.py # Token refresh and expiration
├── visual_feedback.py       # User interface components
├── accessibility.py         # Accessibility features
├── preferences.py           # User preference management
└── error_recovery_workflows.py # Error handling and recovery
```

## 🔧 Core Components

### Authenticator

The central authentication handler that orchestrates the OAuth device flow:

```python
class Authenticator:
    """Enhanced GitHub authentication handler with modern Python features."""
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self._auth_config = AuthenticationConfig()
```

**Key Features:**
- OAuth 2.0 device flow implementation
- Automatic token refresh
- SSO challenge handling
- Environment-adaptive authentication
- Comprehensive error recovery

### Token Manager

Handles secure token storage and lifecycle management:

```python
class TokenManager:
    """Manager for GitHub authentication tokens"""
    
    def __init__(self, config: Config):
        self.config = config
        self.tokens_dir = config.config_dir / 'tokens'
```

**Features:**
- Secure token storage using system keyring
- Multiple token support
- Automatic expiration handling
- Token rotation and cleanup

### SSO Handler

Manages Single Sign-On authentication for organizations:

```python
class SSOHandler:
    """Handler for GitHub SSO authentication"""
    
    async def handle_sso_challenge(self, response_headers: Dict[str, str], token: str) -> None
```

## 🔐 OAuth Device Flow

The authentication system uses GitHub's OAuth device flow for secure, user-friendly authentication:

### Flow Overview

1. **Device Code Request**: Request a device code from GitHub
2. **User Instructions**: Display authentication URL and user code
3. **User Authorization**: User authorizes the application in browser
4. **Token Polling**: Poll GitHub for access token
5. **Token Storage**: Securely store the access token
6. **User Info**: Fetch and cache user information

### Implementation

```python
async def login_interactive(
    self,
    scopes: str | None = None,
    sso: str | None = None
) -> None:
    """Enhanced interactive OAuth device flow login"""
    
    # Start device flow
    device_code_data = await self._request_device_code(scopes)
    
    # Display user instructions
    await self._display_auth_instructions(device_code_data)
    
    # Poll for token
    token_data = await self._poll_for_token(device_code, interval)
    
    # Save token
    token = self.token_manager.save_token(token_data)
```

## 🎯 Authentication Strategies

The system adapts to different environments and user preferences:

### Available Strategies

```python
class AuthStrategy(Enum):
    BROWSER_AUTO = "browser_auto"      # Automatic browser opening
    BROWSER_MANUAL = "browser_manual"  # Manual browser with URL copy
    TEXT_ONLY = "text_only"           # Text-only instructions
    QR_CODE = "qr_code"               # QR code display
    FALLBACK = "fallback"             # Basic fallback method
```

### Environment Detection

```python
@dataclass
class EnvironmentCapabilities:
    has_display: bool
    has_browser: bool
    has_clipboard: bool
    has_qr_support: bool
    terminal_width: int
    terminal_height: int
    is_ssh: bool
    is_ci: bool
```

## 🔑 Token Management

### Token Storage

Tokens are stored securely using multiple layers:

1. **System Keyring**: Primary storage using OS keyring
2. **Encrypted Files**: Fallback encrypted file storage
3. **Memory Cache**: Runtime token caching

### Token Lifecycle

```python
# Save new token
token = token_manager.save_token(token_data)

# Get active token
current_token = token_manager.get_active_token()

# List all tokens
tokens = token_manager.list_tokens()

# Delete token
token_manager.delete_token(token_prefix)

# Set active token
token_manager.set_active_token(token_prefix)
```

### Token Expiration

```python
class TokenExpirationHandler:
    """Handles token expiration and refresh"""
    
    async def with_token_validation(
        self,
        operation: str,
        endpoint: str,
        user_message: str
    ) -> AsyncContextManager[None]:
        """Context manager for automatic token validation"""
```

## 🏢 SSO Support

### SSO Challenge Handling

When accessing SSO-protected resources:

```python
async def handle_sso_challenge(
    self, 
    response_headers: Dict[str, str], 
    token: str
) -> None:
    """Handle an SSO authorization challenge"""
    
    # Extract SSO URL
    sso_url = self._extract_sso_url(response_headers)
    
    # Open browser for authorization
    webbrowser.open(sso_url)
    
    # Wait for user completion
    await self._wait_for_sso_completion(token)
```

### SSO Verification

```python
async def verify_sso(self, token: str, org: str) -> bool:
    """Verify if SSO authorization has been completed"""
    
    # Test API access to organization
    response = await self._test_org_access(token, org)
    return response.status == 200
```

## ♿ Accessibility Features

### Accessibility Manager

```python
class AccessibilityManager:
    """Manages accessibility features for authentication"""
    
    def __init__(self):
        self.settings = AccessibilitySettings()
        self.screen_reader_support = self._detect_screen_reader()
```

### Features

- **Screen Reader Support**: Compatible with NVDA, JAWS, VoiceOver
- **High Contrast Mode**: Automatic detection and adaptation
- **Large Text Support**: Scalable text and UI elements
- **Keyboard Navigation**: Full keyboard accessibility
- **Audio Feedback**: Optional audio cues and confirmations

## 🎨 Visual Feedback

### Adaptive UI Components

```python
class VisualFeedback:
    """Provides visual feedback during authentication"""
    
    def display_auth_progress(self, stage: AuthStage) -> None:
        """Display authentication progress with visual indicators"""
```

### Features

- **Progress Indicators**: Visual progress bars and spinners
- **Status Icons**: Clear status indicators (✅ ❌ ⏳)
- **Color Coding**: Semantic color usage
- **Responsive Layout**: Adapts to terminal size
- **Animation Support**: Smooth transitions and feedback

## 🚨 Error Handling

### Error Recovery Workflows

```python
class ErrorRecoveryWorkflow:
    """Provides step-by-step error recovery"""
    
    async def handle_auth_error(
        self, 
        error: AuthenticationError
    ) -> RecoveryResult:
        """Handle authentication errors with guided recovery"""
```

### Common Error Scenarios

1. **Network Issues**: Connection timeouts, DNS failures
2. **Browser Problems**: Browser not available, popup blocked
3. **Token Expiration**: Expired or invalid tokens
4. **SSO Challenges**: Organization SSO requirements
5. **Permission Issues**: Insufficient scopes or access

### Recovery Strategies

- **Automatic Retry**: Intelligent retry with exponential backoff
- **Alternative Methods**: Fallback authentication strategies
- **User Guidance**: Step-by-step troubleshooting instructions
- **Support Information**: Contact details and help resources

## ⚙️ Configuration

### Authentication Configuration

```python
@dataclass
class AuthenticationConfig:
    client_id: str = "Iv1.b507a08c87ecfe98"
    device_code_url: str = "https://github.com/login/device/code"
    token_url: str = "https://github.com/login/oauth/access_token"
    default_scopes: str = "repo,user,gist"
    poll_interval: int = 5
    poll_timeout: int = 900  # 15 minutes
```

### User Preferences

```python
@dataclass
class AuthPreferences:
    preferred_strategy: AuthStrategy
    auto_open_browser: bool
    show_qr_codes: bool
    enable_clipboard: bool
    remember_choice: bool
```

## 📝 Usage Examples

### Basic Authentication

```python
from github_cli.auth.authenticator import Authenticator
from github_cli.utils.config import Config

# Initialize authenticator
config = Config()
authenticator = Authenticator(config)

# Check if already authenticated
if not authenticator.is_authenticated():
    # Perform interactive login
    await authenticator.login_interactive()

# Get current token
token = authenticator.token
print(f"Authenticated with token: {token[:8]}...")
```

### Custom Scopes

```python
# Authenticate with specific scopes
await authenticator.login_interactive(
    scopes="repo,user,gist,workflow"
)
```

### SSO Authentication

```python
# Authenticate with SSO organization
await authenticator.login_interactive(
    scopes="repo,user",
    sso="my-organization"
)
```

### Token Management

```python
from github_cli.auth.token_manager import TokenManager

token_manager = TokenManager(config)

# List all stored tokens
tokens = token_manager.list_tokens()
for token_info in tokens:
    print(f"Token: {token_info['prefix']} - {token_info['host']}")

# Switch to different token
token_manager.set_active_token("abcd")

# Delete old token
token_manager.delete_token("efgh")
```

### Environment Adaptation

```python
from github_cli.auth.environment_detector import EnvironmentDetector
from github_cli.auth.environment_adapter import EnvironmentAdapter

# Detect environment capabilities
detector = EnvironmentDetector()
capabilities = detector.detect()

# Adapt authentication strategy
adapter = EnvironmentAdapter()
strategy = adapter.select_strategy(capabilities)

print(f"Using authentication strategy: {strategy}")
```

## 🧪 Testing

### Mock Authentication

```python
from github_cli.auth.authenticator import MockAuthenticator

# Use mock authenticator for testing
mock_auth = MockAuthenticator()
mock_auth.set_authenticated(True)
mock_auth.set_token("mock_token_12345")

assert mock_auth.is_authenticated()
assert mock_auth.token == "mock_token_12345"
```

### Integration Testing

```python
import pytest

@pytest.mark.integration
async def test_oauth_flow():
    """Test complete OAuth flow (requires manual intervention)"""
    authenticator = Authenticator(config)
    
    # This test requires manual browser interaction
    await authenticator.login_interactive()
    
    assert authenticator.is_authenticated()
    assert authenticator.token is not None
```

## 🔗 Related Documentation

- [OAuth Flow](oauth.md) - Detailed OAuth implementation
- [Token Management](tokens.md) - Token storage and lifecycle
- [SSO Support](sso.md) - Single Sign-On integration
- [API Client](../api/client.md) - API client integration
- [Configuration](../utils/config.md) - Configuration management
