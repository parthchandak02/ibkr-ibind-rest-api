"""
Config module for the ibind REST API.

This module handles loading configuration from JSON files and environment variables.
"""

import json
from pathlib import Path


class Config:
    """Configuration class that handles loading authentication settings per environment."""

    def __init__(self, environment="live_trading"):
        """Initialize the configuration for the given trading environment."""
        self.environment = environment
        # Look for config.json in the project root (parent of backend directory)
        self.config_path = Path(__file__).resolve().parent.parent / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        """Load the configuration from the JSON file."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}. "
                "Create config.json with 'live_trading' and/or 'paper_trading' sections."
            ) from e

    def get_oauth_config(self):
        """Get OAuth configuration with absolute file paths for the active environment."""
        env_key = self.environment
        if env_key not in self.config:
            raise KeyError(f"Missing environment '{env_key}' in config.json") from e

        oauth_config = dict(self.config[env_key].get("oauth", {}))

        # Base directory is the project root (parent of backend directory)
        base_dir = Path(__file__).resolve().parent.parent
        oauth_dir = f"{env_key}_oauth_files"

        # Only set default paths if not already provided
        oauth_config.setdefault(
            "encryption_key_path", str(base_dir / oauth_dir / "private_encryption.pem")
        )
        oauth_config.setdefault(
            "signature_key_path", str(base_dir / oauth_dir / "private_signature.pem")
        )

        return oauth_config

    def get_api_config(self):
        """Get API configuration for the active environment."""
        env_key = self.environment
        if env_key not in self.config:
            raise KeyError(f"Missing environment '{env_key}' in config.json") from e
        return self.config[env_key].get("api", {})

    def get_application_config(self):
        """Get application configuration."""
        return self.config.get("application", {})

    def is_paper_trading(self):
        """Return True when the active environment is paper trading."""
        return self.environment == "paper_trading"

    def get(self, key, default=None):
        """Get any configuration value by key."""
        return self.config.get(key, default)

    def get_google_sheets_config(self):
        """Get Google Sheets configuration."""
        return self.config.get("google_sheets", {})

    def get_discord_config(self):
        """Get Discord configuration."""
        return self.config.get("discord", {})

    def get_oauth_keys_config(self):
        """Get OAuth keys file paths configuration."""
        oauth_keys = self.config.get("oauth_keys", {})
        base_dir = Path(__file__).resolve().parent.parent
        
        # Provide defaults if not specified
        oauth_keys.setdefault("encryption_key_path", str(base_dir / "private_encryption.pem"))
        oauth_keys.setdefault("signature_key_path", str(base_dir / "private_signature.pem"))
        
        return oauth_keys

    def get_settings(self):
        """Get general settings."""
        return self.config.get("settings", {})
    
    def get_api_base_url(self):
        """Get the complete API base URL."""
        settings = self.get_settings()
        port = settings["api_port"]  # No fallback - config.json required
        return f"http://127.0.0.1:{port}"
    
    def get_service_base_url(self):
        """Get the complete service base URL."""
        settings = self.get_settings()
        port = settings["service_port"]  # No fallback - config.json required
        return f"http://127.0.0.1:{port}"

    def get_complete_config(self):
        """Get complete configuration as a dictionary for the active environment."""
        return {
            "environment": self.environment,
            "oauth": self.get_oauth_config(),
            "api": self.get_api_config(),
            "application": self.get_application_config(),
            "google_sheets": self.get_google_sheets_config(),
            "discord": self.get_discord_config(),
            "oauth_keys": self.get_oauth_keys_config(),
            "settings": self.get_settings(),
        }
