# apps/ai/app/services/ai_pipeline.py
"""
AI Pipeline Orchestration Service
Coordinates all AI services into unified processing pipelines.
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from io import BytesIO
from pydantic import BaseModel, Field, HttpUrl
from PIL import Image

# Import existing services
from app.services.whisper_service import (
    transcribe_from_url,
    DownloadError,
    UnsupportedMediaError,
)
from app.services.shieldgemma_service import (
    ShieldGemmaService,
    SafetyCategory,
    ModerationVerdict,
    ShieldGemmaError,
)
from app.services.gemini_summarizer import GeminiTextSummarizer, SummaryStyle
from app.services.gemini_moderation import (
    moderate_image as gemini_moderate_image,
    SafetyLevel,
    ModerationError as ImageModerationError,
)
from app.utils.url_resolver import resolve_minio_url

import httpx

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS
# ============================================================

class PipelineStatus(str, Enum):
    """Status of a pipeline stage"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineVerdict(str, Enum):
    """Overall pipeline verdict"""
    SAFE = "safe"
    UNSAFE = "unsafe"
    ERROR = "error"


# ============================================================
# RESPONSE MODELS
# ============================================================

class StageResult(BaseModel):
    """Result of a single pipeline stage"""
    stage: str = Field(..., description="Name of the pipeline stage")
    status: PipelineStatus = Field(..., description="Status of this stage")
    started_at: Optional[datetime] = Field(None, description="When stage started")
    completed_at: Optional[datetime] = Field(None, description="When stage completed")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Stage output data")


class TranscriptionData(BaseModel):
    """Transcription stage output"""
    text: str = Field(..., description="Full transcript text")
    segments: List[Dict[str, Any]] = Field(default_factory=list, description="Timed segments")
    duration: float = Field(0.0, description="Audio/video duration in seconds")
    language: Optional[str] = Field(None, description="Detected language")


class TextModerationData(BaseModel):
    """Text moderation stage output"""
    verdict: str = Field(..., description="Moderation verdict: safe/warning/unsafe")
    is_safe: bool = Field(..., description="Whether content is safe")
    flagged_categories: List[str] = Field(default_factory=list, description="Violated categories")
    max_violation_score: float = Field(0.0, description="Highest violation score")
    explanation: str = Field("", description="Human-readable explanation")


class SummarizationData(BaseModel):
    """Summarization stage output"""
    summary: str = Field(..., description="Generated summary")
    style: str = Field(..., description="Summary style used")


class ImageModerationData(BaseModel):
    """Image moderation stage output"""
    is_safe: bool = Field(..., description="Whether image is safe")
    reason: str = Field(..., description="Explanation for decision")
    categories: List[str] = Field(default_factory=list, description="Flagged categories")
    level: str = Field(..., description="Safety level applied")


class VideoPipelineResponse(BaseModel):
    """Complete video pipeline response"""
    pipeline: str = Field(default="video", description="Pipeline type")
    file_url: str = Field(..., description="Input file URL")
    verdict: PipelineVerdict = Field(..., description="Overall safety verdict")
    is_safe: bool = Field(..., description="Whether content is safe for platform")
    processing_time_ms: int = Field(..., description="Total processing time")
    started_at: datetime = Field(..., description="Pipeline start time")
    completed_at: datetime = Field(..., description="Pipeline completion time")

    # Stage results
    stages: List[StageResult] = Field(..., description="Results for each stage")

    # Extracted data (only if stages succeeded)
    transcription: Optional[TranscriptionData] = Field(None, description="Transcription output")
    text_moderation: Optional[TextModerationData] = Field(None, description="Text moderation output")
    summary: Optional[SummarizationData] = Field(None, description="Summary output (only if safe)")

    # Short-circuit info
    short_circuited: bool = Field(False, description="Whether pipeline was short-circuited")
    short_circuit_reason: Optional[str] = Field(None, description="Reason for short-circuit")


class ImagePipelineResponse(BaseModel):
    """Complete image pipeline response"""
    pipeline: str = Field(default="image", description="Pipeline type")
    file_url: str = Field(..., description="Input file URL")
    verdict: PipelineVerdict = Field(..., description="Overall safety verdict")
    is_safe: bool = Field(..., description="Whether image is safe for platform")
    processing_time_ms: int = Field(..., description="Total processing time")
    started_at: datetime = Field(..., description="Pipeline start time")
    completed_at: datetime = Field(..., description="Pipeline completion time")

    # Stage results
    stages: List[StageResult] = Field(..., description="Results for each stage")

    # Moderation data
    moderation: Optional[ImageModerationData] = Field(None, description="Moderation output")


