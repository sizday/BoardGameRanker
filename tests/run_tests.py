#!/usr/bin/env python3
"""
Test runner script for Board Game Ranker
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🚀 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Run test suite"""
    print("🎯 Board Game Ranker - Test Suite")
    print("=" * 60)

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Set PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root / 'backend')

    tests = [
        ("Unit Tests", "pytest tests/ -m 'not integration' --tb=short"),
        ("Integration Tests", "pytest tests/ -m integration --tb=short"),
        ("All Tests with Coverage", "pytest tests/ --cov=backend --cov-report=term-missing --cov-fail-under=70"),
    ]

    results = []

    for test_name, test_cmd in tests:
        success = run_command(test_cmd, test_name)
        results.append((test_name, success))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")

    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        print("\n💡 Tips:")
        print("- Run 'pytest tests/test_<name>.py -v' for detailed output")
        print("- Use 'pytest --pdb' to debug failing tests")
        print("- Check test coverage with 'pytest --cov=backend --cov-report=html'")
        return 1

if __name__ == "__main__":
    sys.exit(main())