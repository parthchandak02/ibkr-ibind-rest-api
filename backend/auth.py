"""
Authentication module for the IBKR REST API.
"""

import datetime
import json
import logging
import secrets
from functools import wraps
from pathlib import Path

from flask import Response, jsonify, request

# Initialize logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Path to API keys file in project root (parent of src directory)
API_KEYS_FILE = Path(__file__).resolve().parent.parent / "api_keys.json"


def generate_api_key(name):
    """Generate a new API key and save it to the keys file."""
    api_key = secrets.token_urlsafe(32)

    # Load existing keys or create empty dict
    if API_KEYS_FILE.exists():
        with open(API_KEYS_FILE, "r") as f:
            try:
                keys = json.load(f)
            except json.JSONDecodeError:
                keys = {}
    else:
        keys = {}

    # Add new key
    keys[api_key] = {"name": name, "created": str(datetime.datetime.now())}

    # Save keys
    with open(API_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

    return api_key


def validate_api_key(api_key):
    """Validate an API key against the keys file."""
    if not API_KEYS_FILE.exists():
        logger.warning("API keys file not found")
        return False

    with open(API_KEYS_FILE, "r") as f:
        try:
            keys = json.load(f)
            return api_key in keys
        except json.JSONDecodeError:
            logger.error("Invalid API keys file format")
            return False


def require_api_key(f):
    """Decorator to require API key for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")

        # For the /auth endpoint used by Nginx
        if request.path == "/auth":
            api_key = request.headers.get("X-API-Key")
            if api_key and validate_api_key(api_key):
                return Response(status=200)
            return Response(status=401)

        if not api_key:
            return jsonify({"status": "error", "message": "API key is required"}), 401

        if not validate_api_key(api_key):
            return jsonify({"status": "error", "message": "Invalid API key"}), 401

        return f(*args, **kwargs)

    return decorated_function
