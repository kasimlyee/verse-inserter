"""
Application settings management with encryption.

Implements secure storage and retrieval of application configuration
including API keys with encryption for sensitive data protection.

Author: Kasim Lyee <lyee@codewithlyee.com>
Company: Softlite Inc.
License: MIT
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet

from ..utils.logger import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    """
    Application settings with secure storage.
    
    Manages all configuration parameters with automatic persistence
    and encryption for sensitive data like API keys.
    
    Attributes:
        api_key: API.Bible authentication key (encrypted)
        default_translation: Default Bible translation
        enable_cache: Whether to use verse caching
        cache_directory: Path to cache storage
        log_directory: Path to log files
        theme: UI theme name
        auto_backup: Whether to backup documents
        max_concurrent_requests: API request concurrency limit
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VERSE_INSERTER_",
        case_sensitive=False,
    )
    
    # API Configuration
    api_key: str = Field(default="", description="API.Bible key")
    default_translation: str = Field(default="NIV", description="Default translation")
    
    # Cache Settings
    enable_cache: bool = Field(default=True, description="Enable verse caching")
    cache_directory: Path = Field(
        default=Path.home() / ".verse_inserter" / "cache",
        description="Cache storage path"
    )
    cache_ttl_days: int = Field(default=30, description="Cache TTL in days")
    
    # Logging
    log_directory: Path = Field(
        default=Path.home() / ".verse_inserter" / "logs",
        description="Log file path"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    
    # UI Settings
    theme: str = Field(default="cosmo", description="UI theme")
    window_size: str = Field(default="900x700", description="Window dimensions")
    
    # Processing Options
    auto_backup: bool = Field(default=True, description="Auto-backup documents")
    max_concurrent_requests: int = Field(default=5, description="API concurrency")
    
    # Advanced
    enable_analytics: bool = Field(default=False, description="Usage analytics")
    check_updates: bool = Field(default=True, description="Check for updates")
    
    _config_file: Path = Path.home() / ".verse_inserter" / "config.json"
    _encryption_key: Optional[bytes] = None
    
    def __init__(self, **kwargs):
        """Initialize settings and load from config file if exists."""
        super().__init__(**kwargs)
        self._ensure_directories()
        self._load_encryption_key()
        self.load_from_file()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.cache_directory, self.log_directory, self._config_file.parent]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_encryption_key(self) -> None:
        """Load or generate encryption key for sensitive data."""
        key_file = self._config_file.parent / ".key"
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                self._encryption_key = f.read()
        else:
            # Generate new key
            self._encryption_key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(self._encryption_key)
            
            # Restrict permissions (Unix-like systems)
            try:
                key_file.chmod(0o600)
            except Exception:
                pass
    
    def _encrypt(self, value: str) -> str:
        """Encrypt sensitive string value."""
        if not value or not self._encryption_key:
            return value
        
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(value.encode()).decode()
    
    def _decrypt(self, value: str) -> str:
        """Decrypt sensitive string value."""
        if not value or not self._encryption_key:
            return value
        
        try:
            fernet = Fernet(self._encryption_key)
            return fernet.decrypt(value.encode()).decode()
        except Exception as e:
            logger.warning(f"Decryption failed: {e}")
            return ""
    
    def save_to_file(self) -> None:
        """Save settings to config file with encryption."""
        try:
            # Prepare data for serialization
            data = self.model_dump()
            
            # Encrypt sensitive fields
            if data.get("api_key"):
                data["api_key"] = self._encrypt(data["api_key"])
            
            # Convert Path objects to strings
            for key, value in data.items():
                if isinstance(value, Path):
                    data[key] = str(value)
            
            # Write to file
            with open(self._config_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Settings saved to {self._config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def load_from_file(self) -> None:
        """Load settings from config file."""
        if not self._config_file.exists():
            logger.debug("No config file found, using defaults")
            return
        
        try:
            with open(self._config_file, "r") as f:
                data = json.load(f)
            
            # Decrypt sensitive fields
            if "api_key" in data and data["api_key"]:
                data["api_key"] = self._decrypt(data["api_key"])
            
            # Convert string paths back to Path objects
            for key in ["cache_directory", "log_directory"]:
                if key in data:
                    data[key] = Path(data[key])
            
            # Update settings
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info("Settings loaded from file")
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def update_api_key(self, api_key: str) -> None:
        """
        Update and save API key securely.
        
        Args:
            api_key: New API key to store
        """
        self.api_key = api_key
        self.save_to_file()
        logger.info("API key updated")
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        # Store current API key
        current_key = self.api_key
        
        # Reload defaults
        self.__init__()
        
        # Restore API key
        self.api_key = current_key
        self.save_to_file()
        
        logger.info("Settings reset to defaults")
    
    def export_config(self, export_path: Path) -> None:
        """
        Export configuration to external file.
        
        Args:
            export_path: Path to export config to
        """
        try:
            data = self.model_dump()
            
            # Don't export sensitive data in plain text
            if "api_key" in data:
                data["api_key"] = "*** REDACTED ***"
            
            # Convert Path objects
            for key, value in data.items():
                if isinstance(value, Path):
                    data[key] = str(value)
            
            with open(export_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Configuration exported to {export_path}")
            
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            raise
    
    def get_safe_display(self) -> Dict[str, Any]:
        """
        Get settings dictionary with sensitive data masked.
        
        Returns:
            Dictionary with masked sensitive values for display
        """
        data = self.model_dump()
        
        # Mask sensitive fields
        if data.get("api_key"):
            data["api_key"] = f"***{data['api_key'][-4:]}" if len(data["api_key"]) > 4 else "***"
        
        return data