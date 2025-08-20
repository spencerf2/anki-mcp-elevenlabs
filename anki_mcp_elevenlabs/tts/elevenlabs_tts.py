import os
import base64
import requests


async def generate_elevenlabs_audio(
    text: str, voice_id: str = None, model: str = "eleven_monolingual_v2"
) -> dict:
    """Generate audio from text using ElevenLabs HTTP API directly and return base64 encoded audio data."""

    # Get ElevenLabs API key from environment variable
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {
            "error": "ElevenLabs API key not found. Please set ELEVENLABS_API_KEY environment variable.",
            "success": False,
            "setup_instructions": "Run: export ELEVENLABS_API_KEY='your-api-key-here'",
        }

    if voice_id is None:
        voice_id = os.getenv(
            "ELEVENLABS_VOICE_ID", "aEO01A4wXwd1O8GPgGlF"
        )  # Default Arabella voice

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }

        data = {
            "text": text,
            "model_id": model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            return {
                "error": f"ElevenLabs API error: {response.status_code} - {response.text}",
                "success": False,
            }

        audio_bytes = response.content

        if not audio_bytes:
            return {
                "error": "No audio data received from ElevenLabs API",
                "success": False,
            }

        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {
            "success": True,
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice_id": voice_id,
            "model": model,
            "text": text,
            "provider": "elevenlabs",
        }

    except Exception as e:
        return {
            "error": f"Failed to generate ElevenLabs audio: {str(e)}",
            "success": False,
        }
