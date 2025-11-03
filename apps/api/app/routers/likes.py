from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel, UUID4
from apps.api.app.services.supabase_client import get_supabase_client
from apps.api.app.dependencies import get_current_user 

router = APIRouter(prefix="/api/v1", tags=["likes"])

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
    username: str | None = None
    avatar_url: str | None = None
    liked_at: str

class LikedUsersResponse(BaseModel):
    post_id: UUID4
    total: int
    users: list[LikedUser]

# ---------- Helpers ----------
def _ensure_post_exists(client, post_id: str):
    res = client.table("posts").select("id").eq("id", post_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Post not found")

def _count_likes(client, post_id: str) -> int:
    # supabase-py v2: use select("*", count='exact') to get count
    res = client.table("likes").select("id", count="exact").eq("post_id", post_id).execute()
    return int(res.count or 0)

def _liked_by(client, post_id: str, user_id: str) -> bool:
    res = client.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).limit(1).execute()
    return bool(res.data)

# ---------- Endpoints ----------
@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse, status_code=200)
def toggle_like(
    post_id: UUID4 = Path(...),
    user = Depends(get_current_user),
):
    client = get_supabase_client()
    _ensure_post_exists(client, str(post_id))

    # remove if it's already existing or insert 
    existed = client.table("likes").select("id").match({"post_id": str(post_id), "user_id": user.user_id}).limit(1).execute()
    if existed.data:
        # unlike
        client.table("likes").delete().match({"post_id": str(post_id), "user_id": user.user_id}).execute()
        liked = False
    else:
        # like (avoid duplication with setting unique)
        client.table("likes").insert({"post_id": str(post_id), "user_id": user.user_id}).execute()
        liked = True

    # count (read posts.like_count if using trigger)
    count = _count_likes(client, str(post_id))
    return LikeToggleResponse(post_id=post_id, liked=liked, count=count)

@router.get("/posts/{post_id}/likes", response_model=LikeStatusResponse)
def get_like_status(
    post_id: UUID4 = Path(...),
    user = Depends(get_current_user),
):
    client = get_supabase_client()
    _ensure_post_exists(client, str(post_id))
    count = _count_likes(client, str(post_id))
    liked = _liked_by(client, str(post_id), user.user_id)
    return LikeStatusResponse(post_id=post_id, count=count, liked_by_me=liked)

@router.get("/posts/{post_id}/likes/users", response_model=LikedUsersResponse)
def list_liked_users(
    post_id: UUID4 = Path(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    client = get_supabase_client()
    _ensure_post_exists(client, str(post_id))

    # total sum
    total_resp = client.table("likes").select("id", count="exact").eq("post_id", str(post_id)).execute()
    total = int(total_resp.count or 0)

    # join user list (users_profile)
    # PostgREST embed: select("user_id, created_at, users_profile(username,avatar_url)")
    resp = (
        client.table("likes")
        .select("user_id, created_at, users_profile!inner(username,avatar_url)")
        .eq("post_id", str(post_id))
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    users: list[LikedUser] = []
    for row in resp.data or []:
        prof = row.get("users_profile") or {}
        users.append(
            LikedUser(
                user_id=row["user_id"],
                username=prof.get("username"),
                avatar_url=prof.get("avatar_url"),
                liked_at=row["created_at"],
            )
        )
    return LikedUsersResponse(post_id=post_id, total=total, users=users)
