﻿from __future__ import annotations

import asyncio
import secrets
import time
import webbrowser
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, TYPE_CHECKING

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from github_cli.utils.config import Config
from github_cli.utils.exceptions import AuthenticationError, NetworkError

if TYPE_CHECKING:
    from github_cli.auth.token_manager import TokenManager
    from github_cli.auth.sso_handler import SSOHandler


@dataclass(frozen=True, slots=True)
class AuthTokenResponse:
    """Immutable data class for authentication token response using Python 3.11+ features."""
    access_token: str
    token_type: str
    scope: str
    refresh_token: str | None = None
    expires_in: int | None = None
    created_at: int | None = field(default_factory=lambda: int(time.time()))


class UserInfo(BaseModel):
    """User information model with validation."""
    login: str = Field(description="GitHub username")
    id: int = Field(description="User ID")
    name: str | None = Field(default=None, description="Display name")
    email: str | None = Field(default=None, description="Primary email")
    avatar_url: str | None = Field(default=None, description="Avatar URL")
    

class AuthenticationConfig(BaseModel):
    """Authentication configuration model."""
    client_id: str = Field(default="Iv1.c42d2e9c91e3a928")
    device_code_url: str = Field(default="https://github.com/login/device/code")
    token_url: str = Field(default="https://github.com/login/oauth/access_token")
    default_scopes: str = Field(default="repo,read:user,user:email,gist,workflow")
    max_poll_attempts: int = Field(default=60, description="Max polling attempts for token")
    poll_interval: int = Field(default=5, description="Default polling interval in seconds")


