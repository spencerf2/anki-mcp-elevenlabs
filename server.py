from fastmcp import FastMCP
import requests
import random
from typing import Annotated
from pydantic import Field

mcp_server = FastMCP("anki-mcp")

ANKI_CONNECT_URL = "http://localhost:8765"

@mcp_server.tool()
async def list_decks() -> str:
    """List all available Anki decks."""
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "deckNames",
        "version": 6
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    decks = result["result"]
    return f"Available decks ({len(decks)}):\n" + "\n".join(f"- {deck}" for deck in decks)

@mcp_server.tool()
async def get_deck_notes(
    deck_name: Annotated[str, Field(description="Name of the Anki deck to retrieve notes from")]
) -> str:
    """Get all notes/cards from a specific deck."""
    # First get all note IDs for the deck
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:\"{deck_name}\""
        }
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    note_ids = result["result"]
    if not note_ids:
        return f"No notes found in deck '{deck_name}'"

    # Get note info for all notes
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    notes = result["result"]
    
    # Format the notes for better readability
    output = [f"Notes in deck '{deck_name}' ({len(notes)} total):\n"]
    
    for i, note in enumerate(notes, 1):
        output.append(f"Note {i} (ID: {note['noteId']}):")
        output.append(f"  Model: {note['modelName']}")
        output.append(f"  Tags: {', '.join(note['tags']) if note['tags'] else 'None'}")
        output.append("  Fields:")
        for field_name, field_value in note['fields'].items():
            # Truncate long field values for readability
            value = field_value['value'][:100] + "..." if len(field_value['value']) > 100 else field_value['value']
            output.append(f"    {field_name}: {value}")
        output.append("")
    
    return "\n".join(output)

@mcp_server.tool()
async def get_deck_sample(
    deck_name: Annotated[str, Field(description="Name of the Anki deck to sample notes from")],
    sample_size: Annotated[int, Field(description="Number of notes to randomly sample from the deck", ge=1, le=50)] = 5
) -> str:
    """Get a random sample of notes from a specific deck to understand typical note structure."""
    # First get all note IDs for the deck
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:\"{deck_name}\""
        }
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    note_ids = result["result"]
    if not note_ids:
        return f"No notes found in deck '{deck_name}'"

    # Get a random sample of note IDs
    actual_sample_size = min(sample_size, len(note_ids))
    sampled_note_ids = random.sample(note_ids, actual_sample_size)

    # Get note info for sampled notes
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": sampled_note_ids
        }
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    notes = result["result"]
    
    # Format the notes for better readability
    output = [f"Sample of {len(notes)} notes from deck '{deck_name}' (total: {len(note_ids)}):\n"]
    
    for i, note in enumerate(notes, 1):
        output.append(f"Sample Note {i} (ID: {note['noteId']}):")
        output.append(f"  Model: {note['modelName']}")
        output.append(f"  Tags: {', '.join(note['tags']) if note['tags'] else 'None'}")
        output.append("  Fields:")
        for field_name, field_value in note['fields'].items():
            # Truncate long field values for readability
            value = field_value['value'][:200] + "..." if len(field_value['value']) > 200 else field_value['value']
            output.append(f"    {field_name}: {value}")
        output.append("")
    
    return "\n".join(output)

@mcp_server.tool()
async def get_deck_note_types(
    deck_name: Annotated[str, Field(description="Name of the Anki deck to analyze for note types")]
) -> str:
    """Get the note types (models) and their field definitions used in a specific deck."""
    # First get a sample of notes to find the note types used in this deck
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:\"{deck_name}\""
        }
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    note_ids = result["result"]
    if not note_ids:
        return f"No notes found in deck '{deck_name}'"

    # Get info for a sample of notes to find unique model names
    sample_size = min(50, len(note_ids))  # Sample up to 50 notes to find model types
    sampled_note_ids = random.sample(note_ids, sample_size)
    
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": sampled_note_ids
        }
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    # Find unique model names used in this deck
    model_names = set()
    for note in result["result"]:
        model_names.add(note["modelName"])

    # Get field names for each model
    output = [f"Note types used in deck '{deck_name}':\n"]
    
    for model_name in sorted(model_names):
        response = requests.post(ANKI_CONNECT_URL, json={
            "action": "modelFieldNames",
            "version": 6,
            "params": {
                "modelName": model_name
            }
        })

        if response.status_code == 200:
            result = response.json()
            if not result.get("error"):
                fields = result["result"]
                output.append(f"Model: {model_name}")
                output.append(f"  Fields: {', '.join(fields)}")
                output.append("")

    return "\n".join(output)

