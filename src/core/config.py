"""
Secure Vault - Configuration Management
Handles global configuration, paths, and settings.
"""

import json
import os
from pathlib import Path
from typing import Optional, Any


class Config:
    """Global configuration manager for Secure Vault."""
    
    # Application paths
    APP_NAME = "SecureVault"
    
    def __init__(self):
        self._config_data: dict = {}
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / "config.json"
        self._ensure_directories()
        self._load_config()
    
    def _get_config_dir(self) -> Path:
        """Get the application configuration directory."""
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / self.APP_NAME
        # Fallback for non-Windows systems
        return Path.home() / f".{self.APP_NAME.lower()}"
    
    def _ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config_data = {}
        else:
            self._config_data = {}
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config_data, f, indent=2, ensure_ascii=False)
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self._config_dir
    
    @property
    def database_path(self) -> Path:
        """Get the database file path."""
        return self._config_dir / "vault.db"
    
    
    
    @property
    def is_first_run(self) -> bool:
        """Check if this is the first run (no encrypted key stored)."""
        return "encrypted_master_key" not in self._config_data
    
    # Theme settings
    @property
    def dark_mode(self) -> bool:
        """Get current theme mode."""
        return self._config_data.get("dark_mode", True)
    
    @dark_mode.setter
    def dark_mode(self, value: bool) -> None:
        """Set theme mode."""
        self._config_data["dark_mode"] = value
        self._save_config()
    
    # Master key storage (encrypted)
    @property
    def encrypted_master_key(self) -> Optional[bytes]:
        """Get the encrypted master key."""
        key_hex = self._config_data.get("encrypted_master_key")
        return bytes.fromhex(key_hex) if key_hex else None
    
    @encrypted_master_key.setter
    def encrypted_master_key(self, value: bytes) -> None:
        """Set the encrypted master key."""
        self._config_data["encrypted_master_key"] = value.hex()
        self._save_config()
    
    @property
    def master_key_salt(self) -> Optional[bytes]:
        """Get the salt used for PIN derivation."""
        salt_hex = self._config_data.get("master_key_salt")
        return bytes.fromhex(salt_hex) if salt_hex else None
    
    @master_key_salt.setter
    def master_key_salt(self, value: bytes) -> None:
        """Set the salt for PIN derivation."""
        self._config_data["master_key_salt"] = value.hex()
        self._save_config()
    
    @property
    def language(self) -> str:
        """Get the current language ('zh' or 'en')."""
        return self._config_data.get("language", "zh")
    
    @language.setter
    def language(self, value: str) -> None:
        """Set the current language."""
        if value in ["zh", "en"]:
            self._config_data["language"] = value
            self._save_config()
    
    @property
    def master_key_nonce(self) -> Optional[bytes]:
        """Get the nonce used for master key encryption."""
        nonce_hex = self._config_data.get("master_key_nonce")
        return bytes.fromhex(nonce_hex) if nonce_hex else None
    
    @master_key_nonce.setter
    def master_key_nonce(self, value: bytes) -> None:
        """Set the nonce for master key encryption."""
        self._config_data["master_key_nonce"] = value.hex()
        self._save_config()
    
    @property
    def master_key_hash(self) -> Optional[str]:
        """Get the hash of the master key for verification."""
        return self._config_data.get("master_key_hash")
    
    @master_key_hash.setter
    def master_key_hash(self, value: str) -> None:
        """Set the hash of the master key."""
        self._config_data["master_key_hash"] = value
        self._save_config()
    
    # Active repository
    @property
    def active_repository_id(self) -> Optional[int]:
        """Get the currently active repository ID."""
        return self._config_data.get("active_repository_id")
    
    @active_repository_id.setter
    def active_repository_id(self, value: Optional[int]) -> None:
        """Set the active repository ID."""
        self._config_data["active_repository_id"] = value
        self._save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config_data[key] = value
        self._save_config()


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
