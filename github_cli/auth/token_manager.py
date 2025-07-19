"""
Token management for GitHub CLI authentication
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import time

from github_cli.utils.config import Config
from github_cli.utils.exceptions import AuthenticationError


class TokenManager:
    """Manager for GitHub authentication tokens"""

    def __init__(self, config: Config):
        """Initialize the token manager"""
        self.config = config
        self.tokens_dir = config.config_dir / 'tokens'
        self.active_token_file = config.config_dir / 'active_token'

        # Create tokens directory if it doesn't exist
        if not self.tokens_dir.exists():
            self.tokens_dir.mkdir(parents=True, exist_ok=True)

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

    def list_tokens(self) -> List[Dict[str, Any]]:
        """List all saved tokens"""
        tokens = []

        for token_file in self.tokens_dir.glob("*.json"):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)

                # Add the filename to the data
                token_data["file"] = token_file.name
                tokens.append(token_data)
            except json.JSONDecodeError:
                pass

        return tokens

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

    def set_active_token(self, token_prefix: str) -> bool:
        """Set a token as the active token by its prefix"""
        for token_file in self.tokens_dir.glob(f"*-{token_prefix}*.json"):
            with open(self.active_token_file, 'w') as f:
                f.write(str(token_file))
            return True

        return False

    def clear_token(self) -> None:
        """Clear the active token completely"""
        try:
            # Remove active token reference
            if self.active_token_file.exists():
                self.active_token_file.unlink()
            
            # Optionally remove all tokens - uncomment if desired
            # for token_file in self.tokens_dir.glob("*.json"):
            #     token_file.unlink()
            
        except Exception:
            # Silent fail for cleanup operations
            pass