class Authenticator:
    """Enhanced GitHub authentication handler with modern Python features."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._auth_config = AuthenticationConfig()
        
        # Lazy load these to avoid circular imports
        self._token_manager: TokenManager | None = None
        self._sso_handler: SSOHandler | None = None
        
        self._token: str | None = None
        self._user_info: UserInfo | None = None
        
        # Setup structured logging
        logger.configure(
            handlers=[
                {
                    "sink": "logs/auth.log",
                    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
                    "rotation": "5 MB",
                    "retention": "3 days",
                    "level": "INFO"
                }
            ]
        )
        
        logger.info("Authenticator initialized")
    
    @property
    def token_manager(self) -> TokenManager:
        """Lazy-loaded token manager."""
        if self._token_manager is None:
            from github_cli.auth.token_manager import TokenManager
            self._token_manager = TokenManager(self.config)
        return self._token_manager
    
    @property
    def sso_handler(self) -> SSOHandler:
        """Lazy-loaded SSO handler."""
        if self._sso_handler is None:
            from github_cli.auth.sso_handler import SSOHandler
            self._sso_handler = SSOHandler(self.config)
        return self._sso_handler
    
    @property
    def token(self) -> str | None:
        """Get the current authentication token."""
        if self._token is None:
            self._token = self.token_manager.get_active_token()
        return self._token
    
    @property
    def user_info(self) -> UserInfo | None:
        """Get cached user information."""
        return self._user_info

    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        authenticated = self.token is not None
        logger.debug(f"Authentication status: {authenticated}")
        return authenticated

    async def login_interactive(
        self, 
        scopes: str | None = None, 
        sso: str | None = None
    ) -> None:
        """Enhanced interactive OAuth device flow login with better error handling."""
        if self.is_authenticated():
            logger.info("User already authenticated, skipping login")
            print("Already authenticated. Use 'logout' first to change accounts.")
            return

        # Use configured scopes if none provided
        scopes = scopes or self._auth_config.default_scopes
        logger.info(f"Starting authentication flow with scopes: {scopes}")

        try:
            # Start device flow
            device_code_data = await self._request_device_code(scopes)
            if not device_code_data:
                raise AuthenticationError("Failed to start authentication flow")

            # Display user instructions
            await self._display_auth_instructions(device_code_data)

            # Poll for token
            device_code = device_code_data.get("device_code", "")
            interval = int(device_code_data.get("interval", self._auth_config.poll_interval))

            logger.info("Starting token polling")
            token_data = await self._poll_for_token(device_code, interval)
            
            if not token_data or "access_token" not in token_data:
                raise AuthenticationError("Authentication failed or timed out")

            # Save and set the token
            token = self.token_manager.save_token(token_data)
            self._token = token

            # Handle SSO if specified
            if sso:
                logger.info(f"Configuring SSO for organization: {sso}")
                await self._configure_sso(sso)

            print("\n�Successfully authenticated with GitHub!")
            logger.info("Authentication completed successfully")

            # Fetch and cache user info
            await self.fetch_user_info()
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Login failed: {e}") from e
    
    async def _display_auth_instructions(self, device_code_data: dict[str, Any]) -> None:
        """Display authentication instructions to the user."""
        user_code = device_code_data.get("user_code", "")
        verification_uri = device_code_data.get("verification_uri", "")

        print("\n🔐 GitHub Authentication Required")
        print(f"📋 Copy your one-time code: {user_code}")
        print(f"🌐 Open this URL in your browser: {verification_uri}")

        # Open browser automatically if possible
        try:
            if verification_uri:
                webbrowser.open(verification_uri)
                print("🚀 We've opened the verification page in your browser.")
                logger.debug("Opened browser for authentication")
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")
            print("⚠️  Please manually open the URL above.")

        print("\n�Waiting for GitHub authentication...\n")
    
    async def _configure_sso(self, sso: str) -> None:
        """Configure Single Sign-On for the organization."""
        try:
            # Use the SSO handler for configuration
            await self.sso_handler.configure(sso)
            print(f"�SSO configured for organization: {sso}")
        except Exception as e:
            logger.warning(f"SSO configuration failed: {e}")
            print(f"⚠️  SSO configuration failed: {e}")

    async def logout(self) -> None:
        """Enhanced logout with comprehensive cleanup."""
        if not self.is_authenticated():
            logger.info("User not authenticated, logout not needed")
            print("Not currently authenticated.")
            return

        try:
            # Clear the active token from storage
            if self._token:
                token_prefix = self._token[:8] if len(self._token) >= 8 else self._token
                self.token_manager.delete_token(token_prefix)
                logger.info(f"Deleted token with prefix: {token_prefix[:4]}...")

            # Clear in-memory state
            self._token = None
            self._user_info = None

            print("�Successfully logged out.")
            logger.info("Logout completed successfully")
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            # Still clear in-memory state even if token deletion fails
            self._token = None
            self._user_info = None
            print(f"⚠️  Logout completed with warnings: {e}")

    async def fetch_user_info(self) -> UserInfo | None:
        """Fetch and validate user information with enhanced error handling."""
        if not self.is_authenticated():
            logger.debug("Cannot fetch user info: not authenticated")
            return None

        logger.debug("Fetching user information from GitHub API")
        
        try:
            async with self._create_http_session() as session:
                async with session.get(
                    "https://api.github.com/user",
                    headers=self._get_auth_headers()
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        try:
                            # Validate and store user info
                            self._user_info = UserInfo(**user_data)
                            logger.info(f"Successfully fetched user info for: {self._user_info.login}")
                            return self._user_info
                        except ValidationError as e:
                            logger.error(f"Invalid user data format: {e}")
                            return None
                    elif response.status == 401:
                        logger.warning("Token is invalid or expired")
                        # Clear invalid token
                        self._token = None
                        return None
                    else:
                        logger.error(f"Failed to fetch user info: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return None
    
    @asynccontextmanager
    async def _create_http_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """Create an optimized HTTP session for authentication requests."""
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(
            limit=10,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={"User-Agent": "GitHub-CLI/0.1.0"}
        ) as session:
            try:
                yield session
            finally:
                # Session cleanup is automatic with context manager
                pass
    
    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
            
        return headers

    async def _request_device_code(self, scopes: str) -> dict[str, Any] | None:
        """Request a device code for OAuth authentication with enhanced error handling."""
        logger.debug(f"Requesting device code for scopes: {scopes}")
        
        try:
            async with self._create_http_session() as session:
                async with session.post(
                    self._auth_config.device_code_url,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={
                        "client_id": self._auth_config.client_id,
                        "scope": scopes
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug("Device code request successful")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Device code request failed: HTTP {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Network error requesting device code: {e}")
            return None

    async def _poll_for_token(self, device_code: str, interval: int) -> dict[str, Any] | None:
        """Poll for OAuth token with exponential backoff and enhanced error handling."""
        logger.debug(f"Starting token polling with {interval}s interval")
        
        current_interval = interval
        max_attempts = self._auth_config.max_poll_attempts

        for attempt in range(1, max_attempts + 1):
            await asyncio.sleep(current_interval)
            
            logger.debug(f"Polling attempt {attempt}/{max_attempts}")

            try:
                async with self._create_http_session() as session:
                    async with session.post(
                        self._auth_config.token_url,
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json"
                        },
                        json={
                            "client_id": self._auth_config.client_id,
                            "device_code": device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                        }
                    ) as response:
                        data = await response.json()

                        match response.status:
                            case 200 if "access_token" in data:
                                # Success! Add creation timestamp
                                data["created_at"] = int(time.time())
                                logger.info("Token polling successful")
                                return data
                                
                            case 200 if data.get("error") == "authorization_pending":
                                # User hasn't authorized yet, continue polling
                                logger.debug("Authorization still pending")
                                continue
                                
                            case 200 if data.get("error") == "slow_down":
                                # Need to slow down polling
                                current_interval = min(current_interval + 1, 10)  # Cap at 10s
                                logger.debug(f"Rate limited, increasing interval to {current_interval}s")
                                continue
                                
                            case 200 if data.get("error") == "expired_token":
                                logger.error("Device code expired")
                                print("\n�Authentication code expired. Please try again.")
                                return None
                                
                            case 200 if data.get("error") == "access_denied":
                                logger.error("User denied authorization")
                                print("\n�Authorization denied by user.")
                                return None
                                
                            case _:
                                error_msg = data.get("error_description", data.get("error", "Unknown error"))
                                logger.error(f"Token polling error: {error_msg}")
                                print(f"\n�Authentication error: {error_msg}")
                                return None
                                
            except Exception as e:
                logger.warning(f"Error during token polling attempt {attempt}: {e}")
                if attempt == max_attempts:
                    raise
                continue

        logger.error("Token polling timed out")
        print("\n�Authentication timed out. Please try again.")
        return None
