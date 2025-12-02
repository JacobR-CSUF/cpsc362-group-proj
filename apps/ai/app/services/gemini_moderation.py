import re
from google import genai
from google.genai import types

from app.core.config import settings


client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"


def _normalize_label(text: str) -> str:
    """
    Normalization words (SAFE/UNSAFE) in Gemini response test
    """
    if not text:
        return "UNSAFE"

    text = text.strip().upper()
    m = re.search(r"\b(UNSAFE|SAFE)\b", text)
    if m:
        return m.group(1)
    return "UNSAFE"


def is_image_unsafe(image_bytes: bytes, mime_type: str) -> bool:
    """
    if image is unsafe, return True, or return False 
    """
    contents = [
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        ),
        (
            "You are an image safety classifier for a social media web app.\n"
            "Classify this image as either SAFE or UNSAFE.\n"
            "UNSAFE if it contains any of the following:\n"
            "- nudity or sexually explicit content\n"
            "- graphic violence or gore\n"
            "- self-harm or suicide content\n"
            "- child abuse or exploitation\n"
            "If it's acceptable for a general-audience website, classify as SAFE.\n"
            "Answer with exactly one word: SAFE or UNSAFE."
        ),
    ]

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
    )

    label = _normalize_label(response.text)
    return label == "UNSAFE"
