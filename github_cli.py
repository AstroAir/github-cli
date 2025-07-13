#!/usr/bin/env python3

"""
GitHub CLI - An advanced terminal-based GitHub client
Entry point for the CLI application
"""

import asyncio
import sys
from github_cli.__main__ import main

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
