import asyncio
import base64
import os

import pytest

from anki_mcp_elevenlabs.tts.elevenlabs_tts import generate_elevenlabs_audio
from anki_mcp_elevenlabs.tts.unified_tts import generate_tts_audio


@pytest.mark.asyncio
async def test_elevenlabs_api_key_missing():
    """Test that missing API key is handled gracefully."""
    # Temporarily remove API key
    original_key = os.environ.get("ELEVENLABS_API_KEY")
    if "ELEVENLABS_API_KEY" in os.environ:
        del os.environ["ELEVENLABS_API_KEY"]

    try:
        result = await generate_elevenlabs_audio("test")
        assert not result["success"]
        assert "API key not found" in result["error"]
    finally:
        # Restore API key
        if original_key:
            os.environ["ELEVENLABS_API_KEY"] = original_key


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY"), reason="ELEVENLABS_API_KEY not set"
)
async def test_elevenlabs_audio_generation():
    """Test ElevenLabs audio generation with real API call."""
    result = await generate_elevenlabs_audio(
        text="Hello world",
        voice_id=None,
        model="eleven_monolingual_v1",  # Use default
    )

    assert result["success"] is True
    assert "audio_base64" in result
    assert result["format"] == "wav"
    assert result["provider"] == "elevenlabs"
    assert len(result["audio_base64"]) > 0

    # Verify base64 is valid
    audio_bytes = base64.b64decode(result["audio_base64"])
    assert len(audio_bytes) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY"), reason="ELEVENLABS_API_KEY not set"
)
async def test_unified_tts_elevenlabs():
    """Test unified TTS interface with ElevenLabs provider."""
    result = await generate_tts_audio(
        text="Testing unified interface", provider="elevenlabs"
    )

    assert result["success"] is True
    assert result["provider"] == "elevenlabs"


@pytest.mark.asyncio
async def test_unified_tts_invalid_provider():
    """Test unified TTS interface with invalid provider."""
    result = await generate_tts_audio(text="test", provider="invalid_provider")

    assert result["success"] is False
    assert "Unsupported TTS provider" in result["error"]


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GOOGLE_CLOUD_API_KEY"), reason="GOOGLE_CLOUD_API_KEY not set"
)
async def test_unified_tts_google():
    """Test unified TTS interface with Google provider."""
    result = await generate_tts_audio(
        text="Testing Google TTS",
        provider="google",
        language="en-US",
        voice="en-US-Standard-A",
    )

    assert result["success"] is True
    assert result.get("model") == "chirp"


if __name__ == "__main__":

    async def run_tests():
        print("Running TTS tests...")

        await test_elevenlabs_api_key_missing()
        print("✅ API key handling test passed")

        if os.getenv("ELEVENLABS_API_KEY"):
            await test_elevenlabs_audio_generation()
            print("✅ ElevenLabs audio generation test passed")

            await test_unified_tts_elevenlabs()
            print("✅ Unified TTS ElevenLabs test passed")
        else:
            print("⏭️  Skipping ElevenLabs tests (no API key)")

        await test_unified_tts_invalid_provider()
        print("✅ Invalid provider test passed")

        print("🎉 All tests completed!")

    asyncio.run(run_tests())
