#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

try:
    from fuzzywuzzy import fuzz
    print("Testing fuzzy matching with Russian text...")

    text1 = "Покорение марса"
    text2 = "Cathedral"

    ratio = fuzz.token_sort_ratio(text1, text2)
    partial = fuzz.partial_ratio(text1.lower(), text2.lower())

    print(f"Text 1: '{text1}'")
    print(f"Text 2: '{text2}'")
    print(f"Token sort ratio: {ratio}")
    print(f"Partial ratio: {partial}")
    print(f"Max similarity: {max(ratio, partial)}")

    # Test with English
    text3 = "Terraforming Mars"
    ratio2 = fuzz.token_sort_ratio(text1, text3)
    partial2 = fuzz.partial_ratio(text1.lower(), text3.lower())

    print(f"\nText 1: '{text1}'")
    print(f"Text 3: '{text3}'")
    print(f"Token sort ratio: {ratio2}")
    print(f"Partial ratio: {partial2}")
    print(f"Max similarity: {max(ratio2, partial2)}")

except ImportError:
    print("fuzzywuzzy not available")