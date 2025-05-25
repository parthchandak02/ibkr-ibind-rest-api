#!/usr/bin/env python3
"""
IBKR REST API Server Entry Point

Simple entry point script for the IBKR REST API server.
Uses the Application class for all startup logic.
"""
import sys
import argparse
import logging
from src import Application

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point for the IBKR REST API server."""
    parser = argparse.ArgumentParser(description="IBKR REST API Server")
    parser.add_argument(
        "--env", 
        choices=["live_trading"], 
        default="live_trading",
        help="Trading environment (only live_trading is supported)"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run the server on (defaults to PORT env var or 8080)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Run in debug mode"
    )
    
    args = parser.parse_args()
    
    try:
        # Create and run the application
        app = Application(environment=args.env)
        app.run(port=args.port, debug=args.debug)
        return 0
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
