# app/services/gemini_moderation.py

import json
import logging
import re
import time
from enum import Enum
from io import BytesIO
from typing import List, Dict, Any, Tuple

from PIL import Image
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"


class SafetyLevel(str, Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class ModerationError(Exception):
    """Custom exception for moderation failures."""


def _compress_if_needed(
    image_bytes: bytes,
    max_bytes: int = 4 * 1024 * 1024,  # 4MB
) -> Tuple[bytes, bool]:
    """
	If the image is too large, resize/compress it to reduce the byte size.
	If that fails, return the original image as is.
    """
    if len(image_bytes) <= max_bytes:
        return image_bytes, False

    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        max_dim = 1024
        w, h = img.size
        scale = min(max_dim / float(max(w, h)), 1.0)
        if scale < 1.0:
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size)

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        compressed = buf.getvalue()
        logger.info(
            "Image compressed from %d bytes to %d bytes",
            len(image_bytes),
            len(compressed),
        )
        return compressed, True
    except Exception as e:
        logger.warning("Image compression failed, using original image: %s", e)
        return image_bytes, False


def _call_gemini_with_retry(
    contents: List[Any],
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
):
    """
	Retry wrapper for calling Gemini.
	Handles temporary errors (network issues, 5xx responses, etc.).
    """
    last_exc = None
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "is_flagged": types.Schema(type=types.Type.BOOLEAN),
                "categories": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING),
                ),
                "reason": types.Schema(type=types.Type.STRING),
            },
            required=["is_flagged", "categories", "reason"],
        ),
    )

    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config,  
            )
        except Exception as e:
            last_exc = e
            logger.warning(
                "Gemini moderation call failed (attempt %d/%d): %s",
                attempt,
                max_retries,
                e,
            )
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
            else:
                break

    raise ModerationError(
        f"Gemini moderation failed after {max_retries} attempts: {last_exc}"
    )


def _apply_threshold(
    categories: List[str],
    level: SafetyLevel,
) -> bool:
    """
	Calculate is_safe based on the threshold level.
	Assume categories are in the format like 'nudity:severe', 'violence:mild', etc.
    """
    severity_map = {"none": 0, "mild": 1, "moderate": 2, "severe": 3}

    max_severity = 0
    for cat in categories:
        # "violence:moderate" -> ("violence", "moderate")
        parts = cat.split(":", 1)
        if len(parts) == 2:
            severity_str = parts[1].strip().lower()
        else:
            severity_str = "moderate"  # f the model does not provide detailed information, assume a moderate level.
        sev = severity_map.get(severity_str, 2)
        max_severity = max(max_severity, sev)

    # criteria per level
    if level == SafetyLevel.STRICT:
        # if mild or higher, then UNSAFE
        return max_severity <= 0
    elif level == SafetyLevel.MODERATE:
        # if moderate or higher, then UNSAFE
        return max_severity <= 1
    else:  # LENIENT
        # if severe only UNSAFE
        return max_severity <= 2


def moderate_image(
    image_bytes: bytes,
    mime_type: str,
    level: SafetyLevel = SafetyLevel.MODERATE,
) -> Dict[str, Any]:
    """
    Production-ready image moderation function.
    Supports: JPEG, PNG, WebP, HEIC, HEIF (NOT GIF - Gemini limitation)
    """
    if mime_type not in ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"):
        raise ModerationError(
            f"Unsupported image type: {mime_type}. "
            "Gemini supports: JPEG, PNG, WebP, HEIC, HEIF only."
        )

    original_size = len(image_bytes)
    image_bytes, compressed = _compress_if_needed(image_bytes)

    prompt = (
        "You are an image safety classifier for a social media platform.\n"
        "Analyze the image and decide if it should be allowed for a general-audience website.\n\n"
        "Return a JSON object with the following fields:\n"
        "  - is_flagged (boolean): true if the image is NOT safe for a general audience.\n"
        "  - categories (array of strings): list of applicable categories with severity,\n"
        "    using the format '<category>:<severity>'.\n"
        "    Categories should be chosen from: nudity, sexual_content, violence, graphic_violence,\n"
        "    self_harm, hate_symbol, drugs, other.\n"
        "    Severities must be one of: none, mild, moderate, severe.\n"
        "    Example: [\"nudity:severe\", \"violence:mild\"].\n"
        "  - reason (string): short human-readable explanation.\n\n"
        "The JSON MUST be valid and parsable. Do NOT include any text outside of the JSON.\n"
    )

    contents = [
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        ),
        prompt,
    ]

    response = _call_gemini_with_retry(contents)

    raw_text = (response.text or "").strip()
    logger.debug("Raw moderation response: %s", raw_text)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini moderation JSON: %s", e)
        raise ModerationError("Gemini returned invalid JSON for moderation")

    is_flagged = bool(data.get("is_flagged", False))
    categories = data.get("categories", []) or []
    reason = data.get("reason") or "No reason provided"

    # Recalculate the final is_safe based on the threshold level.
    is_safe_by_threshold = _apply_threshold(categories, level)
    # Use both is_flagged (model judgment) and the threshold to make a conservative determination.
    is_safe = is_safe_by_threshold and not is_flagged

    # test log
    logger.info(
        "Image moderation decision: is_safe=%s, level=%s, flagged=%s, "
        "categories=%s, original_size=%d, compressed=%s",
        is_safe,
        level.value,
        is_flagged,
        categories,
        original_size,
        compressed,
    )

    return {
        "is_safe": is_safe,
        "reason": reason,
        "categories": categories,
        "level": level.value,
    }


def is_image_unsafe(
    image_bytes: bytes,
    mime_type: str,
    level: SafetyLevel = SafetyLevel.MODERATE,
) -> bool:
    """
    Helper retained for compatibility with existing code.
    Internally calls moderate_image and returns only a boolean.
    """
    result = moderate_image(image_bytes=image_bytes, mime_type=mime_type, level=level)
    return not result["is_safe"]
