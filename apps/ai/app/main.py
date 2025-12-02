# /root/apps/ai/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from app.services.gemini_moderation import is_image_unsafe
from app.services.whisper_service import (
    TranscribeRequest,
    TranscribeResponse,
    DownloadError,
    UnsupportedMediaError,
)
from app.services import whisper_service


app = FastAPI(
    title="AI Service",
    description="AI features: Transcription, Moderation, Summarization",
    version="1.1.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "ai"}


@app.get("/")
async def root():
    return {"message": "AI Service is running. See /docs for API documentation."}


@app.post("/moderation/image")
async def moderate_image(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed.",
        )

    image_bytes = await file.read()
    unsafe = is_image_unsafe(image_bytes=image_bytes, mime_type=file.content_type)
    return {"unsafe": unsafe}


@app.post("/transcribe", response_model=TranscribeResponse, summary="Transcribe audio/video via Whisper")
async def transcribe(payload: TranscribeRequest):
    """Transcribe Service
        Insert JSON"""
    try:
        result = await whisper_service.transcribe_from_url(
            file_url=str(payload.file_url),
            language=None if payload.language in (None, "", "string") else payload.language,
        )
        return result
    except UnsupportedMediaError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except DownloadError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
