# /root/apps/ai/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from app.services.gemini_moderation import is_image_unsafe  

app = FastAPI(
    title="AI Service",
    description="AI features: Transcription, Moderation, Summarization",
    version="1.0.0"
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
