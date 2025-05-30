"""
Application class for the IBKR REST API.

This module contains the main Application class that handles server startup,
configuration validation, and environment setup.
"""

import logging
import os
from pathlib import Path

from .api import app
from .config import Config

logger = logging.getLogger(__name__)


class Application:
    """Main application class that handles server startup and configuration."""

    def __init__(self, environment="live_trading"):
        """
        Initialize the application with the specified environment.

        Args:
            environment: The trading environment (only live_trading is supported)
        """
        self.environment = environment
        self.config = Config(environment)
        self.app = app

        # Set the global trading environment
        os.environ["IBIND_TRADING_ENV"] = environment

    def validate_oauth_files(self):
        """
        Validate that required OAuth files exist.

        Returns:
            bool: True if all files exist, False otherwise
        """
        base_dir = Path(__file__).resolve().parent.parent
        oauth_dir = f"{self.environment}_oauth_files"

        required_files = [
            base_dir / oauth_dir / "private_encryption.pem",
            base_dir / oauth_dir / "private_signature.pem",
        ]

        for file_path in required_files:
            if not file_path.exists():
                logger.error(f"Required OAuth file not found: {file_path}")
                return False

        logger.info("✅ OAuth files verified")
        return True

    def run(self, host="0.0.0.0", port=None, debug=False):
        """
        Run the Flask application.

        Args:
            host: Host to bind to (default: '0.0.0.0')
            port: Port to run on (default: PORT env var or 8080)
            debug: Whether to run in debug mode
        """
        # Always prioritize PORT environment variable (for Cloud Run compatibility)
        if port is None:
            port = int(os.environ.get("PORT", 8080))

        logger.info(f"Starting IBKR REST API server:")
        logger.info(f"  Environment: {self.environment}")
        logger.info(f"  Host: {host}")
        logger.info(f"  Port: {port}")
        logger.info(f"  Debug: {debug}")

        # Validate OAuth files before starting
        if not self.validate_oauth_files():
            raise FileNotFoundError("Required OAuth files are missing")

        # Start the Flask application
        self.app.run(host=host, port=port, debug=debug)
