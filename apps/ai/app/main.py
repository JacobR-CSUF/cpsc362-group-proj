# /root/apps/ai/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import httpx
import logging

from app.services.gemini_moderation import (
    moderate_image as moderate_image_service,
    SafetyLevel,
    ModerationError,
)
from app.services.emotion_detect import predict_emotion_from_bytes
from app.services.gemini_summarizer import GeminiTextSummarizer, SummaryStyle

from app.services.whisper_service import (
    TranscribeRequest,
    TranscribeResponse,
    DownloadError,
    UnsupportedMediaError,
)
from app.services import whisper_service
from app.utils.url_resolver import resolve_minio_url


from app.services.shieldgemma_service import (
    moderate_text as moderate_text_service,
    SafetyCategory,
    ModerationVerdict,
    ShieldGemmaError
)


app = FastAPI(
    title="AI Service",
    description="AI features: Transcription, Moderation, Summarization",
    version="1.2.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "ai"}


@app.get("/")
async def root():
    return {"message": "AI Service is running. See /docs for API documentation."}


class ImageModerationResponse(BaseModel):
    is_safe: bool = Field(..., description="True if image is allowed on the platform")
    reason: str = Field(..., description="Short explanation for the decision")
    categories: list[str] = Field(
        default_factory=list,
        description="List of categories with severity"
    )
    level: SafetyLevel = Field(..., description="Safety level applied")


@app.post(
    "/moderation/image",
    response_model=ImageModerationResponse,
    summary="Moderate image with Google Gemini",
    description="Supports file upload or presigned URL. JPEG/PNG/WebP/HEIC/HEIF ONLY.",
)
async def moderate_image(
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Query(None, description="Presigned image URL"),
    level: SafetyLevel = Query(SafetyLevel.MODERATE),
):
    # validate input
    if file is None and not file_url:
        raise HTTPException(
            status_code=400,
            detail="Either file upload or file_url must be provided.",
        )

    # If both exist, uploaded file wins
    if file is not None and file_url is not None:
        logging.getLogger(__name__).info("Both file and file_url provided; using uploaded file.")

    # 1) load image bytes
    if file is not None:
        if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"):
            raise HTTPException(
                status_code=400,
                detail="Only JPEG, PNG, WebP, HEIC, HEIF are supported.",
            )
        mime_type = file.content_type
        image_bytes = await file.read()
    else:
        if file_url is None:
            raise HTTPException(
                status_code=400,
                detail="file_url is required when file is not provided.",
            )
        resolved_url = resolve_minio_url(file_url)
        logging.getLogger(__name__).info(f"Resolved URL: {file_url} -> {resolved_url}")

        # download from presigned URL
        async with httpx.AsyncClient(timeout=15) as client_http:
            try:
                resp = await client_http.get(resolved_url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image from URL: {e}",
                )
        mime_type = resp.headers.get("content-type", "image/jpeg")
        image_bytes = resp.content

    # 2) execute moderation
    try:
        result = moderate_image_service(
            image_bytes=image_bytes,
            mime_type=mime_type,
            level=level,
        )
    except ModerationError as me:
        raise HTTPException(502, str(me))
    except Exception as e:
        raise HTTPException(500, f"Unexpected error during image moderation: {e}")

    return ImageModerationResponse(**result)



class TranscribeAndSummarizeRequest(TranscribeRequest):
    """
    Extends TranscribeRequest with summary style field.
    """
    style: SummaryStyle = Field(
        default=SummaryStyle.BRIEF,
        description="Summary style: brief, detailed, or bullet_points",
    )


class TranscribeAndSummarizeResponse(BaseModel):
    transcript: str = Field(..., description="Full transcript text")
    summary: str = Field(..., description="Generated summary from Gemini")
    style: SummaryStyle = Field(..., description="Summary style used")


@app.post(
    "/transcribe-and-summarize",
    response_model=TranscribeAndSummarizeResponse,
    summary="Transcribe + summarize"
)
async def transcribe_and_summarize(payload: TranscribeAndSummarizeRequest):
    """
    1) Whisper transcription → text
    2) Gemini summarization → summary
    3) return both
    """
    # 1) Transcribe phase
    try:
        transcribe_dict = await whisper_service.transcribe_from_url(
            file_url=str(payload.file_url),
            language=None if payload.language in (None, "", "string") else payload.language,
        )
        # dict → Pydantic model
        transcribe_result = TranscribeResponse(**transcribe_dict)
    except DownloadError as de:
        raise HTTPException(400, f"Failed to download media: {de}")
    except UnsupportedMediaError as ue:
        raise HTTPException(415, f"Unsupported media: {ue}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected transcription error: {e}")

    transcript_text = (transcribe_result.text or "").strip()
    if not transcript_text:
        raise HTTPException(500, "Transcription returned empty text; cannot summarize.")

    # 2) Summarize phase
    try:
        summarizer = GeminiTextSummarizer()
        summary_text = summarizer.summarize(
            text=transcript_text,
            style=payload.style,
        )
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except RuntimeError as re:
        raise HTTPException(502, str(re))
    except Exception as e:
        raise HTTPException(500, f"Unexpected error during summarization: {e}")

    return TranscribeAndSummarizeResponse(
        transcript=transcript_text,
        summary=summary_text,
        style=payload.style,
    )

@app.post(
    "/emotion/detect",
    summary="Detect emotion from image",
    description="Supports uploaded file or presigned URL"
)
async def detect_emotion(
    file: UploadFile = File(None),
    file_url: Optional[str] = Query(None),
):
    # --- check input ---
    if file is None and file_url is None:
        raise HTTPException(
            status_code=400,
            detail="Either file or file_url must be provided.",
        )

    # Priority: Use uploaded file
    if file is not None:
        if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            raise HTTPException(
                status_code=400,
                detail="Supported types: JPEG, PNG, WebP, GIF.",
            )
        image_bytes = await file.read()
    else:
        resolved_url = resolve_minio_url(file_url)
        logging.getLogger(__name__).info(f"Emotion detect - Resolved URL: {file_url} -> {resolved_url}")

        # download from presigned URL
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.get(resolved_url)
                resp.raise_for_status()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download image: {e}",
                )
        image_bytes = resp.content

    # --- analyze emotion ---
    try:
        label, score, scores = predict_emotion_from_bytes(image_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Emotion detection failed: {e}",
        )

    return {
        "top_emotion": label,
        "score": score,
        "all_scores": scores,
    }


