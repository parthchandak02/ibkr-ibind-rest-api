#!/usr/bin/env python3
"""
IBKR Recurring Orders Service - Main Entry Point

Simple entry point that delegates to the service manager.
"""

import sys
from pathlib import Path

# Add service directory to path
sys.path.insert(0, str(Path(__file__).parent / "service"))

from service_manager import main

if __name__ == "__main__":
    main()
