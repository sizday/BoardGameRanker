#!/usr/bin/env python3
"""
Test script for clear database functionality
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_clear_database_api_simulation():
    """Test API clear database endpoint simulation"""
    print("Testing clear database API simulation...")

    try:
        # Test that we can import required modules
        sys.path.insert(0, str(project_root / 'backend'))
        from app.api.clear_database import ClearDatabaseRequest

        # Create request object without confirmation (should fail)
        try:
            request_no_confirm = ClearDatabaseRequest(confirm=False)
            print("ERROR: Request without confirmation should fail but didn't")
            return False
        except Exception:
            print("OK: Request without confirmation properly rejected")

        # Create request object with confirmation
        request = ClearDatabaseRequest(confirm=True)

        print("OK: API request object created successfully")
        print(f"   Confirm: {request.confirm}")

        return True

    except Exception as e:
        print(f"ERROR: API simulation test failed: {e}")
        return False


async def test_clear_database_function_import():
    """Test that we can import the clear_all_data function"""
    print("Testing clear_all_data function import...")

    try:
        # Test that we can import required modules
        sys.path.insert(0, str(project_root / 'backend'))
        from app.infrastructure.repositories import clear_all_data

        print("OK: clear_all_data function imported successfully")

        return True

    except Exception as e:
        print(f"ERROR: Function import test failed: {e}")
        return False


async def main():
    """Run clear database tests"""
    print("Clear Database Functionality Tests")
    print("=" * 50)

    tests = [
        ("API Simulation Test", test_clear_database_api_simulation),
        ("Function Import Test", test_clear_database_function_import),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*10} {test_name} {'='*10}")
        success = await test_func()
        results.append((test_name, success))

    print("\n" + "=" * 50)
    print("Clear Database Test Results:")

    all_passed = True
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("All clear database tests passed!")
        print("\nTo test full clear database functionality:")
        print("1. Start the backend server: cd backend && python wsgi.py")
        print("2. Make a POST request to /clear-database with {\"confirm\": true}")
    else:
        print("Some clear database tests failed.")

    return all_passed


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)