@app.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe audio/video via Whisper (URL-based)",
)
async def transcribe(payload: TranscribeRequest):
    """Transcribe Service (URL-based).
        Insert JSON
    """
    try:
        result = await whisper_service.transcribe_from_url(
            file_url=str(payload.file_url),
            language=None if payload.language in (None, "", "string") else payload.language,
        )
        return result
    except UnsupportedMediaError as exc:
        raise HTTPException(415, str(exc))
    except DownloadError as exc:
        raise HTTPException(502, str(exc))
    except Exception as exc:
        raise HTTPException(500, str(exc))
    
class TextModerationRequest(BaseModel):
    text: str = Field(..., description="Text content to moderate", min_length=1, max_length=10000)
    categories: Optional[List[SafetyCategory]] = Field(
        None,
        description="Specific categories to check (default: all)"
    )

class CategoryResult(BaseModel):
    violated: bool
    confidence: float

class TextModerationResponse(BaseModel):
    verdict: ModerationVerdict
    is_safe: bool
    categories: Dict[str, CategoryResult]
    flagged_categories: List[str]
    explanation: str
    max_violation_score: float

logger = logging.getLogger(__name__)

@app.post(
    "/moderate/text",
    response_model=TextModerationResponse,
    summary="Moderate text content with ShieldGemma",
    description="Analyzes text against safety categories: Dangerous Content, Harassment, Hate Speech, Sexually Explicit",
    tags=["moderation"]
)
async def moderate_text(request: TextModerationRequest):
    """
    Moderate text content using Google's ShieldGemma 2B model.

    **Categories:**
    - Dangerous Content: Violence, weapons, illegal activities
    - Harassment: Bullying, threats, intimidation
    - Hate Speech: Discriminatory or prejudiced content
    - Sexually Explicit: Pornographic or graphic sexual content

    **Verdict:**
    - `safe`: Content passes all checks
    - `warning`: Borderline content (score 0.3-0.5)
    - `unsafe`: Content violates policies (score > 0.5)

    **Example Request:**
    ```json
    {
      text: How do I bake a cake?,
      categories: [Dangerous Content, Hate Speech]
    }
    """
    try:
        result = moderate_text_service(
            text=request.text,
            categories=request.categories,
        )
        return TextModerationResponse(**result)

    except ShieldGemmaError as e:  # import or define ShieldGemmaError in this module
        raise HTTPException(status_code=503, detail=f"Moderation service error: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error in text moderation", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during moderation")