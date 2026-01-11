# Anki MCP Server with ElevenLabs Support

> **Based on [anki-mcp](https://github.com/amidvidy/anki-mcp) by [Adam Midvidy]**
>
> This version adds ElevenLabs TTS support via Pipecat while maintaining the original Google Cloud TTS functionality.

A FastMCP server for interacting with Anki through the Model Context Protocol (MCP). This server provides comprehensive tools for managing Anki decks, notes, and note types, with advanced features including AI-powered audio generation, bulk operations, and semantic similarity search.

## External APIs Used

This project integrates with several external APIs to provide enhanced functionality:

### Google Cloud Text-to-Speech API

- **Purpose**: High-quality audio generation from text using Google's Chirp voices
- **Use Case**: Generate pronunciation audio files for flashcards
- **Features**: HD quality voices with natural pronunciation, especially excellent for Chinese
- **Setup**: Requires `GOOGLE_CLOUD_API_KEY` environment variable

### AnkiConnect API (Local)

- **Purpose**: Interface with Anki desktop application
- **Use Case**: All Anki operations (create/read/update notes, manage decks, etc.)
- **Features**: Complete Anki functionality via HTTP API
- **Setup**: AnkiConnect add-on must be installed and Anki must be running

## Setup

1. Install dependencies using uv:

   ```bash
   uv sync
   ```

2. Make sure Anki is running with the AnkiConnect add-on installed:
   - In Anki, go to Tools > Add-ons > Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki

3. (Optional) Set up API key for audio generation:

   ```bash
   # For audio generation with Google Cloud TTS
   export GOOGLE_CLOUD_API_KEY='your-google-cloud-api-key-here'
   ```

4. Run the server:

   ```bash
   uv run server.py
   ```

## Claude Desktop Integration

To use this MCP server with Claude Desktop, add the following configuration to your `claude_desktop_config.json` file:

### Configuration Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Example

```json
{
  "mcpServers": {
    "anki-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/anki-mcp/",
        "run",
        "server.py"
      ],
      "env": {
        "GOOGLE_CLOUD_API_KEY": "your-google-cloud-api-key-here"
      }
    }
  }
}
```

### Setup Steps

1. **Ensure dependencies are installed**: Make sure you've run `uv sync` in your anki-mcp directory
2. **Find your config file** at the location above (create it if it doesn't exist)
3. **Update the path**: Replace `/path/to/your/anki-mcp/` with the actual path to your anki-mcp directory
4. **Add your API key**:
   - Replace `your-google-cloud-api-key-here` with your actual Google Cloud API key (for audio generation)
5. **Restart Claude Desktop** for the changes to take effect

### Important Notes

- Make sure **Anki is running** with the AnkiConnect add-on before using the tools
- The `uv` command will automatically handle the Python environment and dependencies
- Make sure `uv` is installed on your system (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Alternative: Using Environment Variables

If you prefer to keep your API key in your shell environment, you can omit the `env` section:

```json
{
  "mcpServers": {
    "anki-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/anki-mcp/",
        "run",
        "server.py"
      ]
    }
  }
}
```

Then set the environment variable in your shell:

```bash
export GOOGLE_CLOUD_API_KEY='your-google-cloud-api-key-here'
```

### Verification

Once configured, restart Claude Desktop and you should see the Anki MCP tools available in your conversations. You can verify by asking Claude to list your Anki decks or try any of the available tools.

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

### `update_note`

Updates specific fields of an existing note while preserving other fields.

**Parameters**:

- `note_id` (int): ID of the note to update
- `fields` (dict): Dictionary mapping field names to new values (e.g., `{'Audio': '[sound:pronunciation.mp3]'}`)
- `tags` (list, optional): Optional list of tags to replace existing tags

**Returns**: JSON object with success status and updated field information

**Use Case**: Perfect for adding audio files to existing cards or updating specific content

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

### `generate_audio`

Generates high-quality audio files from text using Google Cloud Text-to-Speech API with Chirp voices.

**Parameters**:

- `text` (str): Text to convert to speech
- `language` (str, optional): Language code (default: "cmn-cn" for Chinese)
- `voice` (str, optional): Voice name (default: "cmn-CN-Chirp3-HD-Achernar" for Chinese HD voice)

**Returns**: JSON object with base64-encoded MP3 audio data and metadata

**Setup**: Requires `GOOGLE_CLOUD_API_KEY` environment variable

**Features**: HD quality voices with natural pronunciation, especially excellent for Chinese language learning

### `save_media_file`

Saves media data as a file in Anki's media collection for use in cards.

**Parameters**:

- `filename` (str): Name of the file to save (e.g., 'audio.mp3', 'image.jpg')
- `media_data` (str): Base64 encoded file data OR a local file path (auto-detected)

**Returns**: JSON object with saved filename and success status

**Use Case**: Save generated audio, images, or other media files for use in Anki cards. Accepts either base64 data or a file path for convenience.

### `generate_and_save_audio`

Generates audio from text and saves it directly to Anki's media collection in one operation.

**Parameters**:

- `text` (str): Text to convert to speech and save
- `filename` (str): Name for the audio file (e.g., 'pronunciation.mp3')
- `language` (str, optional): Language code (default: "cmn-cn" for Chinese)
- `voice` (str, optional): Voice name (default: "cmn-CN-Chirp3-HD-Achernar")

**Returns**: JSON object with filename and sound tag for use in card fields

**Setup**: Requires `GOOGLE_CLOUD_API_KEY` environment variable

**Use Case**: One-step audio generation and saving, returns `[sound:filename.mp3]` tag ready for card fields

### `create_notes_bulk`

Creates multiple notes in a single batch operation for maximum efficiency. Handles duplicates gracefully by reporting which notes are duplicates while still creating non-duplicate notes.

**Parameters**:

- `deck_name` (str): Name of the Anki deck to add notes to
- `notes_list` (list): List of note dictionaries, each containing 'model_name', 'fields', and optionally 'tags'

**Returns**: JSON object with success/failed counts, successful notes array, and failed notes array with specific error details

**Features**:

- Uses canAddNotesWithErrorDetail to pre-check which notes can be added
- Only attempts to add valid notes, ensuring no batch failures
- Provides detailed error reporting for each failed note (duplicates, validation errors, etc.)
- Returns note IDs for successfully created notes for further processing

### `update_notes_bulk`

Updates multiple notes in a single batch operation for maximum efficiency.

**Parameters**:

- `updates` (list): List of update dictionaries, each containing 'note_id', 'fields' dict, and optionally 'tags' list

**Returns**: JSON object with success/failure counts and detailed update results

**Use Case**: Perfect for batch updates like adding audio files to multiple cards at once

### `find_similar_notes`

Finds notes that contain the search text as a substring in any field. Simple and reliable text matching.

**Parameters**:

- `deck_name` (str): Name of the Anki deck to search in
- `search_text` (str): Text to search for as a substring in any field
- `case_sensitive` (bool, optional): Whether the search should be case sensitive (default: false)
- `max_results` (int, optional): Maximum number of matching notes to return (default: 20)

**Returns**: JSON object with matching notes and details about which fields contained the search text

**Features**:

- Fast substring matching across all note fields
- Case-sensitive or case-insensitive search options
- Shows exactly which fields matched the search criteria
- No external API dependencies required

## Technical Details

- **Framework**: FastMCP (built on FastAPI)
- **Server Name**: "anki-mcp"
- **AnkiConnect URL**: <http://localhost:8765>
- **Dependencies**: fastapi, fastmcp, requests, uvicorn
- **External APIs**:
  - Google Cloud Text-to-Speech API (for audio generation)
- **Audio Format**: MP3 with base64 encoding

## Features

- **HD Audio Generation**: Premium quality TTS using Google Cloud Chirp voices, optimized for Chinese pronunciation
- **Note Updates**: Update existing notes with new content like audio files while preserving other fields
- **Media Management**: Direct integration with Anki's media collection for seamless file handling
- **Bulk Operations**: Efficient batch note creation and updates for large datasets
- **Fast Text Search**: Simple substring matching for finding notes containing specific text
- **Comprehensive Error Handling**: Robust error handling for all API failures and edge cases
- **Smart Data Formatting**: Content truncation and formatting for optimal readability
- **Random Sampling**: Efficient sampling for large datasets without memory issues
- **Custom Templates**: Full support for custom card templates and CSS styling
- **Type Safety**: Complete parameter validation using Pydantic
- **Secure API Key Handling**: Environment variable-based API key management
- **Robust Error Handling**: Pre-validation of notes with detailed error reporting for duplicates and other issues
- **Cross-Language Support**: Optimized for Chinese language learning but supports multiple languages

