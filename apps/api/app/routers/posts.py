# apps/api/routes/posts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, AnyUrl, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import jwt

from ..services.supabase_client import get_supabase_client

router = APIRouter(prefix="/posts", tags=["Posts"])
bearer_scheme = HTTPBearer(auto_error=True)
# =========================
# Auth dependency
# =========================
class AuthUser(BaseModel):
    user_id: str
    access_token: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> AuthUser:
# def get_current_user(authorization: Optional[str] = Header(None)) -> AuthUser:
    """
    Extract user_id (sub) from Supabase JWT.
    Uses SUPABASE_JWT_SECRET (if set) for signature verification; otherwise decodes without verify.
    """
    # if not authorization or not authorization.lower().startswith("bearer "):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

    # token = authorization.split(" ", 1)[1].strip()
    token = credentials.credentials
    secret = os.getenv("JWT_SECRET")

    try:
        if secret:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        else:
            payload = jwt.decode(token, options={"verify_signature": False})

        sub = payload.get("sub") or payload.get("user_id")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")

        return AuthUser(user_id=sub, access_token=token)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# Pydantic models
# =========================
class PostCreate(BaseModel):
    caption: str = Field(..., max_length=2000, description="Post caption (max 2000 chars)")
    media_url: Optional[AnyUrl] = Field(None, description="Optional media URL")


class PostUpdate(BaseModel):
    caption: str = Field(..., max_length=2000, description="Updated caption (max 2000 chars)")


class AuthorInfo(BaseModel):
    user_id: str
    username: str
    profile_pic: Optional[AnyUrl] = None


class PostResponse(BaseModel):
    id: int
    user_id: str
    caption: str
    media_url: Optional[AnyUrl] = None
    created_at: datetime
    updated_at: datetime
    author: AuthorInfo


# =========================
# Helpers
# =========================
def _iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _row_to_post(row: Dict[str, Any]) -> PostResponse:
    profile = row.get("users") or {}
    return PostResponse(
        id=row["id"],
        user_id=row["user_id"],
        caption=row["caption"],
        media_url=row.get("media_url"),
        created_at=_iso_to_dt(row["created_at"]),
        updated_at=_iso_to_dt(row["updated_at"]),
        author=AuthorInfo(
            user_id=row["user_id"],
            username=profile.get("username", ""),
            profile_pic=profile.get("profile_pic"),
        ),
    )


def _rls_client(user_token: str):
    client = get_supabase_client()
    client.postgrest.auth(user_token)
    return client



# =========================
# Endpoints
# =========================
@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new post",
    description="Create a new post for the authenticated user. `caption` required, `media_url` optional.",
)
def create_post(payload: PostCreate, current: AuthUser = Depends(get_current_user)):
    db = _rls_client(current.access_token)

    data = {
        "user_id": current.user_id,
        "caption": payload.caption,
        "media_url": str(payload.media_url) if payload.media_url else None,
    }

    res = (
        db.table("posts")
        .insert(data)
        .select("*, users(username, profile_pic)")
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)

    return _row_to_post(res.data[0])


@router.get(
    "",
    response_model=List[PostResponse],
    summary="Get feed (paginated, latest first)",
    description="Returns posts ordered by created_at DESC. Supports `limit` and `offset`.",
)
def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: AuthUser = Depends(get_current_user),
):
    db = _rls_client(current.access_token)
    start, end = offset, offset + limit - 1

    res = (
        db.table("posts")
        .select("*, users(username, profile_pic)")
        .order("created_at", desc=True)
        .range(start, end)
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)

    rows = res.data or []
    return [_row_to_post(r) for r in rows]


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="Get a post by ID (with author)",
    description="Returns a specific post and the author's profile (username, avatar).",
)
def get_post_by_id(
    post_id: int = Path(..., ge=1),
    current: AuthUser = Depends(get_current_user),
):
    db = _rls_client(current.access_token)

    res = (
        db.table("posts")
        .select("*, users(username, profile_pic)")
        .eq("id", post_id)
        .single()
        .execute()
    )
    if getattr(res, "error", None):
        # Supabase Python client error message may contain "No rows"
        if res.error.message and "No rows" in res.error.message:
            raise HTTPException(status_code=404, detail="Post not found")
        raise HTTPException(status_code=400, detail=res.error.message)

    return _row_to_post(res.data)


@router.get(
    "/user/{user_id}",
    response_model=List[PostResponse],
    summary="Get posts by user (paginated)",
    description="Returns posts for a specific user ordered by created_at DESC.",
)
def get_posts_by_user(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: AuthUser = Depends(get_current_user),
):
    db = _rls_client(current.access_token)
    start, end = offset, offset + limit - 1

    res = (
        db.table("posts")
        .select("*, users(username, profile_pic)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(start, end)
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)

    return [_row_to_post(r) for r in (res.data or [])]


@router.put(
    "/{post_id}",
    response_model=PostResponse,
    summary="Update own post (caption only)",
    description="Updates the caption of your own post. Ownership is enforced by RLS; we also pre-check for quicker 403s.",
)
def update_post(
    post_id: int = Path(..., ge=1),
    payload: PostUpdate = ...,
    current: AuthUser = Depends(get_current_user),
):
    db = _rls_client(current.access_token)

    # Quick ownership check for better UX
    chk = db.table("posts").select("id, user_id").eq("id", post_id).single().execute()
    if getattr(chk, "error", None):
        if chk.error.message and "No rows" in chk.error.message:
            raise HTTPException(status_code=404, detail="Post not found")
    if chk.data["user_id"] != current.user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this post")

    res = (
        db.table("posts")
        .update({"caption": payload.caption})
        .eq("id", post_id)
        .select("*, users(username, profile_pic)")
        .single()
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)

    return _row_to_post(res.data)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own post",
    description="Deletes your own post. Associated comments/likes are removed via FK ON DELETE CASCADE.",
)
def delete_post(
    post_id: UUID4 = Path(..., description="UUID of the post to delete"),
    current: AuthUser = Depends(get_current_user),
):
    db = _rls_client(current.access_token)

    # Quick ownership check
    chk = db.table("posts").select("id, user_id").eq("id", post_id).single().execute()
    if getattr(chk, "error", None):
        if chk.error.message and "No rows" in chk.error.message:
            raise HTTPException(status_code=404, detail="Post not found")
        raise HTTPException(status_code=400, detail=chk.error.message)
    if chk.data["user_id"] != current.user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this post")

    res = db.table("posts").delete().eq("id", post_id).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    return
