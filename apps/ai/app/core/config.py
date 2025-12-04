# apps/ai/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Configuration settings for AI service"""

    # ============================================
    # Google Gemini Cloud API
    # ============================================
    GEMINI_API_KEY: str = ""

    # ============================================
    # Whisper Settings (Local Transcription)
    # ============================================
    WHISPER_MODEL_SIZE: str = "base"  # tiny, base, small, medium, large

    # ============================================
    # ShieldGemma Settings (Local Text Moderation)
    # ============================================
    SHIELDGEMMA_MODEL_NAME: str = "google/shieldgemma-2b"
    SHIELDGEMMA_DEVICE: Literal["cpu", "cuda"] = "cpu"
    SHIELDGEMMA_LOAD_IN_8BIT: bool = True  # Reduce memory usage
    SHIELDGEMMA_MAX_LENGTH: int = 512  # Max input tokens

    # Safety thresholds (0.0 to 1.0, higher = stricter)
    SHIELDGEMMA_THRESHOLD_UNSAFE: float = 0.5  # Score above this = unsafe
    SHIELDGEMMA_THRESHOLD_WARNING: float = 0.3  # Score above this = warning

    # ============================================
    # Image Moderation Settings
    # ============================================
    IMAGE_MODERATION_THRESHOLD: str = "strict"  # strict, moderate, lenient

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow lowercase env vars
        extra = "ignore"  # Ignore extra fields (optional safety net)


settings = Settings()
