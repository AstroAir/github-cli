# Token Management

The GitHub CLI token management system provides secure storage, lifecycle management, and automatic handling of authentication tokens.

## 🏗️ Architecture Overview

The token management system consists of several components:

```
github_cli/auth/
├── token_manager.py          # Core token storage and retrieval
├── token_expiration_handler.py # Token expiration and refresh
└── authenticator.py           # Authentication integration
```

## 🔑 TokenManager Class

The `TokenManager` class is responsible for storing, retrieving, and managing GitHub authentication tokens:

```python
class TokenManager:
    """Manager for GitHub authentication tokens"""
    
    def __init__(self, config: Config):
        """Initialize the token manager"""
        self.config = config
        self.tokens_dir = config.config_dir / 'tokens'
        self.active_token_file = config.config_dir / 'active_token'
```

## 📚 Core Methods

### Token Storage

```python
def save_token(self, token_data: Dict[str, Any], host: str = "github.com") -> str:
    """Save a token to disk"""
    token = token_data.get("access_token")
    if not token:
        raise AuthenticationError("No access token in response")

    # Generate a unique filename based on the token prefix
    token_prefix = token[:4]
    token_file = self.tokens_dir / f"{host}-{token_prefix}.json"

    # Save the token data
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=4)

    # Set as active token
    with open(self.active_token_file, 'w') as f:
        f.write(str(token_file))

    return token
```

### Token Retrieval

```python
def get_active_token(self) -> Optional[str]:
    """Get the currently active token"""
    if not self.active_token_file.exists():
        return None

    try:
        with open(self.active_token_file, 'r') as f:
            token_file = Path(f.read().strip())

        if not token_file.exists():
            return None

        with open(token_file, 'r') as f:
            token_data = json.load(f)

        # Check if token has expired
        if "expires_in" in token_data and "created_at" in token_data:
            expiry = token_data["created_at"] + token_data["expires_in"]
            if time.time() > expiry:
                return None

        return token_data.get("access_token")
    except (json.JSONDecodeError, KeyError):
        return None
```

### Token Management

```python
def list_tokens(self) -> List[Dict[str, Any]]:
    """List all stored tokens"""
    tokens = []
    for token_file in self.tokens_dir.glob("*.json"):
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Extract metadata
            host = token_data.get("host", "github.com")
            created_at = token_data.get("created_at", 0)
            token_prefix = token_data.get("access_token", "")[:4]
            
            tokens.append({
                "file": token_file.name,
                "host": host,
                "prefix": token_prefix,
                "created_at": created_at
            })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return tokens
```

```python
def delete_token(self, token_prefix: str) -> bool:
    """Delete a token by its prefix"""
    for token_file in self.tokens_dir.glob(f"*-{token_prefix}*.json"):
        token_file.unlink()

        # If this was the active token, clear the active token
        if self.active_token_file.exists():
            with open(self.active_token_file, 'r') as f:
                active_file = Path(f.read().strip())
                if active_file == token_file:
                    self.active_token_file.unlink()

        return True

    return False
```

```python
def set_active_token(self, token_prefix: str) -> bool:
    """Set a token as the active token by its prefix"""
    for token_file in self.tokens_dir.glob(f"*-{token_prefix}*.json"):
        with open(self.active_token_file, 'w') as f:
            f.write(str(token_file))
        return True

    return False
```

## 🔄 Token Expiration Handling

The `TokenExpirationHandler` manages token expiration and refresh:

```python
class TokenExpirationHandler:
    """Handles token expiration and refresh"""
    
    def __init__(self, authenticator: Authenticator):
        self.authenticator = authenticator
        self.refresh_in_progress = False
        self.refresh_lock = asyncio.Lock()
```

### Automatic Token Validation

```python
@asynccontextmanager
async def with_token_validation(
    self,
    operation: str,
    endpoint: str,
    user_message: str
) -> AsyncGenerator[None, None]:
    """Context manager for automatic token validation"""
    
    # Check if token is valid before operation
    await self._validate_token()
    
    try:
        # Yield control to the operation
        yield
    except AuthenticationError as e:
        if "token expired" in str(e).lower():
            # Token expired during operation
            logger.info(f"Token expired during {operation}")
            
            # Refresh token
            if await self._refresh_token():
                # Retry operation
                logger.info(f"Token refreshed, retrying {operation}")
                yield
            else:
                # Token refresh failed
                raise AuthenticationError(
                    f"Authentication failed during {operation}. Please login again."
                )
        else:
            # Other authentication error
            raise
```

### Token Refresh

```python
async def _refresh_token(self) -> bool:
    """Refresh the authentication token"""
    
    # Use lock to prevent multiple simultaneous refreshes
    async with self.refresh_lock:
        if self.refresh_in_progress:
            # Wait for ongoing refresh
            return await self._wait_for_refresh()
        
        self.refresh_in_progress = True
        try:
            # Get refresh token
            refresh_token = self.authenticator.token_manager.get_refresh_token()
            if not refresh_token:
                return False
            
            # Request new token
            token_data = await self._request_new_token(refresh_token)
            if not token_data or "access_token" not in token_data:
                return False
            
            # Save new token
            self.authenticator.token_manager.save_token(token_data)
            return True
            
        finally:
            self.refresh_in_progress = False
```

## 🔐 Security Features

### Token Encryption

```python
def _encrypt_token_data(self, token_data: Dict[str, Any]) -> bytes:
    """Encrypt token data for secure storage"""
    
    # Convert to JSON string
    json_data = json.dumps(token_data)
    
    # Generate encryption key from system-specific data
    key = self._derive_encryption_key()
    
    # Create cipher
    cipher = Fernet(key)
    
    # Encrypt data
    return cipher.encrypt(json_data.encode('utf-8'))
```

