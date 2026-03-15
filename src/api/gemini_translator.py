"""
gemini_translator.py
Translates English board game descriptions to Japanese using Gemini 2.0 Flash.
Falls back gracefully when the API key is absent or the call fails.
"""

import os
import logging
import functools
from dotenv import load_dotenv

load_dotenv()

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy client – avoids import errors when google-genai is not installed
# ---------------------------------------------------------------------------
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        return _client
    except Exception as e:
        _logger.warning(f"Failed to initialize Gemini client: {e}")
        return None


# ---------------------------------------------------------------------------
# Simple in-process cache (avoids re-translating identical texts in one run)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=256)
def _cached_translate(text: str) -> str | None:
    """Translate *text* and cache the result by content hash."""
    client = _get_client()
    if client is None:
        return None

    prompt = (
        "次の英語のボードゲーム説明文を自然な日本語に翻訳してください。\n"
        "翻訳文のみを出力し、前置きや補足は一切付けないでください。\n\n"
        f"{text}"
    )

    try:
        from google.genai import types
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="text/plain"
            ),
        )
        translated = response.text.strip()
        _logger.info("Gemini translation succeeded (%d chars → %d chars)", len(text), len(translated))
        return translated
    except Exception as e:
        _logger.warning(f"Gemini translation failed: {e}")
        return None


def translate_description(description: str | None) -> str | None:
    """
    Translate an English board game description to Japanese.

    Returns the Japanese translation, or None if translation is unavailable
    (missing API key, network error, etc.).  The original description is
    never overwritten – callers decide what to do with the result.

    Parameters
    ----------
    description : str | None
        English description text retrieved from BGG.

    Returns
    -------
    str | None
        Japanese translation, or None on failure / no-op.
    """
    if not description or not description.strip():
        return None

    # Skip translation when the text is already predominantly Japanese
    japanese_chars = sum(
        1 for c in description
        if '\u3040' <= c <= '\u9FFF' or '\uF900' <= c <= '\uFAFF'
    )
    if japanese_chars / max(len(description), 1) > 0.2:
        _logger.debug("Description appears to be already in Japanese – skipping translation.")
        return None

    return _cached_translate(description)
