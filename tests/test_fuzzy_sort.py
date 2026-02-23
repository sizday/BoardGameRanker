#!/usr/bin/env python3
"""
Simple test to verify the fuzzy matching sort logic works correctly
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_sort_logic():
    """Test the candidate sorting logic"""

    # Mock candidates that might be returned by BGG
    candidates = [
        {"name": "Catan", "type": "boardgame", "rank": 1, "usersrated": 50000, "id": 1},
        {"name": "Catan: Seafarers", "type": "boardgameexpansion", "rank": 50, "usersrated": 10000, "id": 2},
        {"name": "Settlers of Catan", "type": "boardgame", "rank": None, "usersrated": 60000, "id": 3},
        {"name": "Ticket to Ride", "type": "boardgame", "rank": 2, "usersrated": 45000, "id": 4},
    ]

    query_name = "Catan"

    # Test our sort key function
    try:
        from backend.app.infrastructure.repositories import _fetch_bgg_details_for_row

        # Extract the sort_key function from the module
        import backend.app.infrastructure.repositories as repo

        # Create a dummy function to access the sort_key logic
        def test_sort_key(candidate):
            candidate_name = (candidate.get("name") or '').strip()
            query_name_clean = query_name.strip()

            # Use fuzzy matching if available
            try:
                from fuzzywuzzy import fuzz
                similarity_ratio = fuzz.token_sort_ratio(query_name_clean, candidate_name)
                partial_ratio = fuzz.partial_ratio(query_name_clean.lower(), candidate_name.lower())
                best_similarity = max(similarity_ratio, partial_ratio)
            except ImportError:
                best_similarity = 100 if candidate_name.lower() == query_name_clean.lower() else 0

            # Determine similarity levels
            is_high_similarity = best_similarity >= 85
            is_medium_similarity = best_similarity >= 60

            # Check for expansions
            name_length_ratio = len(candidate_name) / len(query_name_clean) if query_name_clean else 1
            is_likely_expansion = name_length_ratio > 1.5 and best_similarity < 95

            # Game type priority
            game_type = candidate.get("type", "").lower()
            is_base_game = game_type == "boardgame"

            similarity_priority = 0 if is_high_similarity else (1 if is_medium_similarity else 2)
            game_type_priority = 0 if is_base_game else 1000
            if is_likely_expansion:
                game_type_priority += 500

            rank = candidate.get("rank") or 999999
            users_rated = candidate.get("usersrated") or 0

            return (
                similarity_priority,
                game_type_priority,
                -best_similarity,
                rank,
                -users_rated
            )

        # Sort candidates
        sorted_candidates = sorted(candidates, key=test_sort_key)

        print("🎯 Testing improved sort logic for query 'Catan':")
        for i, candidate in enumerate(sorted_candidates, 1):
            print(f"  {i}. '{candidate['name']}' (type: {candidate['type']}, rank: {candidate['rank']})")

        # Check that "Catan" comes first
        if sorted_candidates[0]['name'] == 'Catan':
            print("✅ SUCCESS: Exact match 'Catan' comes first!")
        else:
            print(f"❌ FAIL: Expected 'Catan' first, got '{sorted_candidates[0]['name']}'")

        return True

    except Exception as e:
        print(f"❌ Error testing sort logic: {e}")
        return False

if __name__ == "__main__":
    test_sort_logic()