#!/usr/bin/env python3
"""
Interactive testing script for media methods.
Run this to test the new media functions directly.
"""

import asyncio
import pytest
from ..server import (
    list_media_files,
    media_file_exists,
    retrieve_media_file,
    get_media_directory,
)

@pytest.mark.asyncio
async def test_media_methods():
    """Test all media methods and print results"""
    
    print("=== Testing Media Methods ===\n")
    
    # Test 1: List all media files
    print("1. Testing list_media_files()...")
    result = await list_media_files()
    print(f"Result: {result}")
    print()
    
    # Test 2: List only mp3 files
    print("2. Testing list_media_files(pattern='*.mp3')...")
    result = await list_media_files(pattern="*.mp3")
    print(f"Result: {result}")
    print()
    
    # Test 3: Get media directory
    print("3. Testing get_media_directory()...")
    result = await get_media_directory()
    print(f"Result: {result}")
    print()
    
    # Test 4: Check if a file exists (use first file from list if available)
    print("4. Testing media_file_exists()...")
    
    # First get a real filename from the collection
    files_result = await list_media_files()
    if files_result.get("success") and files_result.get("files"):
        test_filename = files_result["files"][0]
        print(f"Testing with existing file: {test_filename}")
        result = await media_file_exists(test_filename)
        print(f"Result: {result}")
        print()
        
        # Test 5: Try to retrieve that file (without base64 for cleaner output)
        print("5. Testing retrieve_media_file()...")
        result = await retrieve_media_file(test_filename, return_base64=False)
        print(f"Result: {result}")
        print()
    else:
        print("No media files found to test with")
        print()
    
    # Test 6: Check non-existent file
    print("6. Testing with non-existent file...")
    result = await media_file_exists("nonexistent_file.mp3")
    print(f"Result: {result}")
    print()
    
    # Test 7: Try to retrieve non-existent file
    print("7. Testing retrieve non-existent file...")
    result = await retrieve_media_file("nonexistent_file.mp3", return_base64=False)
    print(f"Result: {result}")
    print()
    
    print("=== Testing Complete ===")

if __name__ == "__main__":
    # Make sure Anki is running with AnkiConnect
    print("Make sure Anki is running with AnkiConnect plugin!")
    print("Press Enter to continue...")
    input()
    
    asyncio.run(test_media_methods())
