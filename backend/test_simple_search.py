#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')
from app.infrastructure.repositories import _fetch_bgg_details_for_row

# Test the simplified search logic
print("Testing simplified search logic...")

# Test with Russian game name that should find Terraforming Mars
result = _fetch_bgg_details_for_row({
    "name": "Terraforming Mars",
    "bgg_id": 99999  # Wrong ID, should be ignored
})

if result and result.get("id") == 167791:
    print("✅ SUCCESS: Found Terraforming Mars by name search")
else:
    print(f"❌ FAIL: Expected Terraforming Mars (167791), got {result.get('id') if result else None}")

print("Test completed!")