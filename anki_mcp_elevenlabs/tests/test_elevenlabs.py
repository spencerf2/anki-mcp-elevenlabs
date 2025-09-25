import asyncio
import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from anki_mcp_elevenlabs.tts import generate_elevenlabs_audio, generate_tts_audio


@pytest.mark.asyncio
async def test_elevenlabs():
    """Test ElevenLabs audio generation."""

    print("🧪 Testing ElevenLabs TTS via Pipecat...")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set!")
        print("Please run: export ELEVENLABS_API_KEY='your-key-here'")
        return False

    print(f"✅ API key found: {api_key[:10]}...")

    test_text = "Hello, this is a test of ElevenLabs text-to-speech integration."
    print(f"🎯 Testing with text: '{test_text}'")

    try:
        print("🔄 Generating audio...")
        result = await generate_elevenlabs_audio(
            text=test_text,
            voice_id=None,  # Use default voice
            model="eleven_monolingual_v1",
        )

        if result.get("success"):
            print("✅ Audio generation successful!")
            print(f"   Format: {result.get('format')}")
            print(f"   Voice ID: {result.get('voice_id')}")
            print(f"   Model: {result.get('model')}")
            print(
                f"   Audio data length: {len(result.get('audio_base64', ''))} characters"
            )

            # Save to file for testing
            audio_data = result.get("audio_base64", "")
            if audio_data:
                import base64

                audio_bytes = base64.b64decode(audio_data)

                output_file = "test_output.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)

                print(f"💾 Audio saved to: {output_file}")
                print(f"   File size: {len(audio_bytes)} bytes")
                print("   You can play this file to verify the audio!")

            return True
        else:
            print(f"❌ Audio generation failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"💥 Exception during audio generation: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_tts_unified():
    """Test the unified TTS interface."""

    print("\n🧪 Testing unified TTS interface...")

    try:
        result = await generate_tts_audio(
            text="Testing unified interface", provider="elevenlabs"
        )

        if result.get("success"):
            print("✅ Unified TTS interface works!")
            return True
        else:
            print(f"❌ Unified TTS failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"💥 Exception in unified TTS: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting ElevenLabs TTS tests...\n")

    # Test 1: Direct ElevenLabs function
    test1_passed = await test_elevenlabs()

    # Test 2: Unified interface
    test2_passed = await test_tts_unified()

    print(f"\n📊 Test Results:")
    print(f"   Direct ElevenLabs: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Unified Interface: {'✅ PASS' if test2_passed else '❌ FAIL'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! ElevenLabs integration is working.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
