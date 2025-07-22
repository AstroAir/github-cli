#!/usr/bin/env python3
"""
Simple test runner to verify our test fixes work.
"""

import subprocess
import sys
import os

def run_test(test_path):
    """Run a specific test file and return the result."""
    try:
        # Use the Python executable that has pytest installed
        cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running test: {e}")
        return False

def main():
    """Run tests to verify our fixes."""
    print("Testing our API client fixes...")
    
    # Test the API client tests we just fixed
    test_files = [
        "tests/unit/api/test_client.py",
        "tests/unit/test_main.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n{'='*60}")
            print(f"Testing: {test_file}")
            print('='*60)
            
            success = run_test(test_file)
            
            if success:
                print(f"✅ {test_file} - PASSED")
            else:
                print(f"❌ {test_file} - FAILED")
        else:
            print(f"⚠️  {test_file} - FILE NOT FOUND")

if __name__ == "__main__":
    main()
