import asyncio
import json
import logging
import mimetypes
import os
import subprocess
import tempfile
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import httpx
import whisper
from pydantic import BaseModel, HttpUrl

from app.core.config import settings
from app.utils.url_resolver import resolve_minio_url

# Common audio/video suffixes; fallback handled via Content-Type guess.
SUPPORTED_SUFFIXES = {
    ".mp4",
    ".webm",
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".mpga",
    ".aac",
    ".opus",
    ".hevc",
    ".mov",
    ".mkv",
    ".avi",
}

# Type definition for Whisper transcription result
WhisperSegment = Dict[str, Any]  # Each segment: {"start": float, "end": float, "text": str, ...}
WhisperResult = Dict[str, Any]   # Result: {"text": str, "segments": List[WhisperSegment], "language": str}

logger = logging.getLogger(__name__)



_model = None
_model_lock = asyncio.Lock()


class DownloadError(Exception):
    """Raised when the remote file cannot be downloaded."""


class UnsupportedMediaError(Exception):
    """Raised when the downloaded file is not audio/video."""


class TranscribeRequest(BaseModel):
    file_url: HttpUrl
    language: Optional[str] = None


class Segment(BaseModel):
    start: float
    end: float
    text: str


class TranscribeResponse(BaseModel):
    text: str
    segments: List[Segment]
    duration: float
    media_duration: Optional[float] = None
    vtt: Optional[str] = None


async def _get_model():
    """Lazy-load the Whisper model once per process"""
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                _model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
    return _model



def _infer_suffix(url: str, content_type: Optional[str]) -> str:
    """Best-effort suffix detection from URL path, query params, or content-type."""
    parsed = urlparse(url)

    # 1) Suffix from path
    suffix = Path(parsed.path).suffix.lower()
    if suffix in SUPPORTED_SUFFIXES:
        return suffix

    # 2) Try common query params
    if not suffix:
        qs = parse_qs(parsed.query)
        for key in ("prefix", "filename", "name", "file", "key"):  # Added "key" for S3/MinIO
            if key in qs and qs[key]:
                candidate = Path(qs[key][0]).suffix.lower()
                if candidate in SUPPORTED_SUFFIXES:
                    return candidate

    # 3) Use Content-Type header
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed and guessed in SUPPORTED_SUFFIXES:
            return guessed

    # 4) Fallback - use .mp4 for video, .mp3 for audio, .bin otherwise
    if content_type:
        if content_type.startswith("video/"):
            logger.info(f"No extension found, defaulting to .mp4 for video type")
            return ".mp4"
        elif content_type.startswith("audio/"):
            logger.info(f"No extension found, defaulting to .mp3 for audio type")
            return ".mp3"

    logger.warning(f"Could not determine file type for {url}, using .bin")
    return ".bin"



def _probe_duration(file_path: str) -> Optional[float]:
    """Use ffprobe to get media duration"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", 
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", 
             file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return None  #  Returns None on error
    except Exception:
        return None  #  Swallows errors


def _format_timestamp(seconds: float) -> str:
    """Format seconds as WebVTT timestamp (HH:MM:SS.mmm)."""
    total_ms = max(int(round(seconds * 1000)), 0)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def _segments_to_vtt(segments: List[Dict[str, Any]]) -> str:
    """Convert Whisper segments into a simple WebVTT string."""
    lines: List[str] = ["WEBVTT", ""]

    for segment in segments:
        start = segment.get("start")
        end = segment.get("end")
        text = str(segment.get("text", "")).strip()

        if start is None or end is None or not text:
            continue

        start_ts = _format_timestamp(float(start))
        end_ts = _format_timestamp(float(end))

        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines).strip()


async def _download_to_temp(url: str) -> Tuple[Path, Optional[str]]:
    """
    Stream download to a temp file. Returns (path, content_type).
    Uses Content-Type and query params to pick a better suffix so MIME checks succeed.
    """

    resolved_url = resolve_minio_url(url)

    tmp_path: Optional[str] = None
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("GET", resolved_url, follow_redirects=True) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type")
                suffix = _infer_suffix(url, content_type)  # Use original URL for suffix detection
                fd, tmp_path = tempfile.mkstemp(prefix="whisper-", suffix=suffix)
                os.close(fd)

                with open(tmp_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
        return Path(tmp_path), content_type
    except Exception as exc:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise DownloadError(str(exc)) from exc


def _is_audio_video(path: Path, content_type: Optional[str]) -> bool:
    # Prefer server-declared Content-Type if present
    mimetype = None
    if content_type:
        mimetype = content_type.split(";")[0].strip()
    if not mimetype:
        mimetype, _ = mimetypes.guess_type(path.name)
    return bool(mimetype and (mimetype.startswith("audio/") or mimetype.startswith("video/")))


async def transcribe_from_url(file_url: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Download audio/video from URL, transcribe with Whisper.
    Returns {"text": ..., "segments": [...], "duration": ...}
    """
    
    resolved_url = resolve_minio_url(file_url)

    temp_path, content_type = await _download_to_temp(resolved_url)
    try:
        if not _is_audio_video(temp_path, content_type):
            raise UnsupportedMediaError(f"Unsupported media type for {temp_path.name}")

        model = await _get_model()
        loop = asyncio.get_running_loop()

        result: WhisperResult = await loop.run_in_executor(
            None,
            partial(model.transcribe, str(temp_path), language=language, fp16=False),
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    segments = [
        {
            "start": float(seg.get("start", 0.0)),
            "end": float(seg.get("end", 0.0)),
            "text": seg.get("text", "").strip(),
        }
        for seg in result.get("segments", [])
    ]

    # Prefer Whisper's duration if present; otherwise derive from the last segment end.
    duration_raw = result.get("duration")
    if duration_raw is not None:
        if isinstance(duration_raw, (int, float)):
            duration = float(duration_raw)
        elif isinstance(duration_raw, str):
            try:
                duration = float(duration_raw)
            except ValueError:
                duration = 0.0
        else:
            duration = 0.0
    elif segments:
        last_end = segments[-1].get("end")
        duration = float(last_end) if last_end is not None else 0.0
    else:
        duration = 0.0

    media_duration = _probe_duration(str(temp_path))
    vtt_text = _segments_to_vtt(segments) if segments else None

    return {
        "text": result.get("text", "").strip(),
        "segments": segments,
        "duration": duration,
        "media_duration": media_duration,
        "vtt": vtt_text,
    }
