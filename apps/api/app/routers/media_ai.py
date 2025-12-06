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
    summary="Get transcript text for a media item",
)
async def get_media_transcript(
    media_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Return transcript text for a given media (video) item.

    Assumes:
    - For video uploads, the Whisper pipeline already stored transcript
      text inside the `caption` column of the `media` table.
    """
    media = _get_media_or_404(media_id)

    # Optional: restrict to videos only
    if media.get("media_type") != "video":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is only available for video media.",
        )

    transcript = (media.get("caption") or "").strip()
    if not transcript:
        # Either Whisper did not run, or no text was stored
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transcript stored for this media.",
        )

    return TranscriptResponse(
        media_id=media_id,
        text=transcript,
    )


@router.get(
    "/{media_id}/summary",
    response_model=SummaryResponse,
    summary="Summarize transcript text for a media item",
)
async def get_media_summary(
    media_id: str,
    style: str = "brief",
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a summary for a given media item.

    Flow:
    1) Load transcript text from `media.caption`
    2) Call AI service /summarize via AIServiceClient.summarize_text
    3) Return summary text
    """
    media = _get_media_or_404(media_id)

    if media.get("media_type") != "video":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summary is only available for video media.",
        )

    transcript = (media.get("caption") or "").strip()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transcript stored for this media.",
        )

    # Call AI service summarizer
    try:
        ai_result = await AIServiceClient.summarize_text(
            text=transcript,
            style=style,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Summarization service failed: {e}",
        )

    summary_text = (ai_result or {}).get("summary", "").strip()
    if not summary_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Summarization service returned empty result.",
        )

    return SummaryResponse(
        media_id=media_id,
        summary=summary_text,
        style=style,
        source="media.caption",
    )
