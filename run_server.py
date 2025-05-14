#!/usr/bin/env python3
"""
IBKR REST API Server Launcher

This script provides a convenient way to start the IBKR REST API server
with proper environment configuration. It handles path resolution and
environment setup automatically.
"""
import os
import sys
import argparse
from pathlib import Path

def run_api_server(environment="live_trading", port=5001, debug=False):
    """
    Run the IBKR REST API server with the specified configuration.
    
    Args:
        environment (str): Trading environment - either "paper_trading" or "live_trading"
        port (int): Port to run the server on
        debug (bool): Whether to run in debug mode
    """
    # Set the working directory to the script directory
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)
    print(f"Working directory set to: {os.getcwd()}")
    
    # Set environment variables
    os.environ["IBIND_TRADING_ENV"] = environment
    os.environ["IBIND_USE_OAUTH"] = "true"
    
    # Print the paths to the OAuth files for verification
    oauth_dir = f"{environment}_oauth_files"
    encryption_path = base_dir / oauth_dir / "private_encryption.pem"
    signature_path = base_dir / oauth_dir / "private_signature.pem"
    
    print(f"Environment: {environment}")
    print(f"Encryption key path: {encryption_path}")
    print(f"Signature key path: {signature_path}")
    
    # Verify that the OAuth files exist
    if not encryption_path.exists():
        print(f"ERROR: Encryption key file not found at: {encryption_path}")
        print("Please make sure you have generated the OAuth keys and placed them in the correct directory.")
        return 1
    if not signature_path.exists():
        print(f"ERROR: Signature key file not found at: {signature_path}")
        print("Please make sure you have generated the OAuth keys and placed them in the correct directory.")
        return 1
    
    print("✅ OAuth files verified")
    
    # Import and run the API
    try:
        print("Importing API module...")
        import api
        
        print(f"Starting API server on port {port}...")
        api.app.run(debug=debug, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"Error running API server: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the IBKR REST API server")
    parser.add_argument(
        "--env", 
        choices=["paper_trading", "live_trading"], 
        default="live_trading",
        help="Trading environment (paper_trading or live_trading)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=5001,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Run in debug mode"
    )
    
    args = parser.parse_args()
    sys.exit(run_api_server(args.env, args.port, args.debug))
