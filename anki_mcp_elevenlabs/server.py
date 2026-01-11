import base64
import random
import re
from pathlib import Path
from typing import Annotated

import requests
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .server_utils import safe_get_error
from .tts import generate_tts_audio

mcp_server = FastMCP("anki-mcp")

ANKI_CONNECT_URL = "http://localhost:8765"


async def _anki_request(action: str, params: dict = None) -> dict:
    """Generic AnkiConnect request handler with consistent error handling. Return AnkiConnect format for backward compatibility."""
    try:
        payload = {"action": action, "version": 6}
        if params:
            payload["params"] = params

        response = requests.post(ANKI_CONNECT_URL, json=payload)

        if response.status_code != 200:
            return {
                "result": None,
                "error": f"Failed to connect to Anki: {response.status_code}",
            }

        result = response.json()
        return result

    except Exception as e:
        return {"result": None, "error": f"Request failed: {str(e)}"}


async def _fetch_deck_notes(deck_name: str, sample_size: int = None) -> dict:
    """Shared helper for getting notes from a deck."""
    # Get all note IDs for the deck
    find_result = await _anki_request("findNotes", {"query": f'deck:"{deck_name}"'})
    if find_result.get("error"):
        return find_result

    note_ids = find_result["result"]
    if not note_ids:
        return {
            "result": {
                "notes": [],
                "count": 0,
                "total_in_deck": 0,
            },
            "error": None,
        }

    # Apply sampling if requested
    original_count = len(note_ids)
    if sample_size is not None:
        actual_sample_size = min(sample_size, len(note_ids))
        note_ids = random.sample(note_ids, actual_sample_size)

    # Get detailed note info
    notes_result = await _anki_request("notesInfo", {"notes": note_ids})
    if notes_result.get("error"):
        return notes_result

    notes = notes_result["result"]
    return {
        "result": {
            "notes": notes,
            "count": len(notes),
            "total_in_deck": original_count,
        },
        "error": None,
    }


MAX_MEDIA_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _prepare_media_data(data: str) -> str:
    """
    Convert media data to base64 format if needed.

    Accepts either:
    - File path -> reads file and converts to base64
    - Base64 string -> passes through unchanged

    Returns:
        Base64 encoded string

    Raises:
        ValueError: If file exceeds MAX_MEDIA_FILE_SIZE
    """
    try:
        path = Path(data)
        with open(path, "rb") as f:
            raw = f.read(MAX_MEDIA_FILE_SIZE + 1)
        if len(raw) > MAX_MEDIA_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(raw)}+ bytes (max {MAX_MEDIA_FILE_SIZE})"
            )
        return base64.b64encode(raw).decode("utf-8")
    except (OSError, FileNotFoundError, IsADirectoryError, PermissionError):
        # Not a readable file - assume base64
        pass

    # Not a valid file path - assume it's already base64
    return data


@mcp_server.tool()
async def list_decks() -> str:
    """List all available Anki decks."""
    result = await _anki_request("deckNames")

    if result.get("error"):
        return f"Error: {result['error']}"

    decks = result["result"]
    return f"Available decks ({len(decks)}):\n" + "\n".join(
        f"- {deck}" for deck in decks
    )


@mcp_server.tool()
async def get_deck_notes(
    deck_name: Annotated[
        str, Field(description="Name of the Anki deck to retrieve notes from")
    ],
    offset: Annotated[
        int, Field(description="Starting position for pagination (0-based)", ge=0)
    ] = 0,
    limit: Annotated[
        int, Field(description="Maximum number of notes to return", ge=1, le=100)
    ] = 50,
    ids_only: Annotated[
        bool, Field(description="Return only note IDs instead of full note data")
    ] = False,
) -> str:
    """Get notes/cards from a specific deck with pagination support."""
    find_result = await _anki_request("findNotes", {"query": f'deck:"{deck_name}"'})
    if find_result.get("error"):
        return f"Error: {find_result['error']}"

    all_note_ids = find_result["result"]
    if not all_note_ids:
        return f"No notes found in deck '{deck_name}'"

    total_notes = len(all_note_ids)

    start_idx = offset
    end_idx = min(offset + limit, total_notes)

    if start_idx >= total_notes:
        return (
            f"Offset {offset} exceeds total notes ({total_notes}) in deck '{deck_name}'"
        )

    paginated_ids = all_note_ids[start_idx:end_idx]

    if ids_only:
        return (
            f"Note IDs in deck '{deck_name}' (showing {len(paginated_ids)} of {total_notes}, offset {offset}):\n"
            + "\n".join(map(str, paginated_ids))
        )

    notes_result = await _anki_request("notesInfo", {"notes": paginated_ids})
    if notes_result.get("error"):
        return f"Error retrieving note details: {notes_result['error']}"

    notes = notes_result["result"]

    # Format the notes for better readability
    output = [
        f"Notes in deck '{deck_name}' (showing {len(notes)} of {total_notes}, offset {offset}):\n"
    ]

    for i, note in enumerate(notes, start=offset + 1):
        output.append(f"Note {i} (ID: {note['noteId']}):")
        output.append(f"  Model: {note['modelName']}")
        output.append(f"  Tags: {', '.join(note['tags']) if note['tags'] else 'None'}")
        output.append("  Fields:")
        for field_name, field_value in note["fields"].items():
            # Truncate long field values for readability
            value = (
                field_value["value"][:100] + "..."
                if len(field_value["value"]) > 100
                else field_value["value"]
            )
            output.append(f"    {field_name}: {value}")
        output.append("")

    has_more = end_idx < total_notes
    if has_more:
        output.append(
            f"... {total_notes - end_idx} more notes available (use offset={end_idx})"
        )

    return "\n".join(output)


