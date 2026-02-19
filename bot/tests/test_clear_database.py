#!/usr/bin/env python3
"""
Test script for clear database bot functionality
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_clear_database_service_import():
    """Test that we can import the clear_database function"""
    print("Testing clear_database service import...")

    try:
        # Test that we can import required modules
        sys.path.insert(0, str(project_root / 'bot'))
        from services.clear_database import clear_database

        print("OK: clear_database function imported successfully")

        return True

    except Exception as e:
        print(f"ERROR: Function import test failed: {e}")
        return False


async def main():
    """Run clear database bot tests"""
    print("Clear Database Bot Functionality Tests")
    print("=" * 50)

    tests = [
        ("Service Import Test", test_clear_database_service_import),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*10} {test_name} {'='*10}")
        success = await test_func()
        results.append((test_name, success))

    print("\n" + "=" * 50)
    print("Clear Database Bot Test Results:")

    all_passed = True
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("All clear database bot tests passed!")
        print("\nTo test full functionality:")
        print("1. Start the bot: cd bot && python main.py")
        print("2. Send /clear_database command to bot as admin")
    else:
        print("Some clear database bot tests failed.")

    return all_passed


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)