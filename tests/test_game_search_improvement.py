#!/usr/bin/env python3
"""
Test script for improved game search logic with fuzzy matching
"""
import sys
import os
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_fuzzy_matching_logic():
    """Test the improved sorting logic for game candidates"""

    # Mock candidates similar to what BGG might return
    mock_candidates = [
        {
            "id": 123,
            "name": "Catan",
            "type": "boardgame",
            "rank": 1,
            "usersrated": 50000
        },
        {
            "id": 456,
            "name": "Catan: Seafarers",
            "type": "boardgameexpansion",
            "rank": 50,
            "usersrated": 10000
        },
        {
            "id": 789,
            "name": "Ticket to Ride",
            "type": "boardgame",
            "rank": 2,
            "usersrated": 45000
        },
        {
            "id": 101,
            "name": "Settlers of Catan",
            "type": "boardgame",
            "rank": None,  # No rank
            "usersrated": 60000
        },
        {
            "id": 202,
            "name": "Catan Card Game",
            "type": "boardgame",
            "rank": 100,
            "usersrated": 5000
        }
    ]

    # Test different query names
    test_queries = [
        "Catan",
        "Settlers of Catan",
        "Ticket to Ride",
        "Some Random Game"
    ]

    print("🧪 Testing improved game search logic...")
    print("=" * 60)

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 40)

        # Import the sort_key function from repositories
        try:
            from backend.app.infrastructure.repositories import _fetch_bgg_details_for_row

            # Create a mock function that returns our test candidates
            def mock_get_boardgame_details(game_id):
                # Simulate API call
                for candidate in mock_candidates:
                    if candidate["id"] == game_id:
                        return candidate
                return None

            # Temporarily replace the function
            import backend.app.infrastructure.repositories as repo_module
            original_get_details = repo_module.get_boardgame_details
            repo_module.get_boardgame_details = mock_get_boardgame_details

            # Test the sorting logic by calling _fetch_bgg_details_for_row
            # We need to mock search_boardgame too
            def mock_search_boardgame(name, exact=False):
                # Return all candidates for any search
                return [{"id": c["id"], "name": c["name"], "type": c["type"]} for c in mock_candidates]

            original_search = repo_module.search_boardgame
            repo_module.search_boardgame = mock_search_boardgame

            # Test the function
            result = repo_module._fetch_bgg_details_for_row({"name": query})

            # Restore original functions
            repo_module.get_boardgame_details = original_get_details
            repo_module.search_boardgame = original_search

            if result:
                print(f"✅ Found: '{result.get('name')}' (ID: {result.get('id')}, Rank: {result.get('rank')})")
            else:
                print("❌ No result found")

        except ImportError as e:
            print(f"❌ Import error: {e}")
        except Exception as e:
            print(f"❌ Test error: {e}")

    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_fuzzy_matching_logic()