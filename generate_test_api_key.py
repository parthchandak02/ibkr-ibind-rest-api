#!/usr/bin/env python3
"""
Generate a test API key for Phase 1 testing

Usage: uv run python generate_test_api_key.py
"""

import sys
sys.path.append('backend')

from auth import generate_api_key

def main():
    """Generate a test API key and display it"""
    try:
        api_key = generate_api_key("phase1-test")
        print(f"✅ Generated API key for testing: {api_key}")
        print(f"📝 Use this in your test scripts with header: X-API-Key: {api_key}")
        return api_key
    except Exception as e:
        print(f"❌ Error generating API key: {e}")
        return None

if __name__ == "__main__":
    main() 