```python
def _decrypt_token_data(self, encrypted_data: bytes) -> Dict[str, Any]:
    """Decrypt token data"""
    
    # Generate decryption key
    key = self._derive_encryption_key()
    
    # Create cipher
    cipher = Fernet(key)
    
    # Decrypt data
    json_data = cipher.decrypt(encrypted_data).decode('utf-8')
    
    # Parse JSON
    return json.loads(json_data)
```

### System Keyring Integration

```python
def _store_in_keyring(self, token: str, host: str) -> bool:
    """Store token in system keyring"""
    try:
        import keyring
        service_name = f"github-cli:{host}"
        username = "oauth-token"
        keyring.set_password(service_name, username, token)
        return True
    except Exception as e:
        logger.warning(f"Failed to store token in keyring: {e}")
        return False
```

```python
def _get_from_keyring(self, host: str) -> Optional[str]:
    """Get token from system keyring"""
    try:
        import keyring
        service_name = f"github-cli:{host}"
        username = "oauth-token"
        token = keyring.get_password(service_name, username)
        return token
    except Exception as e:
        logger.warning(f"Failed to get token from keyring: {e}")
        return None
```

## 📊 Token Metadata

Each token is stored with metadata for lifecycle management:

```json
{
    "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
    "token_type": "bearer",
    "scope": "repo,user,gist",
    "created_at": 1625097600,
    "expires_in": 28800,
    "refresh_token": "ghr_1B4a2e77838347a7E420ce178F2E7c6912E169246c34E1ccbF66C46812d16D5B1A9Dc86A1498",
    "refresh_token_expires_in": 15811200,
    "host": "github.com"
}
```

## 🔧 Token Storage Locations

Tokens are stored in platform-specific secure locations:

### File Storage

```
~/.config/github-cli/tokens/           # Linux/macOS
%APPDATA%\github-cli\tokens\           # Windows
```

### Active Token Reference

```
~/.config/github-cli/active_token      # Linux/macOS
%APPDATA%\github-cli\active_token      # Windows
```

## 🚨 Error Handling

### Token Errors

```python
class TokenError(AuthenticationError):
    """Base class for token-related errors"""
    pass

class TokenExpiredError(TokenError):
    """Token has expired"""
    pass

class TokenRefreshError(TokenError):
    """Failed to refresh token"""
    pass

class TokenStorageError(TokenError):
    """Failed to store or retrieve token"""
    pass
```

### Error Recovery

```python
async def handle_token_error(self, error: TokenError) -> bool:
    """Handle token errors with recovery options"""
    
    if isinstance(error, TokenExpiredError):
        # Try to refresh token
        return await self._refresh_token()
    
    elif isinstance(error, TokenRefreshError):
        # Clear token and request re-authentication
        self.token_manager.clear_active_token()
        print("⚠️ Your authentication has expired.")
        print("🔑 Please login again.")
        return False
    
    elif isinstance(error, TokenStorageError):
        # Try alternative storage method
        return await self._try_alternative_storage()
    
    else:
        # Generic token error
        print(f"❌ Authentication error: {error}")
        return False
```

## 📝 Usage Examples

### Basic Token Management

```python
from github_cli.auth.token_manager import TokenManager
from github_cli.utils.config import Config

# Initialize token manager
config = Config()
token_manager = TokenManager(config)

# Get active token
token = token_manager.get_active_token()
if token:
    print(f"Using token: {token[:4]}...")
else:
    print("No active token found")

# List all tokens
tokens = token_manager.list_tokens()
print(f"Found {len(tokens)} stored tokens:")
for token_info in tokens:
    print(f"- {token_info['prefix']} ({token_info['host']})")

# Switch active token
if tokens:
    token_manager.set_active_token(tokens[0]['prefix'])
    print(f"Switched to token: {tokens[0]['prefix']}")
```

### Token Cleanup

```python
# Delete old tokens
import time
from datetime import datetime

tokens = token_manager.list_tokens()
for token_info in tokens:
    created_at = token_info.get('created_at', 0)
    age_days = (time.time() - created_at) / (60 * 60 * 24)
    
    if age_days > 30:  # Older than 30 days
        print(f"Deleting old token: {token_info['prefix']}")
        token_manager.delete_token(token_info['prefix'])
```

### Multi-Host Support

```python
# Save token for GitHub Enterprise
token_data = {
    "access_token": "ghe_token123",
    "token_type": "bearer",
    "scope": "repo,user"
}
token = token_manager.save_token(token_data, host="github.company.com")
print(f"Saved token for GitHub Enterprise: {token[:4]}...")

# Get token for specific host
tokens = token_manager.list_tokens()
enterprise_tokens = [t for t in tokens if t['host'] == "github.company.com"]
if enterprise_tokens:
    token_manager.set_active_token(enterprise_tokens[0]['prefix'])
    print(f"Using enterprise token: {enterprise_tokens[0]['prefix']}")
```

### Token Expiration Handling

```python
from github_cli.auth.token_expiration_handler import TokenExpirationHandler
from github_cli.auth.authenticator import Authenticator

# Initialize components
authenticator = Authenticator(config)
expiration_handler = TokenExpirationHandler(authenticator)

# Use token validation context manager
async def make_api_request():
    async with expiration_handler.with_token_validation(
        operation="fetch user data",
        endpoint="/user",
        user_message="Fetching user profile"
    ):
        # Make API request
        # If token expires, it will be refreshed automatically
        response = await client.get("/user")
        return response.data
```

## 🔗 Related Documentation

- [Authentication Overview](README.md)
- [OAuth Flow](oauth.md)
- [SSO Support](sso.md)
- [API Client](../api/client.md)
