# apps/api/routes/posts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, AnyUrl, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..utils.pagination import (
    PaginatedResponse,
    normalize_page_limit,
    page_to_range,
    build_paginated_response,
)

from ..services.supabase_client import get_supabase_client, get_rls_client
from ..dependencies import get_current_user as require_user

router = APIRouter(prefix="/posts", tags=["Posts"])
bearer_scheme = HTTPBearer(auto_error=True)
SELECT_FIELDS = "*, users(username, profile_pic), media(id, public_url, media_type, caption, transcription_url)"

# ---------- Pydantic Models ----------

class PostCreate(BaseModel):
    caption: str = Field(..., max_length=2000)
    media_id: Optional[UUID4] = None  # Reference to pre-uploaded media

class PostUpdate(BaseModel):
    caption: str = Field(..., max_length=2000)

class AuthUser(BaseModel):
    user_id: str
    access_token: str

class AuthorInfo(BaseModel):
    user_id: str
    username: str
    profile_pic: Optional[AnyUrl] = None

class MediaInfo(BaseModel):
    """Media information matching the actual schema"""
    id: UUID4
    public_url: str
    media_type: Optional[str] = None  # 'image' | 'video'
    caption: Optional[str] = None
    transcription_url: Optional[str] = None

class PostResponse(BaseModel):
    id: UUID4
    user_id: str
    caption: str
    media_id: Optional[UUID4] = None
    has_media: bool
    visibility: Optional[str] = "public"  # 'public' | 'private' | 'followers'
    created_at: datetime
    author: AuthorInfo
    media: Optional[MediaInfo] = None  # Full media object if present


# ---------- Helper Functions ----------

def _as_obj(v) -> Dict[str, Any]:
    """Convert list or dict to dict object"""
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        return v[0] if v else {}
    return {}

def _iso_to_dt(value):
    """Convert ISO string to datetime"""
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.fromisoformat("1970-01-01T00:00:00+00:00")
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

def _row_to_post(row: Dict[str, Any]) -> PostResponse:
    """Convert database row to PostResponse"""
    profile = _as_obj(row.get("users"))
    media_data = _as_obj(row.get("media"))
    
    # Build media info if present
    media_info = None
    if media_data and media_data.get("id"):
        media_info = MediaInfo(
            id=media_data["id"],
            public_url=media_data.get("public_url") or "",  
            media_type=media_data.get("media_type"),
            caption=media_data.get("caption"),
            transcription_url=media_data.get("transcription_url"),
        )
    
    return PostResponse(
        id=row["id"],
        user_id=row["user_id"],
        caption=row.get("caption", ""),
        media_id=row.get("media_id"),
        has_media=bool(row.get("media_id")),
        visibility=row.get("visibility", "public"),
        created_at=_iso_to_dt(row.get("created_at")),
        author=AuthorInfo(
            user_id=row["user_id"],
            username=profile.get("username", ""),
            profile_pic=profile.get("profile_pic"),
        ),
        media=media_info
    )

def _rls_client(user_token: str):
    """Get Supabase client with RLS using user token"""
    return get_rls_client(user_token)

def current_auth(
    user: dict = Depends(require_user),
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> AuthUser:
    """Extract current authenticated user"""
    return AuthUser(user_id=user["id"], access_token=cred.credentials)


# ---------- Endpoints ----------

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, current: AuthUser = Depends(current_auth)):
    """
    Create a new post with optional media
    
    - Validates media_id exists and belongs to current user
    - Sets has_media flag automatically
    """
    db = _rls_client(current.access_token)
    
    # Validate media ownership if media_id provided
    if payload.media_id:
        media_check = (
            db.table("media")
            .select("id, uploaded_by")
            .eq("id", str(payload.media_id))
            .execute()
        )
        
        if getattr(media_check, "error", None):
            raise HTTPException(
                status_code=400, 
                detail=f"Media validation error: {media_check.error.message}"
            )
        
        if not media_check.data:
            raise HTTPException(
                status_code=404,
                detail="Media not found"
            )
        
        media = media_check.data[0]
        if media["uploaded_by"] != current.user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot use media uploaded by another user"
            )
    
    # Create post
    post_data = {
        "user_id": current.user_id,
        "caption": payload.caption,
        "media_id": str(payload.media_id) if payload.media_id else None,
        "visibility": "public"  # Default visibility
    }
    
    ins = db.table("posts").insert(post_data).execute()
    
    if getattr(ins, "error", None):
        raise HTTPException(status_code=400, detail=ins.error.message)
    
    post_id = ins.data[0]["id"]
    
    # Fetch complete post with joins
    res = (
        db.table("posts")
        .select(SELECT_FIELDS)
        .eq("id", post_id)
        .single()
        .execute()
    )
    
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    
    return _row_to_post(res.data)


@router.get("", response_model=PaginatedResponse[PostResponse])
def get_feed(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    has_media: Optional[bool] = Query(None, description="Filter by media presence"),
    current: AuthUser = Depends(current_auth),
):
    """
    Get feed of posts
    
    - Optional filtering by has_media
    - Includes author and media information
    - Respects RLS and visibility rules
    """
    db = _rls_client(current.access_token)

    # Normalize page + limit
    page, limit = normalize_page_limit(page, limit)
    start, end = page_to_range(page, limit)

    # Total count
    count_q = db.table("posts").select("id", count="exact")
    if has_media is True:
        # posts that have media (media_id IS NOT NULL)
        count_q = count_q.not_.is_("media_id", "null")
    elif has_media is False:
        # posts that do NOT have media (media_id IS NULL)
        count_q = count_q.is_("media_id", "null")
    count_res = count_q.execute()
    total_count = int(count_res.count or 0)

    # Fetch paginated rows
    query = (
        db.table("posts")
        .select(SELECT_FIELDS)
        .order("created_at", desc=True)
        .range(start, end)
    )
    if has_media is True:
        query = query.not_.is_("media_id", "null")
    elif has_media is False:
        query = query.is_("media_id", "null")

    res = query.execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)

    posts = [_row_to_post(r) for r in (res.data or [])]

    return build_paginated_response(
        items=posts,
        total_count=total_count,
        page=page,
        limit=limit,
        request=request,
    )


