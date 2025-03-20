"""
Config module for the ibind REST API.

This module handles loading configuration from JSON files and environment variables.
"""
import json
from pathlib import Path


class Config:
    """Configuration class that handles loading authentication settings from files."""
    
    def __init__(self, environment="paper_trading"):
        """
        Initialize the configuration.
        
        Args:
            environment (str): Either "paper_trading" or "live_trading"
        """
        self.environment = environment
        self.config_path = self._get_config_path()
        self.config = self._load_config()
        
    def _get_config_path(self):
        """Get the path to the configuration file based on the environment."""
        base_dir = Path(__file__).resolve().parent
        if self.environment == "paper_trading":
            return base_dir / "paper_trading.json"
        else:
            return base_dir / "live_trading.json"
    
    def _load_config(self):
        """Load the configuration from the JSON file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_oauth_config(self):
        """Get OAuth configuration."""
        oauth_config = self.config.get("oauth", {})
        
        # Adjust file paths to be absolute
        base_dir = Path(__file__).resolve().parent
        if "encryption_key_path" in oauth_config:
            oauth_config["encryption_key_path"] = str(base_dir / oauth_config["encryption_key_path"])
        if "signature_key_path" in oauth_config:
            oauth_config["signature_key_path"] = str(base_dir / oauth_config["signature_key_path"])
            
        return oauth_config
    
    def get_api_config(self):
        """Get API configuration."""
        return self.config.get("api", {})
    
    def get_application_config(self):
        """Get application configuration."""
        return self.config.get("application", {})
    
    def is_paper_trading(self):
        """Check if using paper trading."""
        return self.environment == "paper_trading"
    
    def get_complete_config(self):
        """Get complete configuration as a dictionary."""
        return {
            "environment": self.environment,
            "oauth": self.get_oauth_config(),
            "api": self.get_api_config(),
            "application": self.get_application_config()
        }
