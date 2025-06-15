# Anki MCP Server

A FastMCP server for interacting with Anki through the Model Context Protocol (MCP). This server provides tools for managing Anki decks, notes, and note types through the AnkiConnect add-on.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Anki is running with the AnkiConnect add-on installed:
   - In Anki, go to Tools > Add-ons > Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki

3. Run the server:
   ```bash
   python server.py
   ```

## Available Tools

### `list_decks`
Lists all available Anki decks with count.

**Parameters**: None

**Returns**: Formatted string with all deck names and total count

### `get_deck_notes`
Retrieves all notes/cards from a specific deck with detailed information.

**Parameters**:
- `deck_name` (str): Name of the Anki deck to retrieve notes from

**Returns**: Detailed information about all notes including model name, tags, and field values

### `get_deck_sample`
Gets a random sample of notes from a deck to understand typical note structure.

**Parameters**:
- `deck_name` (str): Name of the Anki deck to sample notes from
- `sample_size` (int, optional): Number of notes to sample (1-50, default: 5)

**Returns**: Detailed information about sampled notes

### `get_deck_note_types`
Analyzes a deck to identify all note types (models) and their field definitions.

**Parameters**:
- `deck_name` (str): Name of the Anki deck to analyze

**Returns**: All unique note types used in the deck with their field names

### `create_note`
Creates a new note in the specified deck.

**Parameters**:
- `deck_name` (str): Name of the Anki deck to add the note to
- `model_name` (str): Name of the note type/model to use
- `fields` (dict): Dictionary mapping field names to values (e.g., `{'Front': 'Question', 'Back': 'Answer'}`)
- `tags` (list, optional): Optional list of tags to add to the note

**Returns**: JSON object with noteId and success status or error message

### `create_deck_with_note_type`
Creates a new deck and optionally a new note type with custom fields and templates.

**Parameters**:
- `deck_name` (str): Name for the new Anki deck
- `model_name` (str): Name for the note type/model
- `fields` (list): List of field names (e.g., `['Front', 'Back', 'Extra']`)
- `card_templates` (list, optional): Optional list of card template definitions

**Returns**: JSON object with creation status and details

### `list_note_types`
Lists all available note types (models) with comprehensive information.

**Parameters**: None

**Returns**: Information about all note types including fields, templates, and styling

## Technical Details

- **Framework**: FastMCP (built on FastAPI)
- **Server Name**: "anki-mcp"
- **AnkiConnect URL**: http://localhost:8765
- **Dependencies**: fastapi, fastmcp, requests, uvicorn

## Features

- Comprehensive error handling for AnkiConnect API failures
- Smart data formatting with content truncation for readability
- Random sampling for large datasets
- Support for custom card templates and CSS styling
- Type-safe parameter validation using Pydantic