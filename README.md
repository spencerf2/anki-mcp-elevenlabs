# Anki MCP Server

A FastMCP server for interacting with Anki.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure Anki is running with the AnkiConnect add-on installed
   - In Anki, go to Tools > Add-ons > Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki

3. Run the server:
   ```
   python server.py
   ```

## Available Commands

### `anki.listDecks`

Lists all available Anki decks.

Example:
```
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"id":1,"method":"anki.listDecks","params":{}}'
```

Response:
```json
{
  "id": 1,
  "result": {
    "decks": ["Default", "MyDeck1", "MyDeck2"]
  },
  "error": null
}
```