import os

import requests


async def generate_google_audio(
    text: str,
    language: str = "cmn-cn",
    voice: str = "cmn-CN-Chirp3-HD-Achernar",
) -> dict:
    """Generate audio file from text using Google Cloud Chirp TTS API and return base64 encoded audio data."""

    # Get Google Cloud API key from environment variable
    api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
    if not api_key:
        return {
            "error": "Google Cloud API key not found. Please set GOOGLE_CLOUD_API_KEY environment variable.",
            "success": False,
            "setup_instructions": "Run: export GOOGLE_CLOUD_API_KEY='your-api-key-here'",
        }

    try:
        # Google Cloud TTS API call with API key as query parameter
        data = {
            "input": {"text": text},
            "voice": {"languageCode": language, "name": voice},
            "audioConfig": {"audioEncoding": "MP3"},
        }

        response = requests.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=data,
        )

        if response.status_code != 200:
            return {
                "error": f"Google Cloud TTS API error: {response.status_code} - {response.text}",
                "success": False,
            }

        result = response.json()
        audio_base64 = result["audioContent"]

        return {
            "success": True,
            "audio_base64": audio_base64,
            "format": "mp3",
            "language": language,
            "voice": voice,
            "text": text,
            "model": "chirp",
        }

    except Exception as e:
        return {"error": f"Failed to generate audio: {str(e)}", "success": False}
