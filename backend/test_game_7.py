#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')
from app.services.bgg import get_boardgame_details

print('Checking what game has ID 7...')

try:
    result = get_boardgame_details(7)
    if result:
        print(f'Game ID 7: "{result.get("name")}"')
        print(f'Type: {result.get("type")}')
        print(f'Year: {result.get("yearpublished")}')
        print(f'Rank: {result.get("rank")}')
    else:
        print('Game with ID 7 not found')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()