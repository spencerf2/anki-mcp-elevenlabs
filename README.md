# Anki MCP Server

A FastMCP server for interacting with Anki through the Model Context Protocol (MCP). This server provides comprehensive tools for managing Anki decks, notes, and note types, with advanced features including AI-powered audio generation, bulk operations, and semantic similarity search.

## External APIs Used

This project integrates with several external APIs to provide enhanced functionality:

### Google Cloud Text-to-Speech API
- **Purpose**: High-quality audio generation from text using Google's Chirp voices
- **Use Case**: Generate pronunciation audio files for flashcards
- **Features**: HD quality voices with natural pronunciation, especially excellent for Chinese
- **Setup**: Requires `GOOGLE_CLOUD_API_KEY` environment variable

### OpenAI Embeddings API
- **Purpose**: Generate vector embeddings for semantic similarity search
- **Use Case**: Find similar notes based on content meaning rather than exact text matches
- **Features**: Works exceptionally well with Chinese text and cross-language similarity
- **Setup**: Requires `OPENAI_API_KEY` environment variable

### AnkiConnect API (Local)
- **Purpose**: Interface with Anki desktop application
- **Use Case**: All Anki operations (create/read/update notes, manage decks, etc.)
- **Features**: Complete Anki functionality via HTTP API
- **Setup**: AnkiConnect add-on must be installed and Anki must be running

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Anki is running with the AnkiConnect add-on installed:
   - In Anki, go to Tools > Add-ons > Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki

3. (Optional) Set up API keys for enhanced features:
   ```bash
   # For audio generation with Google Cloud TTS
   export GOOGLE_CLOUD_API_KEY='your-google-cloud-api-key-here'
   
   # For similarity search with OpenAI embeddings
   export OPENAI_API_KEY='your-openai-api-key-here'
   ```

4. Run the server:
   ```bash
   python server.py
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
      "command": "python",
      "args": ["/path/to/your/anki-mcp/server.py"],
      "env": {
        "GOOGLE_CLOUD_API_KEY": "your-google-cloud-api-key-here",
        "OPENAI_API_KEY": "your-openai-api-key-here"
      }
    }
  }
}
```

### Setup Steps
1. **Ensure dependencies are installed**: Make sure you've run `pip install -r requirements.txt` in your anki-mcp directory
2. **Find your config file** at the location above (create it if it doesn't exist)
3. **Update the path**: Replace `/path/to/your/anki-mcp/server.py` with the actual path to your server.py file
4. **Add your API keys**: 
   - Replace `your-google-cloud-api-key-here` with your actual Google Cloud API key (for audio generation)
   - Replace `your-openai-api-key-here` with your actual OpenAI API key (for similarity search)
5. **Restart Claude Desktop** for the changes to take effect

### Important Notes
- Make sure **Anki is running** with the AnkiConnect add-on before using the tools
- The `python` command should point to the Python environment where you installed the dependencies
- If using a virtual environment, you may need to use the full path to the Python executable (e.g., `/path/to/venv/bin/python`)

### Alternative: Using Environment Variables
If you prefer to keep your API key in your shell environment, you can omit the `env` section:

```json
{
  "mcpServers": {
    "anki-mcp": {
      "command": "python",
      "args": ["/path/to/your/anki-mcp/server.py"]
    }
  }
}
```

Then set the environment variables in your shell:
```bash
export GOOGLE_CLOUD_API_KEY='your-google-cloud-api-key-here'
export OPENAI_API_KEY='your-openai-api-key-here'
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
Saves base64 encoded media data as a file in Anki's media collection for use in cards.

**Parameters**:
- `filename` (str): Name of the file to save (e.g., 'audio.mp3', 'image.jpg')
- `base64_data` (str): Base64 encoded file data
- `media_type` (str, optional): Type of media file (default: "audio")

**Returns**: JSON object with saved filename and success status

**Use Case**: Save generated audio or other media files for use in Anki cards

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
Creates multiple notes in a single batch operation for maximum efficiency.

**Parameters**:
- `deck_name` (str): Name of the Anki deck to add notes to
- `notes_list` (list): List of note dictionaries, each containing 'model_name', 'fields', and optionally 'tags'

**Returns**: JSON object with success/failure counts and note IDs

### `find_similar_notes`
Finds notes with similar semantic content using vector embeddings, optimized for Chinese text.

**Parameters**:
- `deck_name` (str): Name of the Anki deck to search in
- `search_text` (str): Text to search for (e.g., hanzi, word, or phrase)
- `similarity_threshold` (float, optional): Minimum similarity score 0.0-1.0 (default: 0.7)
- `max_results` (int, optional): Maximum number of results to return (default: 10)

**Returns**: JSON object with similar notes ranked by similarity score

**Setup**: Requires `OPENAI_API_KEY` environment variable

## Technical Details

- **Framework**: FastMCP (built on FastAPI)
- **Server Name**: "anki-mcp"
- **AnkiConnect URL**: http://localhost:8765
- **Dependencies**: fastapi, fastmcp, requests, uvicorn, numpy
- **External APIs**: 
  - Google Cloud Text-to-Speech API (for audio generation)
  - OpenAI Embeddings API (for similarity search)
- **Audio Format**: MP3 with base64 encoding
- **Embeddings Model**: text-embedding-3-small (cost-effective and fast)

## Features

- **HD Audio Generation**: Premium quality TTS using Google Cloud Chirp voices, optimized for Chinese pronunciation
- **Note Updates**: Update existing notes with new content like audio files while preserving other fields
- **Media Management**: Direct integration with Anki's media collection for seamless file handling
- **Bulk Operations**: Efficient batch note creation for large datasets
- **Smart Similarity Search**: Vector embeddings for semantic duplicate detection, works excellently with Chinese text
- **Comprehensive Error Handling**: Robust error handling for all API failures and edge cases
- **Smart Data Formatting**: Content truncation and formatting for optimal readability
- **Random Sampling**: Efficient sampling for large datasets without memory issues
- **Custom Templates**: Full support for custom card templates and CSS styling
- **Type Safety**: Complete parameter validation using Pydantic
- **Secure API Key Handling**: Environment variable-based API key management
- **Cross-Language Support**: Optimized for Chinese language learning but supports multiple languages