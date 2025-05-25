"""
Config module for the ibind REST API.

This module handles loading configuration from JSON files and environment variables.
"""
import json
import os
from pathlib import Path


class Config:
    """Configuration class that handles loading authentication settings for live trading."""

    def __init__(self, environment="live_trading"):
        """
        Initialize the configuration for live trading.
        """
        self.environment = environment
        # Look for config.json in the project root (parent of src directory)
        self.config_path = Path(__file__).resolve().parent.parent / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        """Load the configuration from the JSON file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def get_oauth_config(self):
        """Get OAuth configuration with absolute file paths."""
        oauth_config = self.config["live_trading"]["oauth"]
        # Base directory is the project root (parent of src directory)
        base_dir = Path(__file__).resolve().parent.parent
        oauth_dir = "live_trading_oauth_files"
        
        # Set default paths for OAuth files
        oauth_config["encryption_key_path"] = str(base_dir / oauth_dir / "private_encryption.pem")
        oauth_config["signature_key_path"] = str(base_dir / oauth_dir / "private_signature.pem")
        
        return oauth_config

    def get_api_config(self):
        """Get API configuration."""
        return self.config["live_trading"]["api"]

    def get_application_config(self):
        """Get application configuration."""
        return self.config.get("application", {})

    def is_paper_trading(self):
        """Always return False since we only support live trading."""
        return False

    def get_complete_config(self):
        """Get complete configuration as a dictionary."""
        return {
            "environment": "live_trading",
            "oauth": self.get_oauth_config(),
            "api": self.get_api_config(),
            "application": self.get_application_config()
        }
