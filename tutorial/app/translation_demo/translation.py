"""The same external translation provider used by part 1."""

LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "el": "Greek",
    "hi": "Hindi",
    "ja": "Japanese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
}


def validate(text, source, destination):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter some text to translate.")
    if len(text) > 5000:
        raise ValueError("Use at most 5,000 characters for this demo.")
    if not isinstance(source, str) or source not in LANGUAGES:
        raise ValueError("Choose a supported source language.")
    if not isinstance(destination, str) or destination not in LANGUAGES:
        raise ValueError("Choose a supported destination language.")


def translate(text, source, destination):
    validate(text, source, destination)
    # Import here so offline UI and contract checks do not load the provider.
    import httpx
    from googletrans import Translator

    translator = Translator(timeout=httpx.Timeout(20.0))
    return translator.translate(text, src=source, dest=destination).text
