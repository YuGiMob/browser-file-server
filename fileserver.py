#!/usr/bin/env python3
"""
Browser File Server - Legacy entry point.

This file provides backward compatibility with the original fileserver.py.
For the new modular version, use: python -m server

Usage:
    python3 fileserver.py [ROOT] [PORT]
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from server.__main__ import main
    main()