@mcp_server.tool()
async def get_deck_sample(
    deck_name: Annotated[
        str, Field(description="Name of the Anki deck to sample notes from")
    ],
    sample_size: Annotated[
        int,
        Field(
            description="Number of notes to randomly sample from the deck", ge=1, le=50
        ),
    ] = 5,
) -> str:
    """Get a random sample of notes from a specific deck to understand typical note structure."""
    result = await _fetch_deck_notes(deck_name, sample_size=sample_size)

    if result.get("error"):
        return f"Error: {result['error']}"

    data = result["result"]
    notes = data["notes"]
    total_in_deck = data["total_in_deck"]

    if not notes:
        return f"No notes found in deck '{deck_name}'"

    # Format the notes for better readability
    output = [
        f"Sample of {len(notes)} notes from deck '{deck_name}' (total: {total_in_deck}):\n"
    ]

    for i, note in enumerate(notes, 1):
        output.append(f"Sample Note {i} (ID: {note['noteId']}):")
        output.append(f"  Model: {note['modelName']}")
        output.append(f"  Tags: {', '.join(note['tags']) if note['tags'] else 'None'}")
        output.append("  Fields:")
        for field_name, field_value in note["fields"].items():
            # Truncate long field values for readability
            value = (
                field_value["value"][:200] + "..."
                if len(field_value["value"]) > 200
                else field_value["value"]
            )
            output.append(f"    {field_name}: {value}")
        output.append("")

    return "\n".join(output)


@mcp_server.tool()
async def get_deck_note_types(
    deck_name: Annotated[
        str, Field(description="Name of the Anki deck to analyze for note types")
    ],
) -> str:
    """Get the note types (models) and their field definitions used in a specific deck."""
    # Use helper with sampling to find model types
    result = await _fetch_deck_notes(deck_name, sample_size=50)

    if result.get("error"):
        return f"Error: {result['error']}"

    data = result["result"]
    notes = data["notes"]

    if not notes:
        return f"No notes found in deck '{deck_name}'"

    # Find unique model names used in this deck
    model_names = set()
    for note in notes:
        model_names.add(note["modelName"])

    # Get field names for each model
    output = [f"Note types used in deck '{deck_name}':\n"]

    for model_name in sorted(model_names):
        fields_result = await _anki_request(
            "modelFieldNames", {"modelName": model_name}
        )

        if not fields_result.get("error"):
            fields = fields_result["result"]
            output.append(f"Model: {model_name}")
            output.append(f"  Fields: {', '.join(fields)}")
            output.append("")

    return "\n".join(output)


@mcp_server.tool()
async def create_note(
    deck_name: Annotated[
        str, Field(description="Name of the Anki deck to add the note to")
    ],
    model_name: Annotated[
        str, Field(description="Name of the note type/model to use for this note")
    ],
    fields: Annotated[
        dict,
        Field(
            description="Dictionary mapping field names to their values (e.g., {'Front': 'Question', 'Back': 'Answer'})"
        ),
    ],
    tags: Annotated[
        list, Field(description="Optional list of tags to add to the note")
    ] = None,
    validate_media: Annotated[
        bool,
        Field(
            description="Check that all [sound:...] references exist before creating note"
        ),
    ] = False,
):
    """Create a new note in the specified deck with the given fields and tags."""
    if tags is None:
        tags = []

    if validate_media:
        missing_media = await find_missing_media_references([fields])
        if missing_media:  # If dict is not empty, note 0 has missing files
            missing_files = missing_media[0]
            return {"error": f"Missing media files: {missing_files}", "success": False}

    note_data = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": tags,
    }

    response = requests.post(
        ANKI_CONNECT_URL,
        json={"action": "addNote", "version": 6, "params": {"note": note_data}},
    )

    if response.status_code != 200:
        return {"error": f"Failed to connect to Anki: {response.status_code}"}

    result = response.json()
    if result.get("error"):
        return {"error": result["error"]}

    return {"noteId": result["result"], "success": True}


@mcp_server.tool()
async def update_note(
    note_id: Annotated[int, Field(description="ID of the note to update")],
    fields: Annotated[
        dict,
        Field(
            description="Dictionary mapping field names to their new values (e.g., {'Audio': '[sound:pronunciation.mp3]'})"
        ),
    ],
    tags: Annotated[
        list, Field(description="Optional list of tags to replace existing tags")
    ] = None,
    validate_media: Annotated[
        bool,
        Field(
            description="Check that all [sound:...] references exist before updating note"
        ),
    ] = False,
) -> dict:
    """Update specific fields of an existing note. Perfect for adding audio or other content to existing cards."""

    if validate_media:
        missing_media = await find_missing_media_references([fields])
        if missing_media:  # If dict is not empty, note 0 has missing files
            missing_files = missing_media[0]
            return {"error": f"Missing media files: {missing_files}", "success": False}

    # First get the current note info to validate it exists and get current fields
    response = requests.post(
        ANKI_CONNECT_URL,
        json={"action": "notesInfo", "version": 6, "params": {"notes": [note_id]}},
    )

    if response.status_code != 200:
        return {
            "error": f"Failed to connect to Anki: {response.status_code}",
            "success": False,
        }

    result = response.json()
    if result.get("error"):
        return {"error": result["error"], "success": False}

    notes_info = result["result"]
    if not notes_info or not notes_info[0]:
        return {"error": f"Note with ID {note_id} not found", "success": False}

    current_note = notes_info[0]

    # Prepare the update - merge new fields with existing ones
    updated_fields = {}
    for field_name, field_data in current_note["fields"].items():
        # Keep existing field values
        updated_fields[field_name] = field_data["value"]

    # Update with new field values
    for field_name, new_value in fields.items():
        updated_fields[field_name] = new_value

    # Prepare note data for update
    note_data = {"id": note_id, "fields": updated_fields}

    # Add tags if provided, otherwise keep existing tags
    if tags is not None:
        note_data["tags"] = tags
    else:
        note_data["tags"] = current_note["tags"]

    # Update the note
    response = requests.post(
        ANKI_CONNECT_URL,
        json={
            "action": "updateNoteFields",
            "version": 6,
            "params": {"note": note_data},
        },
    )

    if response.status_code != 200:
        return {
            "error": f"Failed to connect to Anki: {response.status_code}",
            "success": False,
        }

    result = response.json()
    if result.get("error"):
        return {"error": result["error"], "success": False}

    return {
        "success": True,
        "note_id": note_id,
        "updated_fields": list(fields.keys()),
        "message": f"Successfully updated note {note_id} with fields: {', '.join(fields.keys())}",
    }


