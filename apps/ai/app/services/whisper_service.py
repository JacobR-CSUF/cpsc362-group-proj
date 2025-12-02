import asyncio, mimetypes

from app.core.config import settings

##################################
#         funny var box          #
################################## 
SUPPORTED_SUFFIXES = {".mp4", ".webm", ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".mpga", ".aac", ".opus"}
_model = None
_model_lock = asyncio.Lock()

