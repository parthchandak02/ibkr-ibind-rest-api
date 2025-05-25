"""
IBKR REST API - Main Application Package

This package contains the core application modules:
- api: Flask REST API endpoints
- auth: Authentication and API key management
- config: Configuration management
- utils: IBKR client utilities
- application: Main application class for server startup
"""

from .application import Application

__version__ = "1.0.0"
__all__ = ['Application'] 