@mcp_server.tool()
async def create_deck_with_note_type(
    deck_name: Annotated[
        str, Field(description="Name for the new Anki deck to create")
    ],
    model_name: Annotated[
        str, Field(description="Name for the note type/model to create or use")
    ],
    fields: Annotated[
        list,
        Field(
            description="List of field names for the note type (e.g., ['Front', 'Back', 'Extra'])"
        ),
    ],
    card_templates: Annotated[
        list,
        Field(
            description="Optional list of card template definitions. If not provided, basic front/back templates will be created"
        ),
    ] = None,
):
    """Create a new deck and optionally a new note type with specified fields and card templates."""

    # First create the deck
    response = requests.post(
        ANKI_CONNECT_URL,
        json={"action": "createDeck", "version": 6, "params": {"deck": deck_name}},
    )

    if response.status_code != 200:
        return {"error": f"Failed to connect to Anki: {response.status_code}"}

    result = response.json()
    if result.get("error"):
        return {"error": f"Failed to create deck: {result['error']}"}

    deck_id = result["result"]

    # If we need to create a new note type (model)
    if card_templates is None:
        # Default card template for basic front/back cards
        card_templates = [
            {
                "Name": "Card 1",
                "Front": "{{" + fields[0] + "}}",
                "Back": (
                    '{{FrontSide}}<hr id="answer">{{' + fields[1] + "}}"
                    if len(fields) > 1
                    else "{{" + fields[0] + "}}"
                ),
            }
        ]

    # Check if model already exists
    response = requests.post(
        ANKI_CONNECT_URL, json={"action": "modelNames", "version": 6}
    )

    existing_models = []
    if response.status_code == 200:
        result = response.json()
        if not result.get("error"):
            existing_models = result["result"]

    # Create new model if it doesn't exist
    if model_name not in existing_models:
        model_data = {
            "modelName": model_name,
            "inOrderFields": fields,
            "cardTemplates": card_templates,
            "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n",
        }

        response = requests.post(
            ANKI_CONNECT_URL,
            json={"action": "createModel", "version": 6, "params": model_data},
        )

        if response.status_code != 200:
            return {"error": f"Failed to connect to Anki: {response.status_code}"}

        result = response.json()
        if result.get("error"):
            return {"error": f"Failed to create note type: {result['error']}"}

        return {
            "success": True,
            "deck_id": deck_id,
            "deck_name": deck_name,
            "model_created": True,
            "model_name": model_name,
            "fields": fields,
        }
    else:
        return {
            "success": True,
            "deck_id": deck_id,
            "deck_name": deck_name,
            "model_created": False,
            "model_name": model_name,
            "message": f"Note type '{model_name}' already exists, deck created with existing note type",
        }


@mcp_server.tool()
async def list_note_types() -> str:
    """List all available note types (models) with their fields and card templates."""
    # Get all model names
    response = requests.post(
        ANKI_CONNECT_URL, json={"action": "modelNames", "version": 6}
    )

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if error := safe_get_error(result):
        return f"Error: {error}"

    model_names = result["result"]
    output = [f"Available note types ({len(model_names)}):\n"]

    # Get detailed info for each model
    for model_name in sorted(model_names):
        output.append(f"Model: {model_name}")

        # Get field names
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "modelFieldNames",
                "version": 6,
                "params": {"modelName": model_name},
            },
        )

        if response.status_code == 200:
            result = response.json()
            if not safe_get_error(result):
                fields = result["result"]
                output.append(f"  Fields: {', '.join(fields)}")

        # Get templates
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "modelTemplates",
                "version": 6,
                "params": {"modelName": model_name},
            },
        )

        if response.status_code == 200:
            result = response.json()
            if not safe_get_error(result):
                templates = result["result"]
                output.append(f"  Templates: {len(templates)} card type(s)")
                for template_name in templates:
                    output.append(f"    - {template_name}")

        # Get styling (CSS)
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "modelStyling",
                "version": 6,
                "params": {"modelName": model_name},
            },
        )

        if response.status_code == 200:
            result = response.json()
            if not safe_get_error(result):
                css_length = len(result["result"]["css"])
                output.append(f"  CSS: {css_length} characters")

        output.append("")

    return "\n".join(output)


