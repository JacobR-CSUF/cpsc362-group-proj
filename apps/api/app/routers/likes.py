from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, UUID4
from typing import List, Optional, Dict, Any
import os, jwt

from ..services.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/v1", tags=["likes"])
bearer_scheme = HTTPBearer(auto_error=True)

# ---------- Schemas ----------
class LikeToggleResponse(BaseModel):
    post_id: UUID4
    liked: bool
    count: int

class LikeStatusResponse(BaseModel):
    post_id: UUID4
    count: int
    liked_by_me: bool

class LikedUser(BaseModel):
    user_id: UUID4
    username: Optional[str] = None
    profile_pic: Optional[str] = None
    liked_at: str

class LikedUsersResponse(BaseModel):
    post_id: UUID4
    total: int
    users: List[LikedUser]

class AuthUser(BaseModel):
    user_id: str
    access_token: str

# ---------- Local auth ----------
def current_auth(cred: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> AuthUser:
    token = cred.credentials
    secret = os.getenv("JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
    try:
        # Supabase basic aud = "authenticated"
        payload = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    except jwt.InvalidAudienceError:
        payload = jwt.decode(token, secret, algorithms=["HS256"])

    sub = payload.get("sub") or payload.get("user_id")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")

    return AuthUser(user_id=sub, access_token=token)

# ---------- Helpers ----------
def _rls_client(user_token: str):
    client = get_supabase_client()
    client.postgrest.auth(user_token)  
    return client

def _ensure_post_exists(client, post_id: str):
    res = client.table("posts").select("id").eq("id", post_id).limit(1).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    if not (res.data or []):
        raise HTTPException(status_code=404, detail="Post not found")

def _count_likes(client, post_id: str) -> int:
    res = client.table("likes").select("id", count="exact").eq("post_id", post_id).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    return int(res.count or 0)

def _liked_by(client, post_id: str, user_id: str) -> bool:
    res = client.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).limit(1).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    return bool(res.data)

# ---------- Endpoints ----------
@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse)
def toggle_like(post_id: UUID4, current: AuthUser = Depends(current_auth)):
    db = _rls_client(current.access_token)
    _ensure_post_exists(db, str(post_id))

    existed = (
        db.table("likes")
          .select("id")
          .match({"post_id": str(post_id), "user_id": current.user_id})
          .limit(1).execute()
    )
    if getattr(existed, "error", None):
        raise HTTPException(status_code=400, detail=existed.error.message)

    if existed.data:
        res = db.table("likes").delete().match({"post_id": str(post_id), "user_id": current.user_id}).execute()
        if getattr(res, "error", None):
            raise HTTPException(status_code=400, detail=res.error.message)
        liked = False
    else:
        res = db.table("likes").insert({"post_id": str(post_id), "user_id": current.user_id}).execute()
        if getattr(res, "error", None):
            raise HTTPException(status_code=400, detail=res.error.message)
        liked = True

    count = _count_likes(db, str(post_id))
    return LikeToggleResponse(post_id=post_id, liked=liked, count=count)

@router.get("/posts/{post_id}/likes", response_model=LikeStatusResponse)
def get_like_status(post_id: UUID4, current: AuthUser = Depends(current_auth)):
    db = _rls_client(current.access_token)
    _ensure_post_exists(db, str(post_id))
    return LikeStatusResponse(
        post_id=post_id,
        count=_count_likes(db, str(post_id)),
        liked_by_me=_liked_by(db, str(post_id), current.user_id)
    )

@router.get("/posts/{post_id}/likes/users", response_model=LikedUsersResponse)
def list_liked_users(
    post_id: UUID4,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: AuthUser = Depends(current_auth),
):
    db = _rls_client(current.access_token)
    _ensure_post_exists(db, str(post_id))

    total_resp = db.table("likes").select("id", count="exact").eq("post_id", str(post_id)).execute()
    if getattr(total_resp, "error", None):
        raise HTTPException(status_code=400, detail=total_resp.error.message)
    total = int(total_resp.count or 0)

    resp = (
        db.table("likes")
          .select("user_id, created_at, users(id,username,profile_pic)")
          .eq("post_id", str(post_id))
          .order("created_at", desc=True)
          .range(offset, offset + limit - 1)
          .execute()
    )
    if getattr(resp, "error", None):
        raise HTTPException(status_code=400, detail=resp.error.message)

    users: List[LikedUser] = []
    for row in resp.data or []:
        prof = row.get("users") or {}
        if isinstance(prof, list):
            prof = prof[0] if prof else {}
        users.append(
            LikedUser(
                user_id=(prof.get("id") or row["user_id"]),
                username=prof.get("username"),
                profile_pic=prof.get("profile_pic"),
                liked_at=row["created_at"],
            )
        )
    return LikedUsersResponse(post_id=post_id, total=total, users=users)
