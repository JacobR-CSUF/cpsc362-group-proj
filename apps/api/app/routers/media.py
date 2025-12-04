"""
Media Upload Router
Handles file uploads to MinIO with Supabase fallback
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import os
from pathlib import Path

from ..services.supabase_client import SupabaseClient
from ..services.minio_client import get_minio_service
from ..dependencies import get_current_user

router = APIRouter(prefix="/media", tags=["media"])

# Configuration
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-matroska"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".mkv"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB

# Pydantic Models
class MediaMetadata(BaseModel):
    id: str
    filename: str
    original_filename: str
    size: int
    mime_type: str
    media_type: str
    public_url: str
    uploaded_by: str
    caption: Optional[str] = None
    created_at: Optional[datetime] = None 

class MediaUploadResponse(BaseModel):
    success: bool
    data: MediaMetadata
    message: str

def validate_file_type(filename: str, content_type: str) -> tuple[bool, str]:
    """Validate file type based on extension and MIME type"""
    file_ext = Path(filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {file_ext} not allowed"

    if content_type in ALLOWED_IMAGE_TYPES:
        return True, "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        return True, "video"
    else:
        return False, f"MIME type {content_type} not allowed"

def validate_file_size(file_size: int, media_type: str) -> tuple[bool, str]:
    """Validate file size based on media type"""
    if media_type == "image" and file_size > MAX_IMAGE_SIZE:
        return False, f"Image size exceeds {MAX_IMAGE_SIZE // (1024*1024)}MB limit"
    elif media_type == "video" and file_size > MAX_VIDEO_SIZE:
        return False, f"Video size exceeds {MAX_VIDEO_SIZE // (1024*1024)}MB limit"
    return True, ""

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename using UUID to prevent collisions"""
    file_ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid4())
    return f"{unique_id}{file_ext}"


# AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai:8002")

# async def check_image_unsafe_with_ai(
#     file_content: bytes,
#     filename: str,
#     content_type: str,
# ) -> bool:
#     """
#     Call AI moderation service → Return True when image is unsafe.
#     """
#     if not AI_SERVICE_URL:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail="Image moderation service is not configured.",
#         )

#     try:
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.post(
#                 f"{AI_SERVICE_URL}/moderation/image",
#                 files={"file": (filename, file_content, content_type)},
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"Failed to contact AI moderation service: {str(e)}",
#         )

#     if resp.status_code != 200:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"AI moderation service error: {resp.text}",
#         )

#     data = resp.json()
#     return bool(data.get("unsafe", False))


@router.post("/upload",
             response_model=MediaUploadResponse,
             status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload image or video file to MinIO storage"""
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file type
        is_valid, media_type_or_error = validate_file_type(file.filename, file.content_type)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=media_type_or_error
            )

        media_type = media_type_or_error

        # Validate file size
        is_valid_size, size_error = validate_file_size(file_size, media_type)
        if not is_valid_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=size_error
            )

        # AI Moderation for images (need to review)
        # if media_type == "image":
        #     unsafe = await check_image_unsafe_with_ai(
        #         file_content=file_content,
        #         filename=file.filename,
        #         content_type=file.content_type,
        #     )
        #     if unsafe:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail="Blocked upload: Image contains unsafe content.",
        #         )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)

        # Upload to MinIO
        minio_service = get_minio_service()
        public_url = minio_service.upload_file_bytes(
            file_content,
            unique_filename,
            file.content_type
        )

        # Store metadata in database
        media_id = str(uuid4())
        media_data = {
            "id": media_id,
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": file_size,
            "mime_type": file.content_type,
            "media_type": media_type,
            "public_url": public_url,
            "uploaded_by": current_user["id"],
            "caption": caption
        }

        # Insert into database using Supabase client
        response = SupabaseClient.insert("media", media_data)

        if not response or "error" in response:
            # Rollback: Delete file from MinIO if database insert fails
            try:
                minio_service.delete_file(unique_filename)
            except:
                pass

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save media metadata"
            )

        saved_media = response["data"][0] if response.get("data") else media_data

        return MediaUploadResponse(
            success=True,
            data=MediaMetadata(**saved_media),
            message="File uploaded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
    finally:
        await file.close()

@router.get("/{file_id}", response_model=MediaMetadata)
async def get_media(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get media details by ID"""
    try:
        # Use query method with proper filters
        result = SupabaseClient.query(
            "media",
            columns="*",
            id=file_id  # Pass as keyword argument for filtering
        )

        if not result or len(result) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )

        media = result[0]  # Get first (and only) result

        # Check if user has permission to view
        if media["uploaded_by"] != current_user["id"]:
            # Optional: Add logic for public/private media
            pass  # For now, allow all authenticated users to view

        return MediaMetadata(
            id=media["id"],
            filename=media["filename"],
            original_filename=media["original_filename"],
            size=media["size"],
            mime_type=media["mime_type"],
            media_type=media["media_type"],
            public_url=media["public_url"],
            uploaded_by=media["uploaded_by"],
            caption=media.get("caption"),
            created_at=media.get("created_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch media: {str(e)}"
        )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete media file"""
    try:
        # First, get the media to check ownership and get filename
        # Use query() instead of select()
        result = SupabaseClient.query(
            "media",
            id=file_id  # Filter by ID
        )

        if not result or len(result) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )

        media = result[0]

        # Check ownership
        if media["uploaded_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this media"
            )

        # Delete from MinIO
        minio_service = get_minio_service()
        try:
            minio_service.delete_file(media["filename"])
        except Exception as e:
            print(f"Warning: Failed to delete from MinIO: {e}")
            # Continue anyway - database record is more important

        # Delete from database
        SupabaseClient.delete("media", id=file_id)

        # Return 204 No Content (automatically handled by status_code)
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )

