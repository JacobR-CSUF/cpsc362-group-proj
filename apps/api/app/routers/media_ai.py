# apps/api/app/routers/media_ai.py

"""
Media AI helper routes
Expose transcript and summary for a given media (video) item.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ..dependencies import get_current_user
from ..services.supabase_client import SupabaseClient
from ..services.ai_client import AIServiceClient

router = APIRouter(
    prefix="/media-ai",
    tags=["media-ai"],
)


class TranscriptResponse(BaseModel):
    media_id: str = Field(..., description="ID of the media record")
    text: str = Field(..., description="Transcript text stored for this media")


class SummaryResponse(BaseModel):
    media_id: str = Field(..., description="ID of the media record")
    summary: str = Field(..., description="Summary generated from transcript text")
    style: str = Field(..., description="Summary style used (brief/detailed/bullet_points)")
    source: str = Field(..., description="Where the transcript text was loaded from")


def _get_media_or_404(media_id: str) -> Dict[str, Any]:
    """
    Helper to load a single media row from Supabase.
    Raises HTTPException(404) if not found.
    """
    result = SupabaseClient.query(
        "media",
        id=media_id,
        columns="*",
    )
    if not result or len(result) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )
    return result[0]


@router.get(
    "/{media_id}/transcript",
    response_model=TranscriptResponse,
    summary="Get transcript text for a media item (on demand)",
)
async def get_media_transcript(
    media_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate transcript on demand for a video media item.

    Flow:
    1) Load media row from Supabase by `media_id`
    2) Take `public_url` (MinIO URL)
    3) Call AI service `/process-video` with:
       - skip_moderation = True
       - skip_summary = True
    4) Return transcription text only (do not store in DB)
    """
    media = _get_media_or_404(media_id)

    if media.get("media_type") != "video":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is only available for video media.",
        )

    file_url = media.get("public_url")
    if not file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media has no public_url stored.",
        )

    try:
        ai_result = await AIServiceClient.process_video(
            file_url=file_url,
            skip_moderation=True,
            skip_summary=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription service failed: {e}",
        )

    transcription = (ai_result or {}).get("transcription") or {}
    text = (transcription.get("text") or "").strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Transcription service returned empty text.",
        )

    return TranscriptResponse(
        media_id=media_id,
        text=text,
    )


@router.get(
    "/{media_id}/summary",
    response_model=SummaryResponse,
    summary="Summarize transcript text for a media item (on demand)",
)
async def get_media_summary(
    media_id: str,
    style: str = "brief",
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a summary for a given media item on demand.

    Flow:
    1) Load media row from Supabase by `media_id`
    2) Take `public_url` (MinIO URL)
    3) Call AI service `/process-video` and let it:
       - transcribe
       - (optionally moderate)
       - summarize
    4) Return summary text only (do not store in DB)
    """
    media = _get_media_or_404(media_id)

    if media.get("media_type") != "video":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summary is only available for video media.",
        )

    file_url = media.get("public_url")
    if not file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media has no public_url stored.",
        )

    try:
        # If you do NOT want moderation here, set skip_moderation=True
        ai_result = await AIServiceClient.process_video(
            file_url=file_url,
            summary_style=style,
            skip_moderation=False,
            skip_summary=False,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Video pipeline service failed: {e}",
        )

    summary_block = (ai_result or {}).get("summary") or {}
    summary_text = (summary_block.get("summary") or "").strip()
    summary_style = summary_block.get("style") or style

    if not summary_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Summarization service returned empty result.",
        )

    return SummaryResponse(
        media_id=media_id,
        summary=summary_text,
        style=summary_style,
        source="live-ai",  # indicates it was generated on demand
    )
