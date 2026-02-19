from langdetect import detect, LangDetectException


def detect_language(text: str) -> str | None:
    """
    Detects the language of the input text.
    Returns ISO 639-1 code (e.g. 'en', 'de', 'fr') or None if detection fails.
    """
    try:
        if not text or len(text.strip()) < 5:
            return None
        return detect(text)
    except LangDetectException:
        return None
