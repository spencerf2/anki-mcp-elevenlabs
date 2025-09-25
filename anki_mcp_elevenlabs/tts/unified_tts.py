from .elevenlabs_tts import generate_elevenlabs_audio
from .google_tts import generate_google_audio


async def generate_tts_audio(
    text: str,
    provider: str = "elevenlabs",
    language: str = None,
    voice: str = None,
    **kwargs,
) -> dict:
    """Unified TTS interface that supports multiple providers."""

    if provider.lower() == "elevenlabs":
        return await generate_elevenlabs_audio(
            text=text,
            voice_id=voice,
            model=kwargs.get("model", None),  # Let ElevenLabs function auto-select
            language=language,
        )

    elif provider.lower() == "google":
        if language is None:
            language = "cmn-cn"
        if voice is None:
            voice = "cmn-CN-Chirp3-HD-Achernar"

        return await generate_google_audio(text=text, language=language, voice=voice)

    else:
        return {
            "error": f"Unsupported TTS provider: {provider}. Supported providers: elevenlabs, google",
            "success": False,
        }
