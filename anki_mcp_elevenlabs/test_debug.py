import asyncio
import sys

sys.path.append(".")

from anki_mcp_elevenlabs.server import list_note_types


async def test_list_note_types():
    print("Testing list_note_types function...")
    print("=" * 50)

    try:
        result = await list_note_types()
        print("SUCCESS:")
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_list_note_types())
