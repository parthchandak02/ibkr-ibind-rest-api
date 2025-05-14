#!/usr/bin/env python3
"""
Script to generate an API key for the IBKR REST API.
This script should be run locally to create your first API key.
"""
import json
import argparse
from pathlib import Path
from auth import generate_api_key

def main():
    parser = argparse.ArgumentParser(description="Generate an API key for the IBKR REST API")
    parser.add_argument("--name", default="Default", help="Name for the API key (e.g., 'Google Apps Script')")
    
    args = parser.parse_args()
    
    try:
        api_key = generate_api_key(args.name)
        print(f"\n✅ API Key generated successfully!")
        print(f"\nYour API Key: {api_key}")
        print("\nStore this key securely. You'll need to include it in the 'X-API-Key' header")
        print("for all requests to the IBKR REST API.\n")
    except Exception as e:
        print(f"❌ Error generating API key: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()
