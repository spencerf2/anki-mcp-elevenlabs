import pytest
from ..server import (
    get_deck_notes,
    get_deck_sample, 
    get_deck_note_types,
    validate_deck_media,
    _anki_request
)

@pytest.mark.asyncio
async def test_can_list_all_notes_from_existing_deck():
    """Should return formatted string containing all notes when deck exists"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    result = await get_deck_notes(deck_name)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert deck_name in result

@pytest.mark.asyncio
async def test_returns_no_notes_message_when_deck_is_empty():
    """Should return clear message when requesting notes from non-existent deck"""
    non_existent_deck = "NonExistentDeck12345"
    
    result = await get_deck_notes(non_existent_deck)
    assert "No notes found" in result
    assert non_existent_deck in result

@pytest.mark.asyncio
async def test_can_retrieve_limited_sample_of_notes():
    """Should return only requested number of notes when sampling"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    # Test with small sample size
    result = await get_deck_sample(deck_name, sample_size=3)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Sample of" in result

@pytest.mark.asyncio
async def test_sample_respects_maximum_available_notes():
    """Should not fail when requested sample size exceeds available notes"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    # Request very large sample - should not error
    result = await get_deck_sample(deck_name, sample_size=1000)
    assert isinstance(result, str)
    assert not result.startswith("Error:")

@pytest.mark.asyncio
async def test_can_discover_note_types_used_in_deck():
    """Should identify all different note models/templates present in deck"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    result = await get_deck_note_types(deck_name)
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Note types used in deck" in result

@pytest.mark.asyncio
async def test_reports_no_note_types_for_empty_deck():
    """Should handle empty decks gracefully when checking note types"""
    non_existent_deck = "NonExistentDeck12345"
    
    result = await get_deck_note_types(non_existent_deck)
    assert "No notes found" in result
    assert non_existent_deck in result

@pytest.mark.asyncio
async def test_can_validate_media_references_in_deck():
    """Should check all media file references and report status"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    result = await validate_deck_media(deck_name)
    assert isinstance(result, dict)
    assert result.get("success") is not False
    assert "total_notes" in result
    assert "notes_with_missing_media" in result
    assert "missing_files" in result
    assert "broken_notes" in result

@pytest.mark.asyncio
async def test_reports_zero_issues_for_empty_deck():
    """Should report clean validation results when deck has no notes"""
    non_existent_deck = "NonExistentDeck12345"
    
    result = await validate_deck_media(non_existent_deck)
    assert result.get("success") is True
    assert result.get("total_notes") == 0
    assert result.get("notes_with_missing_media") == 0
    assert len(result.get("missing_files", [])) == 0

@pytest.mark.asyncio
async def test_validation_can_run_without_making_changes():
    """Should validate media without modifying any notes when not requested"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    result = await validate_deck_media(deck_name, delete_missing_refs=False)
    assert isinstance(result, dict)
    assert "deleted_refs_count" not in result  # Should not be present when not deleting

@pytest.mark.asyncio
async def test_sampling_uses_default_size_when_not_specified():
    """Should use reasonable default sample size when none provided"""
    decks_result = await _anki_request("deckNames")
    if decks_result.get("error") or not decks_result["result"]:
        pytest.skip("No decks available for testing")
    
    deck_name = decks_result["result"][0]
    
    result = await get_deck_sample(deck_name)  # No sample_size specified
    assert isinstance(result, str)
    assert not result.startswith("Error:")
    assert "Sample of" in result
