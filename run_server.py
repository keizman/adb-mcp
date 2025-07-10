#!/usr/bin/env python3
"""Simple wrapper script to run the Android ADB MCP Server."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from android_adb_mcp_server.main import main

if __name__ == "__main__":
    main()