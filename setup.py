#!/usr/bin/env python3

"""
Setup script for GitHub CLI
"""

from setuptools import setup, find_packages

setup(
    name="github-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "aiohttp>=3.9.0",
        "rich>=13.7.0",
        "questionary>=2.0.0",
        "keyring>=24.0.0",
        "python-dateutil>=2.8.0",
        "loguru>=0.7.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.0",
        "textual>=0.85.0",
        "textual-dev>=1.2.0",
        "rich-argparse>=1.3.0",
        "pyperclip>=1.8.0",
    ],
    entry_points={
        "console_scripts": [
            "github-cli=github_cli.__main__:main_entrypoint",
        ],
    },
    python_requires='>=3.11',
)
