# /root/apps/ai/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import time
import httpx
import logging

from app.services.ai_pipeline import (
    VideoPipelineService,
    ImagePipelineService,
    VideoPipelineRequest,
    ImagePipelineRequest,
    VideoPipelineResponse,
    ImagePipelineResponse,
    PipelineJobStatus,
    PipelineStatus,
    PipelineVerdict,
    StageResult,
    get_job_status,
    store_job,
)
from uuid import uuid4
import asyncio
from urllib.parse import urlparse


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
    ShieldGemmaService,
    SafetyCategory,
    ModerationVerdict,
    ShieldGemmaError
)

logger = logging.getLogger(__name__)

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


# ========== IMAGE MODERATION ==========

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
        logger.info("Both file and file_url provided; using uploaded file.")

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
        logger.info(f"Resolved URL: {file_url} -> {resolved_url}")

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


# ========== TRANSCRIPTION & SUMMARIZATION ==========

class TranscribeAndSummarizeRequest(TranscribeRequest):
    """Extends TranscribeRequest with summary style field."""
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
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe audio/video via Whisper (URL-based)",
)
async def transcribe(payload: TranscribeRequest):
    """Transcribe Service (URL-based)."""
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


# ========== EMOTION DETECTION ==========

@app.post(
    "/emotion/detect",
    summary="Detect emotion from image",
    description="Supports uploaded file or presigned URL"
)
async def detect_emotion(
    file: UploadFile = File(None),
    file_url: Optional[str] = Query(None),
):
    if file is None and file_url is None:
        raise HTTPException(
            status_code=400,
            detail="Either file or file_url must be provided.",
        )

    if file is not None:
        if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
            raise HTTPException(
                status_code=400,
                detail="Supported types: JPEG, PNG, WebP, GIF.",
            )
        image_bytes = await file.read()
    else:
        resolved_url = resolve_minio_url(file_url)
        logger.info(f"Emotion detect - Resolved URL: {file_url} -> {resolved_url}")

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


# ========== TEXT MODERATION (ShieldGemma) ==========

class TextModerationRequest(BaseModel):
    """Request model for text moderation"""
    text: str = Field(
        ..., 
        description="Text content to moderate", 
        min_length=1, 
        max_length=10000
    )
    categories: Optional[List[str]] = Field(
        None,
        description="Specific categories to check. Options: 'Dangerous Content', 'Harassment', 'Hate Speech', 'Sexually Explicit'. Default: all categories.",
        examples=[["Dangerous Content", "Hate Speech"]]
    )


class CategoryResult(BaseModel):
    """Result for a single category"""
    violated: bool = Field(..., description="Whether content violates this category")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")


class TextModerationResponse(BaseModel):
    """Response model for text moderation"""
    verdict: str = Field(..., description="Overall verdict: safe, warning, or unsafe")
    is_safe: bool = Field(..., description="True if content passes all safety checks")
    categories: Dict[str, CategoryResult] = Field(..., description="Results per category")
    flagged_categories: List[str] = Field(..., description="List of violated categories")
    explanation: str = Field(..., description="Human-readable explanation")
    max_violation_score: float = Field(..., description="Highest violation confidence score")


@app.post(
    "/moderate/text",
    response_model=TextModerationResponse,
    summary="Moderate text content with ShieldGemma",
    description="""
Analyzes text against safety categories using Google's ShieldGemma 2B model.

**Categories:**
- `Dangerous Content`: Violence, weapons, illegal activities, self-harm
- `Harassment`: Bullying, threats, intimidation
- `Hate Speech`: Discriminatory or prejudiced content targeting protected groups
- `Sexually Explicit`: Pornographic or graphic sexual content

**Verdict Levels:**
- `safe`: Content passes all checks (score < 0.3)
- `warning`: Borderline content (score 0.3-0.5)
- `unsafe`: Content violates policies (score > 0.5)
    """,
    tags=["moderation"]
)
async def moderate_text(request: TextModerationRequest):
    """
    Moderate text content using Google's ShieldGemma 2B model.
    """
    logger.info(f"Text moderation request: {len(request.text)} chars, categories={request.categories}")

    try:
        # ✅ FIXED: Convert string categories to SafetyCategory enums
        category_enums = None
        if request.categories:
            category_enums = []
            for cat_str in request.categories:
                try:
                    category_enums.append(SafetyCategory(cat_str))
                except ValueError:
                    logger.warning(f"Unknown category '{cat_str}', skipping")

            # If all categories were invalid, use all categories
            if not category_enums:
                logger.warning("No valid categories provided, using all categories")
                category_enums = None

        # ✅ FIXED: Call ShieldGemmaService directly with proper types
        result = ShieldGemmaService.moderate_text(
            text=request.text,
            categories=category_enums
        )

        logger.info(f"Moderation result: verdict={result['verdict']}, max_score={result['max_violation_score']}")

        return TextModerationResponse(**result)

    except ShieldGemmaError as e:
        logger.error(f"ShieldGemma service error: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Moderation service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in text moderation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during moderation"
        )

