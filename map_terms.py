#!/usr/bin/env python3
"""
Command-line interface (CLI) wrapper for Medical Terminology Mapper.
This file redirects to the CLI implementation in cli/map_terms.py.
"""

import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the actual CLI implementation
from cli.map_terms import main

if __name__ == "__main__":
    main()