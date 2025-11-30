# apps/ai/app/core/config.py
from pydantic_settings import BaseSettings

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
    SHIELDGEMMA_DEVICE: str = "cpu"  # cpu or cuda

    # ============================================
    # Image Moderation Settings
    # ============================================
    IMAGE_MODERATION_THRESHOLD: str = "strict"  # strict, moderate, lenient

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow lowercase env vars
        extra = "ignore"  # Ignore extra fields (optional safety net)

settings = Settings()
