# apps/api/routes/posts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, AnyUrl, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.supabase_client import get_supabase_client
from ..dependencies import get_current_user as require_user  # reuse auth

router = APIRouter(prefix="/posts", tags=["Posts"])
bearer_scheme = HTTPBearer(auto_error=True)                  # extract header token
SELECT_FIELDS = "*, users(username, profile_pic), media(url)"

# ---------- models ----------
from pydantic import BaseModel, Field, AnyUrl
from typing import Optional
from datetime import datetime

# prepare validator 
try:
    from pydantic import model_validator  # v2
    _P2 = True
except Exception:
    from pydantic import root_validator as _root_validator  # v1
    _P2 = False

class PostCreate(BaseModel):
    caption: str = Field(..., max_length=2000)
    media_url: Optional[AnyUrl] = None    


class PostUpdate(BaseModel):
    caption: str = Field(..., max_length=2000)

class AuthUser(BaseModel):
    user_id: str
    access_token: str

class AuthorInfo(BaseModel):
    user_id: str
    username: str
    profile_pic: Optional[AnyUrl] = None

class PostResponse(BaseModel):
    id: UUID4
    user_id: str
    caption: str
    media_id: Optional[UUID4] = None
    media_url: Optional[AnyUrl] = None
    created_at: datetime
    author: AuthorInfo


# ---------- helpers ----------
def _as_obj(v) -> Dict[str, Any]:
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        return v[0] if v else {}
    return {}

def _iso_to_dt(value):
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.fromisoformat("1970-01-01T00:00:00+00:00")
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _row_to_post(row: Dict[str, Any]) -> PostResponse:
    profile = _as_obj(row.get("users"))   
    media   = _as_obj(row.get("media")) 
    return PostResponse(
        id=row["id"],                      # UUID4
        user_id=row["user_id"],
        caption=row["caption"],
        media_id=row.get("media_id"),      # UUID4 or None
        media_url=media.get("url"),        # dict or list 
        created_at=_iso_to_dt(row.get("created_at")),
        author=AuthorInfo(
            user_id=row["user_id"],
            username=profile.get("username", ""),
            profile_pic=profile.get("profile_pic"),
        ),
    )

def _rls_client(user_token: str):
    client = get_supabase_client()
    client.postgrest.auth(user_token)  # Use user token 
    return client


def current_auth(
    user: dict = Depends(require_user),                                      # Only valid user in DB
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),            # access_token in header
) -> AuthUser:
    return AuthUser(user_id=user["id"], access_token=cred.credentials)

# ---------- endpoints ----------
@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, current: AuthUser = Depends(current_auth)):
    db = _rls_client(current.access_token)

    media_id = None
    if payload.media_url:
        insm = db.table("media").insert({
            "user_id": current.user_id,
            "url": str(payload.media_url),
        }).execute()
        if getattr(insm, "error", None):
            raise HTTPException(status_code=400, detail=insm.error.message)
        media_id = insm.data[0]["id"]

    ins = db.table("posts").insert({
        "user_id": current.user_id,
        "caption": payload.caption,
        "media_id": media_id,    # None -> NULL
    }).execute()
    if getattr(ins, "error", None):
        raise HTTPException(status_code=400, detail=ins.error.message)
    post_id = ins.data[0]["id"]

    res = db.table("posts").select(SELECT_FIELDS).eq("id", post_id).single().execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    return _row_to_post(res.data)



@router.get("", response_model=List[PostResponse])
def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: AuthUser = Depends(current_auth),
):
    db = _rls_client(current.access_token)
    res = (db.table("posts")
        .select(SELECT_FIELDS)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute())
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    return [_row_to_post(r) for r in (res.data or [])]

@router.get("/{post_id}", response_model=PostResponse)
def get_post_by_id(post_id: UUID4, current: AuthUser = Depends(current_auth)):
    db = _rls_client(current.access_token)
    res = db.table("posts").select(SELECT_FIELDS).eq("id", str(post_id)).limit(1).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Post not found")
    return _row_to_post(rows[0])

@router.get("/user/{user_id}", response_model=List[PostResponse])
def get_posts_by_user(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current: AuthUser = Depends(current_auth),
):
    db = _rls_client(current.access_token)
    res = (
        db.table("posts")
        .select(SELECT_FIELDS)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=400, detail=res.error.message)
    return [_row_to_post(r) for r in (res.data or [])]

@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: UUID4,
    payload: PostUpdate = ...,
    current: AuthUser = Depends(current_auth),
):
    db = _rls_client(current.access_token)

    chk = db.table("posts").select("id, user_id").eq("id", post_id).single().execute()
    if getattr(chk, "error", None):
        if chk.error.message and "No rows" in chk.error.message:
            raise HTTPException(status_code=404, detail="Post not found")
        raise HTTPException(status_code=400, detail=chk.error.message)
    if chk.data["user_id"] != current.user_id:
        raise HTTPException(status_code=403, detail="Not the owner of this post")

    # 1) UPDATE
    upd = db.table("posts").update({"caption": payload.caption}).eq("id", post_id).execute()
    if getattr(upd, "error", None):
        raise HTTPException(status_code=400, detail=upd.error.message)

    # 2) organize final response using SELECT join
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


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: UUID4, current: AuthUser = Depends(current_auth)):
    db = _rls_client(current.access_token)
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
