#!/usr/bin/env python3
"""
IBKR REST API Server Entry Point

Simplified entry point that directly runs the Flask app.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def validate_oauth_files(environment="live_trading"):
    """Validate that required OAuth files exist."""
    base_dir = Path(__file__).resolve().parent
    oauth_dir = f"{environment}_oauth_files"
    
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


def main():
    """Main entry point for the IBKR REST API server."""
    parser = argparse.ArgumentParser(description="IBKR REST API Server")
    parser.add_argument(
        "--env",
        choices=["live_trading"],
        default="live_trading",
        help="Trading environment (only live_trading is supported)",
    )
    parser.add_argument(
        "--port", type=int, help="Port to run the server on (overrides config.json api_port)"
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    try:
        # Set environment
        os.environ["IBIND_TRADING_ENV"] = args.env
        
        # Validate OAuth files
        if not validate_oauth_files(args.env):
            raise FileNotFoundError("Required OAuth files are missing")
        
        # Import and run the Flask app
        from backend.api import app
        from backend.config import Config
        
        config = Config()
        settings = config.get_settings()
        
        # Set port - command line arg overrides config.json (no other fallbacks)
        port = args.port or settings["api_port"]  # No fallback - config.json required
        
        logger.info(f"Starting IBKR REST API server:")
        logger.info(f"  Environment: {args.env}")
        logger.info(f"  Host: 0.0.0.0")
        logger.info(f"  Port: {port}")
        logger.info(f"  Debug: {args.debug}")
        
        # Start the Flask application
        app.run(host="0.0.0.0", port=port, debug=args.debug)
        return 0
        
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
