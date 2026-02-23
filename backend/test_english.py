#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')
from app.services.bgg import search_boardgame

query = 'Terraforming Mars'
print(f'Searching BGG for: {query}')

try:
    results = search_boardgame(query, exact=False)
    print(f'Found {len(results)} results:')

    for i, result in enumerate(results[:5], 1):
        print(f'{i}. ID:{result.get("id")} Name:"{result.get("name")}" Type:{result.get("type")}')

    game7 = next((r for r in results if r.get('id') == 7), None)
    if game7:
        print(f'Game with ID 7: "{game7.get("name")}"')
    else:
        print('Game with ID 7 not found in results')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()