@mcp_server.tool()
async def create_note(
    deck_name: Annotated[str, Field(description="Name of the Anki deck to add the note to")],
    model_name: Annotated[str, Field(description="Name of the note type/model to use for this note")],
    fields: Annotated[dict, Field(description="Dictionary mapping field names to their values (e.g., {'Front': 'Question', 'Back': 'Answer'})")],
    tags: Annotated[list, Field(description="Optional list of tags to add to the note")] = None
):
    """Create a new note in the specified deck with the given fields and tags."""
    if tags is None:
        tags = []

    note_data = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": tags
    }

    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "addNote",
        "version": 6,
        "params": {
            "note": note_data
        }
    })

    if response.status_code != 200:
        return {"error": f"Failed to connect to Anki: {response.status_code}"}

    result = response.json()
    if result.get("error"):
        return {"error": result["error"]}

    return {"noteId": result["result"], "success": True}

@mcp_server.tool()
async def create_deck_with_note_type(
    deck_name: Annotated[str, Field(description="Name for the new Anki deck to create")],
    model_name: Annotated[str, Field(description="Name for the note type/model to create or use")],
    fields: Annotated[list, Field(description="List of field names for the note type (e.g., ['Front', 'Back', 'Extra'])")],
    card_templates: Annotated[list, Field(description="Optional list of card template definitions. If not provided, basic front/back templates will be created")] = None
):
    """Create a new deck and optionally a new note type with specified fields and card templates."""
    
    # First create the deck
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck_name
        }
    })

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
                "Back": "{{FrontSide}}<hr id=\"answer\">{{" + fields[1] + "}}" if len(fields) > 1 else "{{" + fields[0] + "}}"
            }
        ]

    # Check if model already exists
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "modelNames",
        "version": 6
    })

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
            "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n"
        }

        response = requests.post(ANKI_CONNECT_URL, json={
            "action": "createModel",
            "version": 6,
            "params": model_data
        })

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
            "fields": fields
        }
    else:
        return {
            "success": True,
            "deck_id": deck_id,
            "deck_name": deck_name,
            "model_created": False,
            "model_name": model_name,
            "message": f"Note type '{model_name}' already exists, deck created with existing note type"
        }

@mcp_server.tool()
async def list_note_types() -> str:
    """List all available note types (models) with their fields and card templates."""
    # Get all model names
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "modelNames",
        "version": 6
    })

    if response.status_code != 200:
        return f"Error: Failed to connect to Anki: {response.status_code}"

    result = response.json()
    if result.get("error"):
        return f"Error: {result['error']}"

    model_names = result["result"]
    output = [f"Available note types ({len(model_names)}):\n"]

    # Get detailed info for each model
    for model_name in sorted(model_names):
        output.append(f"Model: {model_name}")
        
        # Get field names
        response = requests.post(ANKI_CONNECT_URL, json={
            "action": "modelFieldNames",
            "version": 6,
            "params": {
                "modelName": model_name
            }
        })

        if response.status_code == 200:
            result = response.json()
            if not result.get("error"):
                fields = result["result"]
                output.append(f"  Fields: {', '.join(fields)}")

        # Get templates
        response = requests.post(ANKI_CONNECT_URL, json={
            "action": "modelTemplates",
            "version": 6,
            "params": {
                "modelName": model_name
            }
        })

        if response.status_code == 200:
            result = response.json()
            if not result.get("error"):
                templates = result["result"]
                output.append(f"  Templates: {len(templates)} card type(s)")
                for template in templates:
                    template_name = template.get("Name", "Unnamed")
                    output.append(f"    - {template_name}")

        # Get styling (CSS)
        response = requests.post(ANKI_CONNECT_URL, json={
            "action": "modelStyling",
            "version": 6,
            "params": {
                "modelName": model_name
            }
        })

        if response.status_code == 200:
            result = response.json()
            if not result.get("error"):
                css_length = len(result["result"]["css"])
                output.append(f"  CSS: {css_length} characters")
        
        output.append("")

    return "\n".join(output)

if __name__ == "__main__":
    mcp_server.run()
