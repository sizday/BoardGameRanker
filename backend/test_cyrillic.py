#!/usr/bin/env python3

name = "Покорение марса"
print(f"Name: {name}")
print(f"Name repr: {repr(name)}")

has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in name)
print(f"Has Cyrillic: {has_cyrillic}")

# Check each character
for char in name:
    is_cyrillic = '\u0400' <= char <= '\u04FF'
    print(f"Char: {char}, ord: {ord(char)}, is_cyrillic: {is_cyrillic}")