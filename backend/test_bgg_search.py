#!/usr/bin/env python3
"""
Test script to check what BGG returns for "Покорение марса"
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/app')

def test_bgg_search():
    """Test BGG search for Russian game name"""
    try:
        from app.services.bgg import search_boardgame

        query = "Покорение марса"
        print(f"🔍 Searching BGG for: '{query}'")

        results = search_boardgame(query, exact=False)

        print(f"📊 Found {len(results)} results:")
        for i, result in enumerate(results[:10], 1):  # Show first 10
            print(f"  {i}. ID: {result.get('id')}, Name: '{result.get('name')}', Type: {result.get('type')}")

        # Check if Terraforming Mars is in results
        terraforming_found = any("Terraforming Mars" in (r.get('name') or '') for r in results)
        print(f"\n🔍 Terraforming Mars found in results: {terraforming_found}")

        # Check game with ID 7
        game_7 = next((r for r in results if r.get('id') == 7), None)
        if game_7:
            print(f"🎲 Game with ID 7: '{game_7.get('name')}'")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bgg_search()