@router.get("/{post_id}", response_model=PostResponse)
def get_post_by_id(post_id: UUID4, current: AuthUser = Depends(current_auth)):
    """Get a single post by ID with media information"""
    db = _rls_client(current.access_token)
    
    res = (
        db.table("posts")
        .select(SELECT_FIELDS)
        .eq("id", str(post_id))
        .limit(1)
        .execute()
    )
    
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return _row_to_post(rows[0])


@router.get("/user/{user_id}", response_model=PaginatedResponse[PostResponse])
def get_posts_by_user(
    user_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    has_media: Optional[bool] = Query(None, description="Filter by media presence"),
    current: AuthUser = Depends(current_auth),
):
    """Get posts by specific user with optional media filter"""
    db = _rls_client(current.access_token)

    # Normalize + compute range
    page, limit = normalize_page_limit(page, limit)
    start, end = page_to_range(page, limit)

    # Total count
    count_q = (
        db.table("posts")
        .select("id", count="exact")
        .eq("user_id", user_id)
    )
    if has_media is True:
        count_q = count_q.not_.is_("media_id", "null")
    elif has_media is False:
        count_q = count_q.is_("media_id", "null")

    count_res = count_q.execute()
    total_count = int(count_res.count or 0)

    # Page slice
    query = (
        db.table("posts")
        .select(SELECT_FIELDS)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(start, end)
    )
    if has_media is not None:
        query = query.eq("has_media", has_media)

    if has_media is True:
        query = query.not_.is_("media_id", "null")
    elif has_media is False:
        query = query.is_("media_id", "null")
        
    res = query.execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)

    posts = [_row_to_post(r) for r in (res.data or [])]

    return build_paginated_response(
        items=posts,
        total_count=total_count,
        page=page,
        limit=limit,
        request=request,
    )


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: UUID4,
    payload: PostUpdate,
    current: AuthUser = Depends(current_auth),
):
    """Update post caption (media cannot be changed after creation)"""
    db = _rls_client(current.access_token)
    
    # Check ownership
    chk = (
        db.table("posts")
        .select("id, user_id")
        .eq("id", str(post_id))
        .single()
        .execute()
    )
    
    if getattr(chk, "error", None):
        if chk.error.message and "No rows" in chk.error.message:
            raise HTTPException(status_code=404, detail="Post not found")
        raise HTTPException(status_code=400, detail=chk.error.message)
    
    if chk.data["user_id"] != current.user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this post")
    
    # Update caption
    upd = (
        db.table("posts")
        .update({"caption": payload.caption})
        .eq("id", str(post_id))
        .execute()
    )
    
    if getattr(upd, "error", None):
        raise HTTPException(status_code=400, detail=upd.error.message)
    
    # Fetch updated post with joins
    res = (
        db.table("posts")
        .select(SELECT_FIELDS)
        .eq("id", str(post_id))
        .single()
        .execute()
    )
    
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    
    return _row_to_post(res.data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: UUID4,
    delete_media: bool = Query(False, description="Also delete associated media file"),
    current: AuthUser = Depends(current_auth)
):
    """
    Delete a post
    
    - delete_media=true: Also deletes the associated media file and record
    - delete_media=false (default): Only deletes the post, keeps media
    """
    db = _rls_client(current.access_token)
    
    # Check ownership and get media_id
    chk = (
        db.table("posts")
        .select("id, user_id, media_id")
        .eq("id", str(post_id))
        .single()
        .execute()
    )
    
    if getattr(chk, "error", None):
        if chk.error.message and "No rows" in chk.error.message:
            raise HTTPException(status_code=404, detail="Post not found")
        raise HTTPException(status_code=400, detail=chk.error.message)
    
    if chk.data["user_id"] != current.user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this post")
    
    media_id = chk.data.get("media_id")
    
    # Delete post first
    res = db.table("posts").delete().eq("id", str(post_id)).execute()
    
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    
    # Optionally delete media
    if delete_media and media_id:
        try:
            # Get media details for MinIO deletion
            media_res = (
                db.table("media")
                .select("public_url, uploaded_by")
                .eq("id", str(media_id))
                .single()
                .execute()
            )
            
            if media_res.data:
                # Verify user still owns the media
                if media_res.data["uploaded_by"] == current.user_id:
                    # Extract filename from URL for MinIO deletion
                    url = media_res.data["public_url"]
                    filename = url.split("/")[-1] if "/" in url else url
                    
                    # Delete from MinIO
                    try:
                        from ..services.minio_client import get_minio_service
                        minio_service = get_minio_service()
                        minio_service.delete_file(filename)
                    except Exception as minio_err:
                        print(f"Warning: Failed to delete from MinIO: {minio_err}")
                    
                    # Delete from database
                    db.table("media").delete().eq("id", str(media_id)).execute()
        except Exception as e:
            # Log error but don't fail the post deletion
            print(f"Warning: Failed to delete media: {e}")
    
    return None
