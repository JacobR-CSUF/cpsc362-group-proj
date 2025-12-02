import asyncio, mimetypes, whisper

from app.core.config import settings

##################################
#         funny var box          #
################################## 
SUPPORTED_SUFFIXES = {".mp4", ".webm", ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".mpga", ".aac", ".opus"}
_model = None
_model_lock = asyncio.Lock()

async def _get_model():
    global _model
    if _model is None:
        async with _model_lock:
            if _model is None:
                _model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
    return _model
