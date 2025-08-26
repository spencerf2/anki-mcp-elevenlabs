import asyncio
import pytest
from ..server import find_missing_media_references

@pytest.mark.asyncio
async def test_validation():
    print("=== Testing find_missing_media_references ===\n")
    
    # Test 1: Single card with existing media (should return empty dict)
    print("Test 1: Card with existing media...")
    test_card_good = [{"Front": "Hello", "Audio": "[sound:1-A-Arpa-Speaker2-1.mp3]"}]
    result = await find_missing_media_references(test_card_good)
    print(f"Result: {result}")
    print(f"Expected: Empty dict (no missing files)")
    print()
    
    # Test 2: Single card with missing media
    print("Test 2: Card with missing media...")
    test_card_bad = [{"Front": "Hello", "Audio": "[sound:nonexistent_file.mp3]"}]
    result = await find_missing_media_references(test_card_bad)
    print(f"Result: {result}")
    print(f"Expected: {{0: ['nonexistent_file.mp3']}}")
    print()
    
    # Test 3: Multiple cards, some with issues
    print("Test 3: Multiple cards with mixed media...")
    test_cards_mixed = [
        {"Front": "Good card", "Audio": "[sound:1-A-Arpa-Speaker2-1.mp3]"},  # Card 0 - good
        {"Front": "Bad card", "Audio": "[sound:missing1.mp3]"},               # Card 1 - bad  
        {"Front": "No audio", "Back": "Just text"},                          # Card 2 - no media
        {"Front": "Multiple bad", "Audio": "[sound:missing1.mp3] [sound:missing2.mp3]"},  # Card 3 - multiple bad
    ]
    result = await find_missing_media_references(test_cards_mixed)
    print(f"Result: {result}")
    print(f"Expected: Cards 1 and 3 should have missing files")
    print()
    
    # Test 4: No media references at all
    print("Test 4: Cards with no media references...")
    test_cards_no_media = [
        {"Front": "Hello", "Back": "World"},
        {"Question": "What?", "Answer": "Nothing"},
    ]
    result = await find_missing_media_references(test_cards_no_media)
    print(f"Result: {result}")
    print(f"Expected: Empty dict (no media to check)")
    print()
    
    # Test 5: Multiple media in same field
    print("Test 5: Multiple media references in same field...")
    test_card_multiple = [{"Front": "Test", "Audio": "[sound:1-A-Arpa-Speaker2-1.mp3] and [sound:missing.mp3]"}]
    result = await find_missing_media_references(test_card_multiple)
    print(f"Result: {result}")
    print(f"Expected: {{0: ['missing.mp3']}} (only missing file)")
    print()
    
    print("=== Testing Complete ===")

if __name__ == "__main__":
    print("Make sure Anki is running with AnkiConnect plugin!")
    print("Press Enter to continue...")
    input()
    
    asyncio.run(test_validation())