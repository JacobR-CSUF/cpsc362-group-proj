# apps/api/app/services/ai_client.py
"""
AI Service Client
Helper for main API to call AI pipeline endpoints.
"""

import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai:8002")


class AIServiceClient:
    """Client for calling AI service endpoints"""

    @staticmethod
    async def process_video(
        file_url: str,
        language: Optional[str] = None,
        summary_style: str = "brief",
        skip_moderation: bool = False,
        timeout: float = 300.0  # 5 minutes for long videos
    ) -> Dict[str, Any]:
        """
        Process video through AI pipeline.

        Returns:
            Pipeline response with transcription, moderation, and summary
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    f"{AI_SERVICE_URL}/process-video",
                    json={
                        "file_url": file_url,
                        "language": language,
                        "summary_style": summary_style,
                        "skip_moderation": skip_moderation,
                        "skip_summary": False
                    }
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error(f"AI service video processing failed: {e}")
                raise

    @staticmethod
    async def process_image(
        file_url: str,
        safety_level: str = "moderate",
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Process image through AI moderation pipeline.

        Returns:
            Pipeline response with moderation result
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    f"{AI_SERVICE_URL}/process-image",
                    json={
                        "file_url": file_url,
                        "safety_level": safety_level
                    }
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error(f"AI service image processing failed: {e}")
                raise

    @staticmethod
    async def is_image_safe(file_url: str, safety_level: str = "moderate") -> bool:
        """
        Quick check if image is safe.

        Returns:
            True if image passes moderation
        """
        try:
            result = await AIServiceClient.process_image(file_url, safety_level)
            return result.get("is_safe", False)
        except Exception as e:
            logger.error(f"Image safety check failed: {e}")
            return False  # Fail safe

    @staticmethod
    async def is_video_safe(file_url: str) -> bool:
        """
        Quick check if video content is safe.

        Returns:
            True if video passes text moderation
        """
        try:
            result = await AIServiceClient.process_video(
                file_url=file_url,
                skip_summary=True  # Don't need summary for safety check
            )
            return result.get("is_safe", False)
        except Exception as e:
            logger.error(f"Video safety check failed: {e}")
            return False  # Fail safe


# Convenience functions
async def check_media_safety(file_url: str, media_type: str) -> Dict[str, Any]:
    """
    Check if media is safe based on type.

    Args:
        file_url: Presigned URL to media
        media_type: 'image' or 'video'

    Returns:
        Dict with is_safe, reason, and full result
    """
    if media_type == "image":
        result = await AIServiceClient.process_image(file_url)
        return {
            "is_safe": result.get("is_safe", False),
            "reason": result.get("moderation", {}).get("reason", ""),
            "result": result
        }
    elif media_type == "video":
        result = await AIServiceClient.process_video(file_url, skip_summary=True)
        text_mod = result.get("text_moderation", {})
        return {
            "is_safe": result.get("is_safe", False),
            "reason": text_mod.get("explanation", ""),
            "result": result
        }
    else:
        return {
            "is_safe": True,
            "reason": "Unknown media type, skipping moderation",
            "result": None
        }
