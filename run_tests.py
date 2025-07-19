#!/usr/bin/env python3
"""
Test runner script for GitHub CLI project.

This script provides convenient commands to run different test suites
and generate coverage reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"\n🔄 {description}")
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Standard output: {e.stdout}")
        return False


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli", "--cov-report=term-missing", "--cov-report=html:htmlcov"])
    
    cmd.extend(["-m", "unit"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["-m", "integration"])
    
    return run_command(cmd, "Running integration tests")


def run_api_tests(verbose=False, coverage=False):
    """Run API tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/api/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli.api", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running API tests")


def run_auth_tests(verbose=False, coverage=False):
    """Run authentication tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/auth/", "tests/auth/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli.auth", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running authentication tests")


def run_ui_tests(verbose=False, coverage=False):
    """Run UI tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/ui/", "tests/unit/tui/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli.ui", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running UI tests")


def run_model_tests(verbose=False, coverage=False):
    """Run model tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/models/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli.models", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running model tests")


def run_utils_tests(verbose=False, coverage=False):
    """Run utility tests."""
    cmd = ["python", "-m", "pytest", "tests/unit/utils/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli.utils", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running utility tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=github_cli", "--cov-report=term-missing", "--cov-report=html:htmlcov"])
    
    return run_command(cmd, "Running all tests")


def run_fast_tests(verbose=False):
    """Run only fast tests (unit tests, no integration)."""
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["-m", "unit and not slow"])
    
    return run_command(cmd, "Running fast tests")


def generate_coverage_report():
    """Generate detailed coverage report."""
    cmd = ["python", "-m", "pytest", "tests/", "--cov=github_cli", 
           "--cov-report=html:htmlcov", "--cov-report=term-missing", 
           "--cov-report=xml:coverage.xml"]
    
    success = run_command(cmd, "Generating coverage report")
    
    if success:
        print("\n📊 Coverage report generated:")
        print("  - HTML report: htmlcov/index.html")
        print("  - XML report: coverage.xml")
        print("  - Terminal report shown above")
    
    return success


def lint_code():
    """Run code linting."""
    print("\n🔍 Running code linting...")
    
    # Run flake8 if available
    try:
        cmd = ["python", "-m", "flake8", "github_cli/", "tests/"]
        return run_command(cmd, "Running flake8 linting")
    except FileNotFoundError:
        print("⚠️  flake8 not found, skipping linting")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GitHub CLI Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    
    subparsers = parser.add_subparsers(dest="command", help="Test commands")
    
    # Add subcommands
    subparsers.add_parser("unit", help="Run unit tests")
    subparsers.add_parser("integration", help="Run integration tests")
    subparsers.add_parser("api", help="Run API tests")
    subparsers.add_parser("auth", help="Run authentication tests")
    subparsers.add_parser("ui", help="Run UI tests")
    subparsers.add_parser("models", help="Run model tests")
    subparsers.add_parser("utils", help="Run utility tests")
    subparsers.add_parser("all", help="Run all tests")
    subparsers.add_parser("fast", help="Run fast tests only")
    subparsers.add_parser("coverage", help="Generate coverage report")
    
    args = parser.parse_args()
    
    # Check if pytest is available
    try:
        subprocess.run(["python", "-m", "pytest", "--version"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ pytest not found. Please install it with: pip install pytest")
        return 1
    
    success = True
    
    # Run linting if requested
    if args.lint:
        success = lint_code() and success
    
    # Run tests based on command
    if args.command == "unit":
        success = run_unit_tests(args.verbose, args.coverage) and success
    elif args.command == "integration":
        success = run_integration_tests(args.verbose) and success
    elif args.command == "api":
        success = run_api_tests(args.verbose, args.coverage) and success
    elif args.command == "auth":
        success = run_auth_tests(args.verbose, args.coverage) and success
    elif args.command == "ui":
        success = run_ui_tests(args.verbose, args.coverage) and success
    elif args.command == "models":
        success = run_model_tests(args.verbose, args.coverage) and success
    elif args.command == "utils":
        success = run_utils_tests(args.verbose, args.coverage) and success
    elif args.command == "all":
        success = run_all_tests(args.verbose, args.coverage) and success
    elif args.command == "fast":
        success = run_fast_tests(args.verbose) and success
    elif args.command == "coverage":
        success = generate_coverage_report() and success
    else:
        # Default: run fast tests
        success = run_fast_tests(args.verbose) and success
    
    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