@mcp_server.tool()
async def generate_audio(
    text: Annotated[str, Field(description="Text to convert to speech")],
    provider: Annotated[
        str,
        Field(description="TTS provider to use ('elevenlabs' or 'google')"),
    ] = "elevenlabs",
    language: Annotated[
        str,
        Field(
            description="Language code. For ElevenLabs: simple codes ('en', 'es', 'fr'). For Google TTS: full locale codes ('en-US', 'es-ES', 'cmn-cn')."
        ),
    ] = "en",
    voice: Annotated[
        str,
        Field(
            description="Voice identifier. For ElevenLabs: voice_id (e.g., 'aEO01A4wXwd1O8GPgGlF' for English, 'hEKEQC93QpOYMa6WuwWp' for Spanish). For Google: voice name (e.g., 'cmn-CN-Chirp3-HD-Achernar')"
        ),
    ] = None,
) -> dict:
    """Generate audio using the specified TTS provider (ElevenLabs via Pipecat or Google Cloud TTS)."""
    return await generate_tts_audio(
        text=text, provider=provider, language=language, voice=voice
    )


@mcp_server.tool()
async def create_notes_bulk(
    deck_name: Annotated[
        str, Field(description="Name of the Anki deck to add notes to")
    ],
    notes_list: Annotated[
        list,
        Field(
            description="List of note dictionaries, each containing 'model_name', 'fields', and optionally 'tags'"
        ),
    ],
    validate_media: Annotated[
        bool,
        Field(
            description="Check that all [sound:...] references exist before creating notes"
        ),
    ] = False,
    skip_invalid_media: Annotated[
        bool,
        Field(
            description="Skip notes with missing media instead of failing entire operation"
        ),
    ] = False,
) -> dict:
    """Create multiple notes in a single batch operation for efficiency. Handles duplicates gracefully by reporting which notes are duplicates while still creating non-duplicate notes."""
    if not notes_list:
        return {"error": "No notes provided", "success": False}

    original_notes_count = len(notes_list)

    # Basic input validation
    for i, note_data in enumerate(notes_list):
        if not isinstance(note_data, dict):
            return {"error": f"Note {i + 1} is not a dictionary", "success": False}

        if "model_name" not in note_data or "fields" not in note_data:
            return {
                "error": f"Note {i + 1} missing required 'model_name' or 'fields'",
                "success": False,
            }

    # Media validation if requested
    if validate_media:
        all_fields = [note["fields"] for note in notes_list]
        missing_media = await find_missing_media_references(all_fields)

        if missing_media:  # Some notes have missing media
            if skip_invalid_media:
                # Filter out notes with missing media
                valid_notes = [
                    note for i, note in enumerate(notes_list) if i not in missing_media
                ]
                notes_list = valid_notes  # Use filtered list for creation
                skipped_count = original_notes_count - len(notes_list)
            else:
                # Fail fast with detailed error
                problem_details = {
                    f"note_{i}": files for i, files in missing_media.items()
                }
                return {
                    "error": f"Notes with missing media: {problem_details}",
                    "success": False,
                    "total_attempted": original_notes_count,
                    "notes_with_missing_media": len(missing_media),
                }

    # Prepare notes for Anki
    anki_notes = []
    for i, note_data in enumerate(notes_list):
        anki_note = {
            "deckName": deck_name,
            "modelName": note_data["model_name"],
            "fields": note_data["fields"],
            "tags": note_data.get("tags", []),
        }
        anki_notes.append(anki_note)

    # First check which notes can be added using canAddNotesWithErrorDetail
    response = requests.post(
        ANKI_CONNECT_URL,
        json={
            "action": "canAddNotesWithErrorDetail",
            "version": 6,
            "params": {"notes": anki_notes},
        },
    )

    if response.status_code != 200:
        return {
            "error": f"Failed to connect to Anki: {response.status_code}",
            "success": False,
        }

    result = response.json()
    if result.get("error"):
        return {"error": result["error"], "success": False}

    can_add_results = result["result"]

    # Separate notes that can be added from those that cannot
    valid_notes = []
    valid_note_indices = []
    failed_notes = []

    for i, can_add_result in enumerate(can_add_results):
        if can_add_result["canAdd"]:
            valid_notes.append(anki_notes[i])
            valid_note_indices.append(i)
        else:
            failed_notes.append(
                {
                    "index": i,
                    "fields": notes_list[i]["fields"],
                    "model_name": notes_list[i]["model_name"],
                    "tags": notes_list[i].get("tags", []),
                    "error": can_add_result["error"],
                }
            )

    successful_notes = []

    # Only attempt to add notes that can be added
    if valid_notes:
        response = requests.post(
            ANKI_CONNECT_URL,
            json={"action": "addNotes", "version": 6, "params": {"notes": valid_notes}},
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        note_ids = result["result"]

        # Build successful notes list
        for i, note_id in enumerate(note_ids):
            if note_id is not None:
                original_index = valid_note_indices[i]
                successful_notes.append(
                    {
                        "index": original_index,
                        "note_id": note_id,
                        "fields": notes_list[original_index]["fields"],
                    }
                )

    # Build return message
    message_parts = [f"Created {len(successful_notes)} new notes"]
    if failed_notes:
        message_parts.append(f"{len(failed_notes)} notes failed")
    if (
        validate_media
        and skip_invalid_media
        and "skipped_count" in locals()
        and skipped_count > 0
    ):
        message_parts.append(f"{skipped_count} notes skipped due to missing media")

    return_data = {
        "success": True,
        "total_attempted": original_notes_count,
        "successful_count": len(successful_notes),
        "failed_count": len(failed_notes),
        "successful_notes": successful_notes,
        "failed_notes": failed_notes,
        "message": ". ".join(message_parts) + ".",
    }

    # Add media validation info if applicable
    if validate_media and skip_invalid_media and "skipped_count" in locals():
        return_data["skipped_count"] = skipped_count

    return return_data


@mcp_server.tool()
async def save_media_file(
    filename: Annotated[
        str,
        Field(description="Name of the file to save (e.g., 'audio.mp3', 'image.jpg')"),
    ],
    media_data: Annotated[
        str,
        Field(
            description="Base64 encoded file data OR a local file path (auto-detected)"
        ),
    ],
) -> dict:
    """Save media data as a file in Anki's media collection. Accepts base64 data or a file path."""

    try:
        media_data = _prepare_media_data(media_data)

        # Use AnkiConnect's storeMediaFile action to save the base64 data
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "storeMediaFile",
                "version": 6,
                "params": {"filename": filename, "data": media_data},
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        # AnkiConnect's storeMediaFile returns null on success
        return {
            "success": True,
            "filename": filename,
            "message": f"Media file saved as '{filename}' in Anki's media collection",
        }

    except Exception as e:
        return {"error": f"Failed to save media file: {str(e)}", "success": False}


@mcp_server.tool()
async def generate_and_save_audio(
    text: Annotated[str, Field(description="Text to convert to speech and save")],
    filename: Annotated[
        str, Field(description="Name for the audio file (e.g., 'pronunciation.mp3')")
    ],
    provider: Annotated[
        str,
        Field(description="TTS provider to use ('elevenlabs' or 'google')"),
    ] = "elevenlabs",
    language: Annotated[
        str,
        Field(
            description="Language code. For ElevenLabs: simple codes ('en', 'es', 'fr'). For Google TTS: full locale codes ('en-US', 'es-ES', 'cmn-cn')."
        ),
    ] = "en",
    voice: Annotated[
        str,
        Field(
            description="Voice identifier. For ElevenLabs: voice_id (e.g., 'aEO01A4wXwd1O8GPgGlF' for English, 'hEKEQC93QpOYMa6WuwWp' for Spanish). For Google: voice name (e.g., 'cmn-CN-Chirp3-HD-Achernar')"
        ),
    ] = None,
) -> dict:
    """Generate audio from text using specified provider and save it to Anki's media collection, returning filename for use in cards."""

    # First generate the audio
    audio_result = await generate_audio(text, provider, language, voice)

    if not audio_result.get("success"):
        return audio_result

    # Then save it to Anki's media collection
    save_result = await save_media_file(filename, audio_result["audio_base64"])

    if not save_result.get("success"):
        return save_result

    return {
        "success": True,
        "filename": save_result["filename"],
        "text": text,
        "provider": provider,
        "language": language,
        "voice": voice,
        "sound_tag": f"[sound:{save_result['filename']}]",
        "message": f"Audio generated using {provider} and saved as '{save_result['filename']}'. Use [sound:{save_result['filename']}] in your card fields.",
    }


@mcp_server.tool()
async def update_notes_bulk(
    updates: Annotated[
        list,
        Field(
            description="List of update dictionaries, each containing 'note_id', 'fields' dict, and optionally 'tags' list"
        ),
    ],
) -> dict:
    """Update multiple notes in a single batch operation for efficiency. Each update should contain note_id and fields to update."""
    if not updates:
        return {"error": "No updates provided", "success": False}

    successful_updates = []
    failed_updates = []

    for i, update_data in enumerate(updates):
        if not isinstance(update_data, dict):
            failed_updates.append(
                {
                    "index": i,
                    "error": "Update data is not a dictionary",
                    "data": update_data,
                }
            )
            continue

        if "note_id" not in update_data or "fields" not in update_data:
            failed_updates.append(
                {
                    "index": i,
                    "error": "Missing required 'note_id' or 'fields'",
                    "data": update_data,
                }
            )
            continue

        # Use the existing update_note function for each update
        try:
            result = await update_note(
                note_id=update_data["note_id"],
                fields=update_data["fields"],
                tags=update_data.get("tags"),
            )

            if result.get("success"):
                successful_updates.append(
                    {
                        "note_id": update_data["note_id"],
                        "updated_fields": result["updated_fields"],
                    }
                )
            else:
                failed_updates.append(
                    {
                        "index": i,
                        "note_id": update_data["note_id"],
                        "error": result.get("error", "Unknown error"),
                        "data": update_data,
                    }
                )
        except Exception as e:
            failed_updates.append(
                {
                    "index": i,
                    "note_id": update_data.get("note_id", "unknown"),
                    "error": str(e),
                    "data": update_data,
                }
            )

    return {
        "success": True,
        "total_attempted": len(updates),
        "successful_count": len(successful_updates),
        "failed_count": len(failed_updates),
        "successful_updates": successful_updates,
        "failed_updates": failed_updates,
        "message": f"Successfully updated {len(successful_updates)} out of {len(updates)} notes",
    }


@mcp_server.tool()
async def find_similar_notes(
    deck_name: Annotated[str, Field(description="Name of the Anki deck to search in")],
    search_text: Annotated[
        str, Field(description="Text to search for as a substring in any field")
    ],
    case_sensitive: Annotated[
        bool, Field(description="Whether the search should be case sensitive")
    ] = False,
    max_results: Annotated[
        int,
        Field(description="Maximum number of matching notes to return", ge=1, le=100),
    ] = 20,
) -> dict:
    """Find notes that contain the search text as a substring in any field. Simple and reliable text matching."""

    try:
        # Get all notes from the deck first
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "findNotes",
                "version": 6,
                "params": {"query": f'deck:"{deck_name}"'},
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        note_ids = result["result"]
        if not note_ids:
            return {"error": f"No notes found in deck '{deck_name}'", "success": False}

        # Get detailed info for all notes
        response = requests.post(
            ANKI_CONNECT_URL,
            json={"action": "notesInfo", "version": 6, "params": {"notes": note_ids}},
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        notes = result["result"]

        # Prepare search text for comparison
        search_lower = search_text.lower() if not case_sensitive else search_text

        # Find matching notes
        matching_notes = []
        for note in notes:
            # Check each field for the search text
            matches_found = []
            for field_name, field_data in note["fields"].items():
                field_value = field_data["value"].strip()
                if not field_value:
                    continue

                # Compare based on case sensitivity setting
                field_compare = (
                    field_value.lower() if not case_sensitive else field_value
                )

                if search_lower in field_compare:
                    matches_found.append(
                        {"field_name": field_name, "field_value": field_value}
                    )

            # If any field matched, add the note to results
            if matches_found:
                matching_notes.append({"note": note, "matching_fields": matches_found})

        # Limit results
        matching_notes = matching_notes[:max_results]

        if not matching_notes:
            return {
                "success": True,
                "found_count": 0,
                "message": f"No notes found containing '{search_text}' in deck '{deck_name}'",
                "notes": [],
            }

        # Format results
        formatted_notes = []
        for item in matching_notes:
            note = item["note"]
            formatted_note = {
                "note_id": note["noteId"],
                "model_name": note["modelName"],
                "tags": note["tags"],
                "matching_fields": item["matching_fields"],
                "fields": {},
            }

            for field_name, field_data in note["fields"].items():
                formatted_note["fields"][field_name] = field_data["value"]

            formatted_notes.append(formatted_note)

        return {
            "success": True,
            "search_text": search_text,
            "found_count": len(matching_notes),
            "case_sensitive": case_sensitive,
            "deck_name": deck_name,
            "notes": formatted_notes,
        }

    except Exception as e:
        return {"error": f"Failed to find matching notes: {str(e)}", "success": False}


@mcp_server.tool()
async def list_media_files(
    pattern: Annotated[
        str,
        Field(
            description="Optional pattern like '*.mp3' or '*chinese*' to filter files"
        ),
    ] = None,
) -> dict:
    """List all media files in Anki's collection, optionally filtered by pattern."""
    try:
        params = {}
        if pattern:
            params["pattern"] = pattern

        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "getMediaFilesNames",
                "version": 6,
                "params": params,
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        files = result["result"]
        return {
            "success": True,
            "files": sorted(files),  # Sort for consistent output
            "count": len(files),
            "pattern": pattern,
        }

    except Exception as e:
        return {"error": f"Failed to list media files: {str(e)}", "success": False}


@mcp_server.tool()
async def media_file_exists(
    filename: Annotated[
        str, Field(description="Name of the media file to check (e.g., 'audio.mp3')")
    ],
) -> dict:
    """Check if a specific media file exists in Anki's collection."""
    try:
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "retrieveMediaFile",
                "version": 6,
                "params": {"filename": filename},
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        exists = result["result"] is not False

        return {
            "success": True,
            "exists": exists,
            "filename": filename,
        }

    except Exception as e:
        return {
            "error": f"Failed to check media file existence: {str(e)}",
            "success": False,
        }


@mcp_server.tool()
async def retrieve_media_file(
    filename: Annotated[
        str, Field(description="Name of the media file to retrieve (e.g., 'audio.mp3')")
    ],
    return_base64: Annotated[
        bool, Field(description="Whether to return base64 encoded file contents")
    ] = True,
) -> dict:
    """Retrieve a media file from Anki's collection."""
    try:
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "retrieveMediaFile",
                "version": 6,
                "params": {"filename": filename},
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        file_data = result["result"]

        if file_data is False:
            return {
                "success": True,
                "exists": False,
                "filename": filename,
                "message": f"Media file '{filename}' not found",
            }

        return_data = {
            "success": True,
            "exists": True,
            "filename": filename,
        }

        if return_base64:
            return_data["base64_data"] = file_data
        else:
            return_data["message"] = (
                f"Media file '{filename}' exists (content not returned)"
            )

        return return_data

    except Exception as e:
        return {"error": f"Failed to retrieve media file: {str(e)}", "success": False}


@mcp_server.tool()
async def delete_media_file(
    filename: Annotated[
        str, Field(description="Name of the media file to delete (e.g., 'audio.mp3')")
    ],
    confirm: Annotated[
        bool, Field(description="Safety flag - must be True to proceed with deletion")
    ] = False,
) -> dict:
    """Delete a media file from Anki's collection. Requires confirm=True for safety."""
    if not confirm:
        return {
            "error": "Deletion requires confirm=True for safety",
            "success": False,
            "filename": filename,
        }

    try:
        exists_result = await media_file_exists(filename)
        if not exists_result.get("success"):
            return exists_result

        if not exists_result.get("exists"):
            return {
                "success": True,
                "deleted": False,
                "filename": filename,
                "message": f"Media file '{filename}' does not exist",
            }

        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "deleteMediaFile",
                "version": 6,
                "params": {"filename": filename},
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        return {
            "success": True,
            "deleted": True,
            "filename": filename,
            "message": f"Media file '{filename}' deleted successfully",
        }

    except Exception as e:
        return {"error": f"Failed to delete media file: {str(e)}", "success": False}


@mcp_server.tool()
async def get_media_directory() -> dict:
    """Get the full path to Anki's media directory."""
    try:
        response = requests.post(
            ANKI_CONNECT_URL,
            json={
                "action": "getMediaDirPath",
                "version": 6,
            },
        )

        if response.status_code != 200:
            return {
                "error": f"Failed to connect to Anki: {response.status_code}",
                "success": False,
            }

        result = response.json()
        if result.get("error"):
            return {"error": result["error"], "success": False}

        path = result["result"]
        return {
            "success": True,
            "path": path,
            "message": f"Media directory: {path}",
        }

    except Exception as e:
        return {
            "error": f"Failed to get media directory path: {str(e)}",
            "success": False,
        }


async def find_missing_media_references(
    note_fields: list[dict],
) -> dict[int, list[str]]:
    """
    Find notes with missing media references. Unified function for single or bulk validation.

    Args:
        note_fields: List of field dictionaries (single note = list with 1 item)

    Returns:
        Dictionary mapping note indices to their missing media files.
        Empty dict {} if no issues found.

        Examples:
        {} - No missing media
        {0: ["missing1.mp3"]} - Note 0 has 1 missing file
        {0: ["file1.mp3"], 3: ["file2.mp3", "file3.mp3"]} - Multiple notes with issues
    """
    try:
        all_media_references = {}  # note_index -> [filenames]
        unique_filenames = set()

        for note_index, note_field_dict in enumerate(note_fields):
            media_files = []
            for field_name, field_value in note_field_dict.items():
                # Extract [sound:filename.ext] patterns using regex
                sound_pattern = r"\[sound:(.*?)\]"
                matches = re.findall(sound_pattern, field_value)
                media_files.extend(matches)

            if media_files:
                all_media_references[note_index] = media_files
                unique_filenames.update(media_files)

        if not unique_filenames:
            return {}

        missing_files = set()
        for filename in unique_filenames:
            exists_result = await media_file_exists(filename)
            if exists_result.get("success") and not exists_result.get("exists"):
                missing_files.add(filename)

        notes_with_missing_media = {}
        for note_index, referenced_files in all_media_references.items():
            note_missing_files = [f for f in referenced_files if f in missing_files]
            if note_missing_files:
                notes_with_missing_media[note_index] = note_missing_files

        return notes_with_missing_media

    except Exception as e:
        # In case of error, log and return empty dict to avoid breaking note creation
        print(f"Error in find_missing_media_references: {e}")
        return {}


@mcp_server.tool()
async def validate_deck_media(
    deck_name: Annotated[str, Field(description="Name of the Anki deck to validate")],
    delete_missing_refs: Annotated[
        bool,
        Field(
            description="Automatically remove broken [sound:...] references from cards"
        ),
    ] = False,
) -> dict:
    """
    Validate all media references in an existing deck.
    Useful for cleanup operations and post-import validation.

    Returns detailed report of broken references and optionally fixes them.
    """
    try:
        result = await _fetch_deck_notes(deck_name)

        if result.get("error"):
            return {"error": result["error"], "success": False}

        data = result["result"]
        notes = data["notes"]

        if not notes:
            return {
                "success": True,
                "total_notes": 0,
                "notes_with_missing_media": 0,
                "missing_files": [],
                "broken_notes": {},
                "message": f"No notes found in deck '{deck_name}'",
            }

        all_fields = []
        note_id_to_index = {}

        for i, note in enumerate(notes):
            fields_dict = {
                field_name: field_data["value"]
                for field_name, field_data in note["fields"].items()
            }
            all_fields.append(fields_dict)
            note_id_to_index[note["noteId"]] = i

        missing_media = await find_missing_media_references(all_fields)

        broken_notes = {}
        all_missing_files = set()

        for note_index, missing_files in missing_media.items():
            note = notes[note_index]
            note_id = note["noteId"]
            broken_notes[note_id] = missing_files
            all_missing_files.update(missing_files)

        deleted_refs_count = 0
        if delete_missing_refs and broken_notes:
            for note_id, missing_files in broken_notes.items():
                # Get the note's current fields
                note = next(n for n in notes if n["noteId"] == note_id)
                updated_fields = {}
                fields_changed = False

                for field_name, field_data in note["fields"].items():
                    field_value = field_data["value"]
                    original_value = field_value

                    # Remove all [sound:missing_file.ext] references
                    for missing_file in missing_files:
                        pattern = rf"\[sound:{re.escape(missing_file)}\]"
                        field_value = re.sub(pattern, "", field_value)

                    # Clean up whitespace
                    field_value = re.sub(r"\s+", " ", field_value).strip()

                    if field_value != original_value:
                        updated_fields[field_name] = field_value
                        fields_changed = True

                if fields_changed:
                    update_result = await update_note(
                        note_id=note_id,
                        fields=updated_fields,
                        validate_media=False,  # We're fixing, so don't validate
                    )
                    if update_result.get("success"):
                        deleted_refs_count += 1

        response_data = {
            "success": True,
            "total_notes": len(notes),
            "notes_with_missing_media": len(broken_notes),
            "unique_missing_files": len(all_missing_files),
            "missing_files": sorted(list(all_missing_files)),
            "broken_notes": broken_notes,
        }

        # Build descriptive message
        if not broken_notes:
            response_data["message"] = (
                f"All {len(notes)} notes in deck '{deck_name}' have valid media references"
            )
        else:
            message_parts = [
                f"Found {len(broken_notes)} notes with missing media out of {len(notes)} total notes ({len(broken_notes) / len(notes) * 100:.1f}%) in deck '{deck_name}'",
                f"{len(all_missing_files)} unique missing files",
            ]
            if delete_missing_refs:
                if deleted_refs_count > 0:
                    message_parts.append(
                        f"Removed broken references from {deleted_refs_count} notes"
                    )
                else:
                    message_parts.append(
                        "No broken references could be automatically removed"
                    )

            response_data["message"] = ". ".join(message_parts)

            if delete_missing_refs:
                response_data["deleted_refs_count"] = deleted_refs_count

        return response_data

    except Exception as e:
        return {"error": f"Failed to validate deck media: {str(e)}", "success": False}


@mcp_server.tool()
async def get_notes_by_ids(
    note_ids: Annotated[list[int], Field(description="List of note IDs to retrieve")],
    fields_only: Annotated[
        bool, Field(description="Return only field data, not full note metadata")
    ] = False,
) -> dict:
    """
    Get specific notes by their IDs using AnkiConnect's batch API.

    Returns note data for the requested IDs. Keep batches reasonable to avoid
    token limits.

    Context: Even the simplest cards with minimal text use 150+ tokens (full)
    or 60+ tokens (fields_only). Cards with longer content use significantly more.
    """
    try:
        if not note_ids:
            return {"error": "No note IDs provided", "success": False}

        # Use AnkiConnect's batch notesInfo API
        result = await _anki_request("notesInfo", {"notes": note_ids})

        if result.get("error"):
            return {"error": result["error"], "success": False}

        notes = result["result"]

        if fields_only:
            simplified_notes = []
            for note in notes:
                simplified_notes.append(
                    {
                        "noteId": note["noteId"],
                        "fields": {
                            field_name: field_data["value"]
                            for field_name, field_data in note["fields"].items()
                        },
                    }
                )
            notes = simplified_notes

        return {
            "success": True,
            "notes": notes,
            "notes_count": len(notes),
            "requested_count": len(note_ids),
        }

    except Exception as e:
        return {"error": f"Failed to get notes by IDs: {str(e)}", "success": False}


@mcp_server.tool()
async def extract_content_for_generation(
    deck_name: Annotated[
        str, Field(description="Name of the Anki deck to extract content from")
    ],
    extract_from: Annotated[
        str, Field(description="Field name to extract content from (e.g., 'Front')")
    ] = "Front",
    strip_formatting: Annotated[
        bool, Field(description="Remove HTML tags from content (includes images)")
    ] = True,
    strip_audio_refs: Annotated[
        bool, Field(description="Remove [sound:...] references from content")
    ] = True,
    max_results: Annotated[
        int, Field(description="Maximum number of notes to process")
    ] = 50,
    offset: Annotated[
        int, Field(description="Starting index for pagination (0-based)")
    ] = 0,
) -> dict:
    """
    Extract clean content from cards for generation purposes (audio, images, etc).

    Returns text content with optional stripping of HTML and audio references.
    Maps content back to note IDs for later updates. Supports pagination via offset.

    Context: HTML stripping removes images (<img> tags). Audio stripping removes [sound:...]
    references. TODO: Consider moving image handling to a separate strip_image_refs parameter.
    """
    try:
        find_result = await _anki_request("findNotes", {"query": f'deck:"{deck_name}"'})

        if find_result.get("error"):
            return {"error": find_result["error"], "success": False}

        all_note_ids = find_result["result"]

        start_idx = offset
        end_idx = offset + max_results
        paginated_note_ids = all_note_ids[start_idx:end_idx]

        if not paginated_note_ids:
            if not all_note_ids:
                message = f"No notes found in deck '{deck_name}'"
            else:
                message = f"No notes at offset {offset} in deck '{deck_name}' (total: {len(all_note_ids)})"

            return {
                "success": True,
                "extracted_content": [],
                "field_name": extract_from,
                "message": message,
                "total_notes": len(all_note_ids),
            }

        notes_result = await get_notes_by_ids(paginated_note_ids, fields_only=True)

        if not notes_result.get("success"):
            return {"error": notes_result.get("error"), "success": False}

        notes = notes_result["notes"]
        extracted_content = []

        for note in notes:
            # Check if the requested field exists
            if extract_from not in note["fields"]:
                continue

            original_content = note["fields"][extract_from]
            clean_content = original_content

            if strip_audio_refs:
                import re

                clean_content = re.sub(r"\[sound:[^\]]+\]", "", clean_content)

            if strip_formatting:
                import re

                clean_content = re.sub(r"<br\s*/?>", " ", clean_content)
                clean_content = re.sub(r"<[^>]+>", "", clean_content)

            # Clean up extra whitespace
            clean_content = " ".join(clean_content.split())

            # Only include if there's actual content
            if clean_content.strip():
                extracted_content.append(
                    {"note_id": note["noteId"], "clean_content": clean_content}
                )

        return {
            "success": True,
            "field_name": extract_from,
            "extracted_content": extracted_content,
            "content_count": len(extracted_content),
            "processed_count": len(notes),
            "total_notes": len(all_note_ids),
            "offset": offset,
            "has_more": end_idx < len(all_note_ids),
        }

    except Exception as e:
        return {"error": f"Failed to extract content: {str(e)}", "success": False}
