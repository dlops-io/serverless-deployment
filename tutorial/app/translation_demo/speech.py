"""Vertex AI Gemini TTS using ADC, with browser-playable WAV output.

Reference: https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
The REST API keeps this adapter independent of googletrans's older httpx pin.
"""

import base64
import binascii
import io
import os
import re
import wave

import google.auth
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession
import requests

LOCALES = {
    "en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE",
    "el": "el-GR", "hi": "hi-IN", "ja": "ja-JP",
    "zh-cn": "cmn-CN", "zh-tw": "cmn-TW",
}


class SpeechConfigurationError(RuntimeError):
    """The deployment has not been configured for authorized speech calls."""


class SpeechProviderError(RuntimeError):
    """The external provider failed or returned unusable audio."""


def enabled():
    return os.environ.get("ENABLE_SPEECH", "false").lower() in {"1", "true", "yes"}


def pcm_to_wav(pcm: bytes) -> bytes:
    """Vertex TTS returns mono, 24 kHz, 16-bit PCM, without WAV headers."""
    if not pcm or len(pcm) % 2:
        raise SpeechProviderError("The speech provider returned invalid PCM audio.")
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(pcm)
    return output.getvalue()


def decode_response(data: dict) -> bytes:
    parts = []
    for candidate in data.get("candidates", []):
        for part in (candidate.get("content") or {}).get("parts", []):
            inline = part.get("inlineData")
            if not inline:
                continue
            mime = inline.get("mimeType", "").lower()
            if not (mime.startswith("audio/l16") or mime.startswith("audio/pcm")):
                raise SpeechProviderError("The speech provider returned an unexpected audio format.")
            # Do not silently reinterpret a different sample rate as 24 kHz.
            rate = re.search(r"rate\s*=\s*(\d+)", mime)
            if rate and int(rate.group(1)) != 24000:
                raise SpeechProviderError("The speech provider returned an unexpected sample rate.")
            try:
                parts.append(base64.b64decode(inline.get("data", ""), validate=True))
            except (ValueError, binascii.Error, TypeError) as exc:
                raise SpeechProviderError("The speech provider returned malformed audio.") from exc
        if parts:
            return pcm_to_wav(b"".join(parts))
    raise SpeechProviderError("No audio was returned. The provider may have rejected the text.")


def synthesize(text: str, language: str) -> tuple[bytes, str]:
    if not enabled():
        raise SpeechConfigurationError("Speech is disabled. Enable it for part 3 after configuring Vertex AI access.")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter some translated text to speak.")
    if len(text.encode("utf-8")) > 4000:
        raise ValueError("Use at most 4,000 UTF-8 bytes for this short speech demo.")
    if language not in LOCALES:
        raise ValueError("Speech is not configured for this language.")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    model = os.environ.get("VERTEX_TTS_MODEL", "gemini-2.5-flash-tts")
    voice = os.environ.get("VERTEX_TTS_VOICE", "Kore")
    if not project:
        raise SpeechConfigurationError("Set GOOGLE_CLOUD_PROJECT to the project authorized for Vertex AI.")
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", value) for value in (project, location, model, voice)):
        raise SpeechConfigurationError("Invalid project, location, model, or voice configuration.")
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    url = f"https://{host}/v1beta1/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Read the following text aloud, without adding commentary:\n" + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"languageCode": LOCALES[language],
                             "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
            quota_project_id=project,
        )
        with AuthorizedSession(credentials) as session:
            response = session.post(url, json=payload, timeout=(10, 75))
    except GoogleAuthError as exc:
        raise SpeechConfigurationError("Google credentials are unavailable. Configure local ADC or attach an authorized runtime service account.") from exc
    except requests.RequestException as exc:
        raise SpeechProviderError("The speech request failed or timed out. Try a shorter passage.") from exc
    if response.status_code in (401, 403):
        raise SpeechConfigurationError("Vertex AI access denied. Check the caller identity, enabled API, inference permissions, and quota project.")
    if response.status_code == 404:
        raise SpeechConfigurationError("The speech model was not found. Check the selected Vertex AI model and location.")
    if response.status_code == 429:
        raise SpeechProviderError("The speech service quota is temporarily exhausted. Try again later.")
    if not response.ok:
        raise SpeechProviderError(f"Vertex AI rejected the speech request (HTTP {response.status_code}).")
    try:
        audio = decode_response(response.json())
    except (ValueError, TypeError, AttributeError) as exc:
        raise SpeechProviderError("The speech provider returned an invalid response.") from exc
    return audio, "audio/wav"
