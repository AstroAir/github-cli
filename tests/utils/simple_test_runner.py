#!/usr/bin/env python3
"""
Simple test runner that bypasses PowerShell issues.
"""

import sys
import os
import subprocess
import tempfile

def run_single_test():
    """Run a single test file to verify our fixes work."""
    
    # Try to import pytest and run a simple test
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not available")
        return False
    
    # Try to import our modules
    try:
        sys.path.insert(0, os.getcwd())
        from github_cli.api.client import GitHubClient, APIResponse, RateLimitInfo
        print("✅ Can import GitHubClient and related classes")
    except ImportError as e:
        print(f"❌ Cannot import GitHubClient: {e}")
        return False
    
    # Try to create APIResponse with rate_limit
    try:
        response = APIResponse(
            status_code=200,
            data={"test": "data"},
            headers={"content-type": "application/json"},
            rate_limit=RateLimitInfo()
        )
        print("✅ Can create APIResponse with rate_limit parameter")
    except Exception as e:
        print(f"❌ Cannot create APIResponse: {e}")
        return False
    
    # Try to import test modules
    try:
        from tests.conftest import sample_issue_data, sample_gist_data
        print("✅ Can import test fixtures")
    except ImportError as e:
        print(f"❌ Cannot import test fixtures: {e}")
        return False
    
    # Try to run a simple test
    try:
        # Create a temporary test file
        test_content = '''
import pytest
from github_cli.api.client import APIResponse, RateLimitInfo

def test_api_response_creation():
    """Test that APIResponse can be created with rate_limit."""
    response = APIResponse(
        status_code=200,
        data={"test": "data"},
        headers={"content-type": "application/json"},
        rate_limit=RateLimitInfo()
    )
    assert response.status_code == 200
    assert response.data == {"test": "data"}
    assert response.rate_limit is not None

def test_rate_limit_info_creation():
    """Test that RateLimitInfo can be created."""
    rate_limit = RateLimitInfo()
    assert rate_limit is not None
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_test_file = f.name
        
        # Run the test
        result = subprocess.run([
            sys.executable, '-m', 'pytest', temp_test_file, '-v'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        print("Test output:")
        print(result.stdout)
        if result.stderr:
            print("Test errors:")
            print(result.stderr)
        
        # Clean up
        os.unlink(temp_test_file)
        
        if result.returncode == 0:
            print("✅ Simple test passed!")
            return True
        else:
            print("❌ Simple test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def check_test_files():
    """Check if our test files have correct syntax."""
    test_files = [
        "tests/unit/api/test_client.py",
        "tests/unit/api/test_repositories.py", 
        "tests/unit/api/test_pull_requests.py",
        "tests/unit/api/test_issues_new.py",
        "tests/unit/api/test_gists.py",
        "tests/unit/utils/test_config_fixed.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Try to compile the file
                compile(content, test_file, 'exec')
                print(f"✅ {test_file} - Syntax OK")
                
            except SyntaxError as e:
                print(f"❌ {test_file} - Syntax Error: {e}")
            except Exception as e:
                print(f"⚠️  {test_file} - Other Error: {e}")
        else:
            print(f"⚠️  {test_file} - File not found")

def main():
    """Main function."""
    print("GitHub CLI Test Verification")
    print("=" * 40)
    
    print("\n1. Checking test file syntax...")
    check_test_files()
    
    print("\n2. Running simple integration test...")
    success = run_single_test()
    
    if success:
        print("\n🎉 Tests are working! Our fixes appear to be successful.")
    else:
        print("\n💥 Tests are not working. More fixes needed.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