# ============================================================
# REQUEST MODELS
# ============================================================

class VideoPipelineRequest(BaseModel):
    """Request for video processing pipeline"""
    file_url: HttpUrl = Field(..., description="Presigned URL to video/audio file")
    language: Optional[str] = Field(None, description="Language hint for transcription")
    summary_style: SummaryStyle = Field(
        default=SummaryStyle.BRIEF,
        description="Summary style: brief, detailed, or bullet_points"
    )
    skip_moderation: bool = Field(
        default=False,
        description="Skip text moderation (not recommended for production)"
    )
    skip_summary: bool = Field(
        default=False,
        description="Skip summarization stage"
    )


class ImagePipelineRequest(BaseModel):
    """Request for image processing pipeline"""
    file_url: HttpUrl = Field(..., description="Presigned URL to image file")
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.MODERATE,
        description="Safety threshold: strict, moderate, or lenient"
    )
    user: Optional[str] = Field(None, description="Username initiating the request (for logging)")


# ============================================================
# VIDEO PIPELINE SERVICE
# ============================================================

class VideoPipelineService:
    """
    Orchestrates video/audio processing pipeline:
    1. Transcription (Whisper)
    2. Text Moderation (ShieldGemma) 
    3. Summarization (Gemini) - only if content is safe
    """

    @classmethod
    async def process(cls, request: VideoPipelineRequest) -> VideoPipelineResponse:
        """Execute the full video processing pipeline"""

        pipeline_start = datetime.utcnow()
        start_time = time.time()

        stages: List[StageResult] = []
        transcription_data: Optional[TranscriptionData] = None
        moderation_data: Optional[TextModerationData] = None
        summary_data: Optional[SummarizationData] = None

        short_circuited = False
        short_circuit_reason = None
        overall_verdict = PipelineVerdict.SAFE
        is_safe = True

        file_url = str(request.file_url)

        logger.info("=" * 60)
        logger.info(f"VIDEO PIPELINE STARTED")
        logger.info(f"URL: {file_url[:80]}...")
        logger.info("=" * 60)

        # ========== STAGE 1: TRANSCRIPTION ==========
        stage_start = time.time()
        stage_started_at = datetime.utcnow()

        logger.info("[Stage 1/3] Transcription starting...")

        try:
            result = await transcribe_from_url(
                file_url=file_url,
                language=request.language if request.language not in (None, "", "string") else None
            )

            transcription_data = TranscriptionData(
                text=result.get("text", ""),
                segments=result.get("segments", []),
                duration=result.get("duration", 0.0),
                language=request.language
            )

            stage_duration = int((time.time() - stage_start) * 1000)

            stages.append(StageResult(
                stage="transcription",
                status=PipelineStatus.COMPLETED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                data={
                    "text_length": len(transcription_data.text),
                    "segment_count": len(transcription_data.segments),
                    "duration": transcription_data.duration
                }
            ))

            logger.info(f"[Stage 1/3] Transcription completed: {len(transcription_data.text)} chars, {stage_duration}ms")

            # Check for empty transcription
            if not transcription_data.text.strip():
                logger.warning("Transcription returned empty text")
                short_circuited = True
                short_circuit_reason = "Transcription returned empty text - no audio content detected"
                overall_verdict = PipelineVerdict.ERROR

        except DownloadError as e:
            stage_duration = int((time.time() - stage_start) * 1000)
            stages.append(StageResult(
                stage="transcription",
                status=PipelineStatus.FAILED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                error=f"Download failed: {str(e)}"
            ))
            logger.error(f"[Stage 1/3] Transcription FAILED (download): {e}")
            overall_verdict = PipelineVerdict.ERROR
            short_circuited = True
            short_circuit_reason = f"Failed to download media: {str(e)}"

        except UnsupportedMediaError as e:
            stage_duration = int((time.time() - stage_start) * 1000)
            stages.append(StageResult(
                stage="transcription",
                status=PipelineStatus.FAILED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                error=f"Unsupported media: {str(e)}"
            ))
            logger.error(f"[Stage 1/3] Transcription FAILED (unsupported): {e}")
            overall_verdict = PipelineVerdict.ERROR
            short_circuited = True
            short_circuit_reason = f"Unsupported media format: {str(e)}"

        except Exception as e:
            stage_duration = int((time.time() - stage_start) * 1000)
            stages.append(StageResult(
                stage="transcription",
                status=PipelineStatus.FAILED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                error=str(e)
            ))
            logger.error(f"[Stage 1/3] Transcription FAILED: {e}", exc_info=True)
            overall_verdict = PipelineVerdict.ERROR
            short_circuited = True
            short_circuit_reason = f"Transcription error: {str(e)}"

        # ========== STAGE 2: TEXT MODERATION ==========
        if not short_circuited and not request.skip_moderation:
            stage_start = time.time()
            stage_started_at = datetime.utcnow()

            logger.info("[Stage 2/3] Text moderation starting...")

            try:
                # Run moderation in thread pool (it's CPU-bound)
                loop = asyncio.get_running_loop()
                mod_result = await loop.run_in_executor(
                    None,
                    lambda: ShieldGemmaService.moderate_text(transcription_data.text)
                )

                moderation_data = TextModerationData(
                    verdict=mod_result.get("verdict", "safe"),
                    is_safe=mod_result.get("is_safe", True),
                    flagged_categories=mod_result.get("flagged_categories", []),
                    max_violation_score=mod_result.get("max_violation_score", 0.0),
                    explanation=mod_result.get("explanation", "")
                )

                stage_duration = int((time.time() - stage_start) * 1000)

                stages.append(StageResult(
                    stage="text_moderation",
                    status=PipelineStatus.COMPLETED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    data={
                        "verdict": moderation_data.verdict,
                        "is_safe": moderation_data.is_safe,
                        "flagged_categories": moderation_data.flagged_categories,
                        "max_score": moderation_data.max_violation_score
                    }
                ))

                logger.info(f"[Stage 2/3] Moderation completed: {moderation_data.verdict}, {stage_duration}ms")

                # Check if content is unsafe - SHORT CIRCUIT
                if not moderation_data.is_safe:
                    logger.warning(f"Content flagged as UNSAFE: {moderation_data.flagged_categories}")
                    short_circuited = True
                    short_circuit_reason = f"Content moderation failed: {moderation_data.explanation[:200]}"
                    overall_verdict = PipelineVerdict.UNSAFE
                    is_safe = False

            except ShieldGemmaError as e:
                stage_duration = int((time.time() - stage_start) * 1000)
                stages.append(StageResult(
                    stage="text_moderation",
                    status=PipelineStatus.FAILED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    error=str(e)
                ))
                logger.error(f"[Stage 2/3] Moderation FAILED: {e}")
                # Don't short-circuit on moderation failure - continue with warning
                moderation_data = TextModerationData(
                    verdict="error",
                    is_safe=False,
                    flagged_categories=[],
                    max_violation_score=0.0,
                    explanation=f"Moderation service error: {str(e)}"
                )

            except Exception as e:
                stage_duration = int((time.time() - stage_start) * 1000)
                stages.append(StageResult(
                    stage="text_moderation",
                    status=PipelineStatus.FAILED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    error=str(e)
                ))
                logger.error(f"[Stage 2/3] Moderation FAILED: {e}", exc_info=True)

        elif request.skip_moderation:
            stages.append(StageResult(
                stage="text_moderation",
                status=PipelineStatus.SKIPPED,
                data={"reason": "Skipped by request"}
            ))
            logger.info("[Stage 2/3] Text moderation SKIPPED by request")

        elif short_circuited:
            stages.append(StageResult(
                stage="text_moderation",
                status=PipelineStatus.SKIPPED,
                data={"reason": "Previous stage failed"}
            ))

        # ========== STAGE 3: SUMMARIZATION ==========
        if not short_circuited and not request.skip_summary:
            stage_start = time.time()
            stage_started_at = datetime.utcnow()

            logger.info("[Stage 3/3] Summarization starting...")

            try:
                summarizer = GeminiTextSummarizer()

                # Run in thread pool
                loop = asyncio.get_running_loop()
                summary_text = await loop.run_in_executor(
                    None,
                    lambda: summarizer.summarize(
                        text=transcription_data.text,
                        style=request.summary_style
                    )
                )

                summary_data = SummarizationData(
                    summary=summary_text,
                    style=request.summary_style.value
                )

                stage_duration = int((time.time() - stage_start) * 1000)

                stages.append(StageResult(
                    stage="summarization",
                    status=PipelineStatus.COMPLETED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    data={
                        "summary_length": len(summary_data.summary),
                        "style": summary_data.style
                    }
                ))

                logger.info(f"[Stage 3/3] Summarization completed: {len(summary_data.summary)} chars, {stage_duration}ms")

            except Exception as e:
                stage_duration = int((time.time() - stage_start) * 1000)
                stages.append(StageResult(
                    stage="summarization",
                    status=PipelineStatus.FAILED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    error=str(e)
                ))
                logger.error(f"[Stage 3/3] Summarization FAILED: {e}", exc_info=True)
                # Don't change overall verdict - partial results are still useful

        elif request.skip_summary:
            stages.append(StageResult(
                stage="summarization",
                status=PipelineStatus.SKIPPED,
                data={"reason": "Skipped by request"}
            ))
            logger.info("[Stage 3/3] Summarization SKIPPED by request")

        elif short_circuited:
            stages.append(StageResult(
                stage="summarization",
                status=PipelineStatus.SKIPPED,
                data={"reason": short_circuit_reason or "Content flagged as unsafe"}
            ))
            logger.info(f"[Stage 3/3] Summarization SKIPPED: {short_circuit_reason}")

        # ========== BUILD RESPONSE ==========
        pipeline_end = datetime.utcnow()
        total_time = int((time.time() - start_time) * 1000)

        logger.info("=" * 60)
        logger.info(f"VIDEO PIPELINE COMPLETED")
        logger.info(f"Verdict: {overall_verdict.value}")
        logger.info(f"Total time: {total_time}ms")
        logger.info("=" * 60)

        return VideoPipelineResponse(
            pipeline="video",
            file_url=file_url,
            verdict=overall_verdict,
            is_safe=is_safe,
            processing_time_ms=total_time,
            started_at=pipeline_start,
            completed_at=pipeline_end,
            stages=stages,
            transcription=transcription_data,
            text_moderation=moderation_data,
            summary=summary_data,
            short_circuited=short_circuited,
            short_circuit_reason=short_circuit_reason
        )


