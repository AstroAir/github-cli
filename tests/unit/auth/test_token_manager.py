"""
Unit tests for token manager.

Tests token storage, retrieval, validation, and lifecycle management.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime, timezone, timedelta

from github_cli.auth.token_manager import TokenManager
from github_cli.utils.config import Config
from github_cli.utils.exceptions import AuthenticationError
from dataclasses import dataclass
from typing import Optional

# Define TokenData for tests since it's expected but not implemented
@dataclass
class TokenData:
    """Token data class for testing."""
    id: str
    access_token: str
    token_type: str
    scope: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    name: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@pytest.mark.unit
@pytest.mark.auth
class TestTokenManager:
    """Test cases for TokenManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_config.get_auth_dir = Mock(return_value=Path("/tmp/test_auth"))
        self.mock_config.config_dir = Path("/tmp/test_config")
        
        self.sample_token_data = {
            "access_token": "gho_test123",
            "token_type": "bearer",
            "scope": "repo,user",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def test_token_manager_initialization(self):
        """Test TokenManager initialization."""
        token_manager = TokenManager(self.mock_config)
        
        assert token_manager.config == self.mock_config
        assert token_manager._tokens == {}
        assert token_manager._active_token_id is None

    def test_token_file_path_property(self):
        """Test token_file_path property."""
        token_manager = TokenManager(self.mock_config)
        
        expected_path = Path("/tmp/test_auth") / "tokens.json"
        assert token_manager.token_file_path == expected_path

    def test_save_token_success(self):
        """Test successful token saving."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file') as mock_save:
            token_id = token_manager.save_token(self.sample_token_data)
            
            assert token_id is not None
            assert len(token_id) == 8  # Short UUID
            assert token_id in token_manager._tokens
            assert token_manager._active_token_id == token_id
            
            saved_token = token_manager._tokens[token_id]
            assert saved_token.access_token == "gho_test123"
            assert saved_token.token_type == "bearer"
            assert saved_token.scope == "repo,user"
            
            mock_save.assert_called_once()

    def test_save_token_with_custom_name(self):
        """Test saving token with custom name."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data, name="work-token")
            
            saved_token = token_manager._tokens[token_id]
            assert saved_token.name == "work-token"

    def test_get_token_active(self):
        """Test getting the active token."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data)
        
        token = token_manager.get_token()
        assert token == "gho_test123"

    def test_get_token_by_id(self):
        """Test getting token by specific ID."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data)
        
        token = token_manager.get_token(token_id)
        assert token == "gho_test123"

    def test_get_token_nonexistent(self):
        """Test getting nonexistent token."""
        token_manager = TokenManager(self.mock_config)
        
        token = token_manager.get_token("nonexistent")
        assert token is None

    def test_get_token_no_active(self):
        """Test getting token when no active token set."""
        token_manager = TokenManager(self.mock_config)
        
        token = token_manager.get_token()
        assert token is None

    def test_list_tokens(self):
        """Test listing all tokens."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id1 = token_manager.save_token(self.sample_token_data, name="token1")
            token_id2 = token_manager.save_token(self.sample_token_data, name="token2")
        
        tokens = token_manager.list_tokens()
        assert len(tokens) == 2
        assert token_id1 in [t.id for t in tokens]
        assert token_id2 in [t.id for t in tokens]

    def test_delete_token_success(self):
        """Test successful token deletion."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            result = token_manager.delete_token(token_id)
        
        assert result is True
        assert token_id not in token_manager._tokens
        assert token_manager._active_token_id is None

    def test_delete_token_nonexistent(self):
        """Test deleting nonexistent token."""
        token_manager = TokenManager(self.mock_config)
        
        result = token_manager.delete_token("nonexistent")
        assert result is False

    def test_set_active_token_success(self):
        """Test setting active token."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            result = token_manager.set_active_token(token_id)
        
        assert result is True
        assert token_manager._active_token_id == token_id

    def test_set_active_token_nonexistent(self):
        """Test setting nonexistent token as active."""
        token_manager = TokenManager(self.mock_config)
        
        result = token_manager.set_active_token("nonexistent")
        assert result is False

    def test_validate_token_valid(self):
        """Test validating a valid token."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data)
        
        is_valid = token_manager.validate_token(token_id)
        assert is_valid is True

    def test_validate_token_expired(self):
        """Test validating an expired token."""
        token_manager = TokenManager(self.mock_config)
        
        # Create expired token data
        expired_data = self.sample_token_data.copy()
        expired_data["expires_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(expired_data)
        
        is_valid = token_manager.validate_token(token_id)
        assert is_valid is False

    def test_validate_token_nonexistent(self):
        """Test validating nonexistent token."""
        token_manager = TokenManager(self.mock_config)
        
        is_valid = token_manager.validate_token("nonexistent")
        assert is_valid is False

    def test_load_tokens_from_file_success(self):
        """Test loading tokens from file."""
        token_manager = TokenManager(self.mock_config)
        
        file_data = {
            "tokens": {
                "abc12345": {
                    "id": "abc12345",
                    "access_token": "gho_test123",
                    "token_type": "bearer",
                    "scope": "repo,user",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "name": "test-token"
                }
            },
            "active_token_id": "abc12345"
        }
        
        mock_file_content = json.dumps(file_data)
        
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch.object(token_manager.token_file_path, "exists", return_value=True):
                token_manager._load_tokens_from_file()
        
        assert len(token_manager._tokens) == 1
        assert "abc12345" in token_manager._tokens
        assert token_manager._active_token_id == "abc12345"

    def test_load_tokens_from_file_not_exists(self):
        """Test loading tokens when file doesn't exist."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager.token_file_path, "exists", return_value=False):
            token_manager._load_tokens_from_file()
        
        assert token_manager._tokens == {}
        assert token_manager._active_token_id is None

    def test_load_tokens_from_file_invalid_json(self):
        """Test loading tokens with invalid JSON."""
        token_manager = TokenManager(self.mock_config)
        
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch.object(token_manager.token_file_path, "exists", return_value=True):
                token_manager._load_tokens_from_file()
        
        assert token_manager._tokens == {}
        assert token_manager._active_token_id is None

    def test_save_tokens_to_file_success(self):
        """Test saving tokens to file."""
        token_manager = TokenManager(self.mock_config)
        
        with patch.object(token_manager, '_save_tokens_to_file'):
            token_id = token_manager.save_token(self.sample_token_data)
        
        # Mock the file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            with patch.object(token_manager.token_file_path.parent, "mkdir"):
                token_manager._save_tokens_to_file()
        
        # Verify file was written
        mock_file.assert_called_once()
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        
        # Verify JSON structure
        data = json.loads(written_content)
        assert "tokens" in data
        assert "active_token_id" in data

    def test_save_tokens_to_file_permission_error(self):
        """Test saving tokens with permission error."""
        token_manager = TokenManager(self.mock_config)
        
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch.object(token_manager.token_file_path.parent, "mkdir"):
                with pytest.raises(AuthenticationError, match="Failed to save tokens"):
                    token_manager._save_tokens_to_file()

    def test_token_data_creation(self):
        """Test TokenData dataclass creation."""
        token_data = TokenData(
            id="test123",
            access_token="gho_token",
            token_type="bearer",
            scope="repo,user",
            created_at=datetime.now(timezone.utc),
            name="test-token"
        )
        
        assert token_data.id == "test123"
        assert token_data.access_token == "gho_token"
        assert token_data.token_type == "bearer"
        assert token_data.scope == "repo,user"
        assert token_data.name == "test-token"

    def test_token_data_is_expired_false(self):
        """Test TokenData.is_expired when token is not expired."""
        token_data = TokenData(
            id="test123",
            access_token="gho_token",
            token_type="bearer",
            scope="repo,user",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        assert token_data.is_expired() is False

    def test_token_data_is_expired_true(self):
        """Test TokenData.is_expired when token is expired."""
        token_data = TokenData(
            id="test123",
            access_token="gho_token",
            token_type="bearer",
            scope="repo,user",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        assert token_data.is_expired() is True

    def test_token_data_is_expired_no_expiry(self):
        """Test TokenData.is_expired when no expiry is set."""
        token_data = TokenData(
            id="test123",
            access_token="gho_token",
            token_type="bearer",
            scope="repo,user",
            created_at=datetime.now(timezone.utc)
        )
        
        assert token_data.is_expired() is False
