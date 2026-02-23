#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

# Test the new validation logic
def test_explicit_id_validation():
    """Test the explicit bgg_id validation logic"""

    # Mock the dependencies
    from app.infrastructure import repositories as repo_module

    # Mock get_boardgame_details to return Cathedral for ID 7
    def mock_get_boardgame_details(game_id):
        if game_id == 7:
            return {
                "id": 7,
                "name": "Cathedral",
                "type": "boardgame",
                "yearpublished": 1979,
                "rank": 2572
            }
        return None

    # Save original function
    original_get_details = repo_module.get_boardgame_details
    original_search = repo_module.search_boardgame

    # Mock search to return Terraforming Mars
    def mock_search_boardgame(name, exact=False):
        return [{
            "id": 167791,
            "name": "Terraforming Mars",
            "type": "boardgame"
        }]

    repo_module.get_boardgame_details = mock_get_boardgame_details
    repo_module.search_boardgame = mock_search_boardgame

    try:
        # Test case 1: Wrong explicit ID for Russian name (should be rejected and search by name)
        print("Test 1: Wrong explicit ID for Russian name (ID 7 for 'Покорение марса')")
        from app.infrastructure.repositories import _fetch_bgg_details_for_row
        result = _fetch_bgg_details_for_row({
            "name": "Покорение марса",
            "bgg_id": 7
        })

        print(f"Result: ID={result.get('id') if result else None}, Name='{result.get('name') if result else None}'")

        if result and result.get("id") == 167791:  # Should find Terraforming Mars
            print("✅ SUCCESS: Wrong explicit ID was ignored for Russian name, found correct game by name")
        elif result and result.get("id") == 7:
            print("❌ FAIL: Wrong explicit ID was accepted for Russian name")
        else:
            print("❌ FAIL: No result returned")

        # Test case 2: Correct explicit ID (should be accepted)
        print("\nTest 2: Correct explicit ID (ID 167791 for 'Terraforming Mars')")

        # Mock get_boardgame_details for Terraforming Mars
        def mock_get_details_correct(game_id):
            if game_id == 167791:
                return {
                    "id": 167791,
                    "name": "Terraforming Mars",
                    "type": "boardgame",
                    "yearpublished": 2016,
                    "rank": 1
                }
            return None

        repo_module.get_boardgame_details = mock_get_details_correct

        result2 = _fetch_bgg_details_for_row({
            "name": "Terraforming Mars",
            "bgg_id": 167791
        })

        print(f"Result2: ID={result2.get('id') if result2 else None}, Name='{result2.get('name') if result2 else None}'")

        if result2 and result2.get("id") == 167791:
            print("✅ SUCCESS: Correct explicit ID was accepted")
        else:
            print("❌ FAIL: Correct explicit ID was rejected")

    finally:
        # Restore original functions
        repo_module.get_boardgame_details = original_get_details
        repo_module.search_boardgame = original_search

if __name__ == "__main__":
    test_explicit_id_validation()