# ============================================================
# IMAGE PIPELINE SERVICE
# ============================================================

class ImagePipelineService:
    """
    Orchestrates image processing pipeline:
    1. Image Moderation (Gemini)

    Simple wrapper for consistency with video pipeline.
    """

    @classmethod
    async def process(cls, request: ImagePipelineRequest) -> ImagePipelineResponse:
        """Execute the image processing pipeline"""

        pipeline_start = datetime.utcnow()
        start_time = time.time()

        stages: List[StageResult] = []
        moderation_data: Optional[ImageModerationData] = None

        overall_verdict = PipelineVerdict.SAFE
        is_safe = True

        file_url = str(request.file_url).rstrip("/")

        logger.info("=" * 60)
        logger.info(f"IMAGE PIPELINE STARTED")
        logger.info(f"URL: {file_url[:80]}...")
        if request.user:
            logger.info(f"User: {request.user}")
        logger.info(f"Safety level: {request.safety_level.value}")
        logger.info("=" * 60)

        # ========== STAGE 1: DOWNLOAD IMAGE ==========
        stage_start = time.time()
        stage_started_at = datetime.utcnow()

        logger.info("[Stage 1/2] Downloading image...")

        image_bytes: Optional[bytes] = None
        mime_type: str = "image/jpeg"

        try:
            resolved_url = resolve_minio_url(file_url)

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(resolved_url)
                resp.raise_for_status()

            image_bytes = resp.content
            mime_type = resp.headers.get("content-type", "image/jpeg")

            # Convert GIF to PNG (first frame) so moderation accepts it.
            if mime_type.lower().startswith("image/gif"):
                try:
                    with Image.open(BytesIO(image_bytes)) as im:
                        im.seek(0)
                        buf = BytesIO()
                        im.convert("RGB").save(buf, format="PNG")
                        image_bytes = buf.getvalue()
                        mime_type = "image/png"
                        logger.info("Converted GIF to PNG (first frame) for moderation.")
                except Exception as e:
                    stage_duration = int((time.time() - stage_start) * 1000)
                    stages.append(StageResult(
                        stage="download",
                        status=PipelineStatus.FAILED,
                        started_at=stage_started_at,
                        completed_at=datetime.utcnow(),
                        duration_ms=stage_duration,
                        error=f"GIF conversion failed: {e}",
                    ))
                    overall_verdict = PipelineVerdict.ERROR
                    is_safe = False
                    return ImagePipelineResponse(
                        pipeline="image",
                        file_url=file_url,
                        verdict=overall_verdict,
                        is_safe=is_safe,
                        processing_time_ms=int((time.time() - start_time) * 1000),
                        started_at=pipeline_start,
                        completed_at=datetime.utcnow(),
                        stages=stages,
                        moderation=None,
                    )

            stage_duration = int((time.time() - stage_start) * 1000)

            stages.append(StageResult(
                stage="download",
                status=PipelineStatus.COMPLETED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                data={
                    "size_bytes": len(image_bytes),
                    "mime_type": mime_type
                }
            ))

            logger.info(f"[Stage 1/2] Download completed: {len(image_bytes)} bytes, {stage_duration}ms")

        except httpx.HTTPError as e:
            stage_duration = int((time.time() - stage_start) * 1000)
            stages.append(StageResult(
                stage="download",
                status=PipelineStatus.FAILED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                error=f"HTTP error: {str(e)}"
            ))
            logger.error(f"[Stage 1/2] Download FAILED: {e}")
            overall_verdict = PipelineVerdict.ERROR

        except Exception as e:
            stage_duration = int((time.time() - stage_start) * 1000)
            stages.append(StageResult(
                stage="download",
                status=PipelineStatus.FAILED,
                started_at=stage_started_at,
                completed_at=datetime.utcnow(),
                duration_ms=stage_duration,
                error=str(e)
            ))
            logger.error(f"[Stage 1/2] Download FAILED: {e}", exc_info=True)
            overall_verdict = PipelineVerdict.ERROR

        # ========== STAGE 2: IMAGE MODERATION ==========
        if image_bytes is not None:
            stage_start = time.time()
            stage_started_at = datetime.utcnow()

            logger.info("[Stage 2/2] Image moderation starting...")

            try:
                # Run in thread pool (may involve network call to Gemini)
                loop = asyncio.get_running_loop()
                mod_result = await loop.run_in_executor(
                    None,
                    lambda: gemini_moderate_image(
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                        level=request.safety_level
                    )
                )

                moderation_data = ImageModerationData(
                    is_safe=mod_result.get("is_safe", True),
                    reason=mod_result.get("reason", ""),
                    categories=mod_result.get("categories", []),
                    level=mod_result.get("level", request.safety_level.value)
                )

                stage_duration = int((time.time() - stage_start) * 1000)

                stages.append(StageResult(
                    stage="image_moderation",
                    status=PipelineStatus.COMPLETED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    data={
                        "is_safe": moderation_data.is_safe,
                        "categories": moderation_data.categories,
                        "level": moderation_data.level
                    }
                ))

                logger.info(f"[Stage 2/2] Moderation completed: safe={moderation_data.is_safe}, {stage_duration}ms")

                if not moderation_data.is_safe:
                    overall_verdict = PipelineVerdict.UNSAFE
                    is_safe = False
                    logger.warning(f"Image flagged as UNSAFE: {moderation_data.reason}")

            except ImageModerationError as e:
                stage_duration = int((time.time() - stage_start) * 1000)
                stages.append(StageResult(
                    stage="image_moderation",
                    status=PipelineStatus.FAILED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    error=str(e)
                ))
                logger.error(f"[Stage 2/2] Moderation FAILED: {e}")
                overall_verdict = PipelineVerdict.ERROR
                is_safe = False  # Fail safe

            except Exception as e:
                stage_duration = int((time.time() - stage_start) * 1000)
                stages.append(StageResult(
                    stage="image_moderation",
                    status=PipelineStatus.FAILED,
                    started_at=stage_started_at,
                    completed_at=datetime.utcnow(),
                    duration_ms=stage_duration,
                    error=str(e)
                ))
                logger.error(f"[Stage 2/2] Moderation FAILED: {e}", exc_info=True)
                overall_verdict = PipelineVerdict.ERROR
                is_safe = False  # Fail safe
        else:
            stages.append(StageResult(
                stage="image_moderation",
                status=PipelineStatus.SKIPPED,
                data={"reason": "Download failed"}
            ))

        # ========== BUILD RESPONSE ==========
        pipeline_end = datetime.utcnow()
        total_time = int((time.time() - start_time) * 1000)

        logger.info("=" * 60)
        logger.info(f"IMAGE PIPELINE COMPLETED")
        logger.info(f"Verdict: {overall_verdict.value}")
        logger.info(f"Total time: {total_time}ms")
        logger.info("=" * 60)

        return ImagePipelineResponse(
            pipeline="image",
            file_url=file_url,
            verdict=overall_verdict,
            is_safe=is_safe,
            processing_time_ms=total_time,
            started_at=pipeline_start,
            completed_at=pipeline_end,
            stages=stages,
            moderation=moderation_data
        )


# ============================================================
# BACKGROUND TASK SUPPORT (Optional)
# ============================================================

class PipelineJobStatus(BaseModel):
    """Status of a background pipeline job"""
    job_id: str
    status: str  # pending, processing, completed, failed
    pipeline_type: str  # video, image
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Simple in-memory job store (use Redis in production)
_job_store: Dict[str, PipelineJobStatus] = {}


def get_job_status(job_id: str) -> Optional[PipelineJobStatus]:
    """Get status of a background job"""
    return _job_store.get(job_id)


def store_job(job: PipelineJobStatus) -> None:
    """Store a job status"""
    _job_store[job.job_id] = job
