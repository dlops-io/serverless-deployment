"""Part 3 integration boundary. No synthesized or placeholder audio is returned."""


def synthesize(text: str, language: str) -> tuple[bytes, str]:
    """Eventually return encoded audio bytes and their matching MIME type.

    TODO: select a supported Vertex AI TTS model and region, use ADC from the
    runtime service account, and verify encoding and browser playback. The UI
    must use the returned content type rather than assuming PCM is a WAV file.
    """
    raise NotImplementedError("Vertex AI speech synthesis is not implemented yet.")