# ========== AI PIPELINES ==========
@app.post(
    "/process-video",
    response_model=VideoPipelineResponse,
    summary="Process video through full AI pipeline",
    description="""
**Complete Video Processing Pipeline**

Processes video/audio through all AI stages:

1. **Transcription** (Whisper) - Converts audio to text
2. **Text Moderation** (ShieldGemma) - Checks transcript for policy violations
3. **Summarization** (Gemini) - Generates summary (only if content is safe)

**Short-Circuit Behavior:**
- If transcription fails → Pipeline stops, returns error
- If content is UNSAFE → Summarization is skipped, returns transcript + moderation result
- If content is SAFE → Full pipeline completes with transcript + summary

**Response includes:**
- Stage-by-stage results with timing
- Full transcript (if transcription succeeded)
- Moderation verdict with flagged categories
- Summary (only if content passed moderation)
    """,
    tags=["pipeline"]
)
async def process_video(request: VideoPipelineRequest):
    """
    Process video through transcription → moderation → summarization pipeline.
    """
    logger.info(f"Video pipeline request: {request.file_url}")

    parsed = urlparse(str(request.file_url))
    is_gif = parsed.path.lower().endswith(".gif")

    if is_gif:
        logger.info("GIF detected; routing through image moderation pipeline.")
        pipeline_start = datetime.utcnow()
        start_time = time.time()
        try:
            img_result = await ImagePipelineService.process(
                ImagePipelineRequest(
                    file_url=request.file_url, safety_level=SafetyLevel.MODERATE
                )
            )
        except Exception as e:
            logger.error(f"GIF moderation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"GIF moderation failed: {str(e)}"
            )

        duration_ms = int((time.time() - start_time) * 1000)

        stage = StageResult(
            stage="gif_image_moderation",
            status=PipelineStatus.COMPLETED
            if img_result.is_safe
            else PipelineStatus.FAILED,
            started_at=pipeline_start,
            completed_at=datetime.utcnow(),
            duration_ms=duration_ms,
            data={
                "moderation": img_result.moderation.model_dump()
                if img_result.moderation
                else None
            },
            error=None if img_result.is_safe else "Image failed moderation",
        )

        verdict = PipelineVerdict.SAFE if img_result.is_safe else PipelineVerdict.UNSAFE

        return VideoPipelineResponse(
            pipeline="video",
            file_url=str(request.file_url),
            verdict=verdict,
            is_safe=img_result.is_safe,
            processing_time_ms=duration_ms,
            started_at=pipeline_start,
            completed_at=datetime.utcnow(),
            stages=[stage],
            transcription=None,
            text_moderation=None,
            summary=None,
            short_circuited=True,
            short_circuit_reason="GIF content routed through image moderation",
        )

    try:
        result = await VideoPipelineService.process(request)
        return result
    except Exception as e:
        logger.error(f"Video pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing failed: {str(e)}"
        )


@app.post(
    "/process-image",
    response_model=ImagePipelineResponse,
    summary="Process image through moderation pipeline",
    description="""
**Image Safety Check Pipeline**

Processes image through content moderation:

1. **Download** - Fetches image from presigned URL
2. **Image Moderation** (Gemini) - Analyzes for policy violations

**Safety Levels:**
- `strict` - Flags mild content as unsafe
- `moderate` - Default, balanced approach
- `lenient` - Only flags severe violations

**Supported formats:** JPEG, PNG, WebP, HEIC, HEIF
    """,
    tags=["pipeline"]
)
async def process_image(request: ImagePipelineRequest):
    """
    Process image through moderation pipeline.
    """
    logger.info(f"Image pipeline request: {request.file_url}")

    try:
        result = await ImagePipelineService.process(request)
        return result
    except Exception as e:
        logger.error(f"Image pipeline failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing failed: {str(e)}"
        )


@app.post(
    "/process-video/async",
    response_model=PipelineJobStatus,
    summary="Start async video processing (for large files)",
    description="Starts background processing and returns a job ID to poll for results.",
    tags=["pipeline"]
)
async def process_video_async(request: VideoPipelineRequest):
    """
    Start async video processing for large files.
    Returns a job_id to poll for status.
    """
    job_id = str(uuid4())

    job = PipelineJobStatus(
        job_id=job_id,
        status="pending",
        pipeline_type="video",
        created_at=datetime.utcnow()
    )
    store_job(job)

    # Start background task
    async def run_pipeline():
        try:
            job.status = "processing"
            store_job(job)

            result = await VideoPipelineService.process(request)

            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.result = result.model_dump()
            store_job(job)

        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            store_job(job)

    asyncio.create_task(run_pipeline())

    return job


@app.get(
    "/pipeline/status/{job_id}",
    response_model=PipelineJobStatus,
    summary="Check async pipeline job status",
    tags=["pipeline"]
)
async def get_pipeline_status(job_id: str):
    """
    Check the status of an async pipeline job.
    """
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
