import asyncio, mimetypes, whisper, httpx, tempfile, os
from pathlib import Path
from mimetypes import guess_type
from functools import partial
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv

from pydantic import HttpUrl

##################################
#         funny var box          #
################################## 
SUPPORTED_SUFFIXES = {".mp4", ".webm", ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".mpga", ".aac", ".opus"}
_model = None
_model_lock = asyncio.Lock()

# from app.core.config import settings
load_dotenv(dotenv_path='./../.env')
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL_SIZE')

async def _get_model():
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                _model = whisper.load_model(WHISPER_MODEL_SIZE)
    return _model

class DownloadError(Exception):
    """Unable to download remote file."""

class UnsupportedMediaError(Exception):
    """Unable to process due to non video/audio"""

def _infer_suffix(url: str, content_type: Optional[str]) -> str:
    """Try to detetc file type from url, query, or mime content type"""
    parsed = urlparse(url)

    # This is case 1, just simple checking the end
    suffix = Path(parsed.path).suffix.lower()

    # This is case 2, from the query parameter like ?file=test.mp3 for minio
    if not suffix:
        qs = parse_qs(parsed.query)
        for key in ("prefix", "filename", "name", "file"):
            candidate = Path(qs[key][0]).suffix.lower()
            if candidate:
                suffix = candidate # we got it
                break
    
    # This is case 3 to check the content headers, probably most foolproof
    if (not suffix or suffix not in SUPPORTED_SUFFIXES) and content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            suffix = guessed

    # On our 4th case, just give up 
    if not suffix or suffix not in SUPPORTED_SUFFIXES:
        suffix = ".bin"
    return suffix

async def _download_to_temp(url: str) -> Tuple[Path, Optional[str]]:
    """Stream the download to a temp file and uses Content-Type (case 3) to check mime"""
    tmp_path: Optional[str] = None
    try:   
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("GET", url, follow_redirects=True) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get('Content-Type')
                suffix = _infer_suffix(url, content_type)
                fd, tmp_path = tempfile.mktemp(prefix="whisper-", suffix=suffix)
                os.close(fd) # safety

                with open(tmp_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(): # text?
                        f.write(chunk)

        return Path(tmp_path), content_type
    except Exception as e:
        if tmp_path and os.path.exists():
            os.remove(tmp_path)
        raise DownloadError(str(e)) from e
    
def _is_audio_video(path: Path, content_type: Optional[str]) -> bool:
    # if not server declared
    mimetype = None
    if content_type:
        mimetypes = content_type.split(";")[0].strip()
    if not mimetype:
        mimetype, _ = guess_type(path.name)
    return bool(mimetype and (mimetype.startswith("audio/") or mimetype.startswith("video/")))

########################################
#                                      #
#           MAIN FUNCTION!!!           #
#                                      #
########################################
async def transcribe_from_url(file_url: str, language: Optional[str] = None):
    temp_path, content_type = await _download_to_temp(file_url)
    try:
        if not _is_audio_video(temp_path, content_type):
            raise UnsupportedMediaError(f"Unsupported media type for {temp_path.name}")
        
        model = await _get_model
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            partial(model.transcribe, str(temp_path), language=language, fp16=False),
        )

        segments = [
            {
                "start": float(seg.get("start", 0.0)),
                "end": float(seg.get("end", 0.0)),
                "text": seg.get("text", "").strip(),
            }
            for seg in result.get("segments", [])
        ]
        
        return {
            "text": result.get("text", "").strip(),
            "segments": segments,
            "duration": float(result.get("duration", 0.0)),
        }
    finally:
        if temp_path.exists():
            os.remove(temp_path)