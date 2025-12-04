"""
Comments CRUD Endpoints
Handles comment operations on posts with authentication and authorization
Implements soft delete pattern with deleted_at timestamp
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from ..services.supabase_client import get_supabase_client
from ..dependencies import get_current_user
from ..utils.pagination import (
    PaginatedResponse,
    normalize_page_limit,
    page_to_range,
    build_paginated_response,
)


router = APIRouter(prefix="/comments", tags=["comments"])


# Pydantic Models
class CommentCreateRequest(BaseModel):
    """Request model for creating a comment"""
    content: str = Field(..., min_length=1, max_length=500)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate comment content is not just whitespace"""
        if not v.strip():
            raise ValueError('Comment content cannot be empty or just whitespace')
        return v.strip()


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment"""
    content: str = Field(..., min_length=1, max_length=500)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate comment content is not just whitespace"""
        if not v.strip():
            raise ValueError('Comment content cannot be empty or just whitespace')
        return v.strip()


class CommentAuthor(BaseModel):
    """Author information for a comment"""
    id: str
    username: str
    profile_pic: Optional[str] = None


class CommentResponse(BaseModel):
    """Comment response model with author information"""
    id: str
    post_id: str
    content: str
    author: CommentAuthor
    created_at: datetime
    updated_at: datetime


# class CommentsListResponse(BaseModel):
#     """Paginated list of comments"""
#     success: bool
#     data: List[CommentResponse]
#     total: int
#     page: int
#     page_size: int
#     has_next: bool


class CommentSingleResponse(BaseModel):
    """Single comment response wrapper"""
    success: bool
    data: CommentResponse
    message: Optional[str] = None


# Helper Functions
async def get_post_by_id(post_id: str) -> Optional[dict]:
    """Check if a post exists"""
    try:
        UUID(post_id)
        client = get_supabase_client()
        response = client.table("posts").select("id").eq("id", post_id).execute()
        return response.data[0] if response.data else None
    except (ValueError, Exception):
        return None


async def get_comment_with_author(comment_id: str) -> Optional[dict]:
    """Fetch comment with author information (excluding soft-deleted)"""
    try:
        client = get_supabase_client()
        response = client.table("comments").select(
            "*, users:user_id(id, username, profile_pic)"
        ).eq("id", comment_id).is_("deleted_at", "null").execute()
        
        if not response.data:
            return None
            
        return response.data[0]
    except Exception:
        return None


async def verify_comment_ownership(comment_id: str, user_id: str) -> bool:
    try:
        client = get_supabase_client()
        response = client.table("comments").select("user_id").eq(
            "id", comment_id
        ).is_("deleted_at", "null").execute()
        
        if not response.data:
            return False
            
        return response.data[0]["user_id"] == user_id
    except Exception:
        return False


# Endpoints
@router.post("/posts/{post_id}/comments", 
             response_model=CommentSingleResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: str,
    comment_data: CommentCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new comment on a post
    
    Protected endpoint - requires authentication
    """
    try:
        try:
            UUID(post_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid post ID format"
            )
        
        post = await get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found"
            )
        
        client = get_supabase_client()
        comment_insert = {
            "post_id": post_id,
            "user_id": current_user["id"],
            "content": comment_data.content
        }
        
        response = client.table("comments").insert(comment_insert).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create comment"
            )
        
        comment_with_author = await get_comment_with_author(response.data[0]["id"])
        
        comment_response = CommentResponse(
            id=str(comment_with_author["id"]),
            post_id=str(comment_with_author["post_id"]),
            content=comment_with_author["content"],
            author=CommentAuthor(
                id=str(comment_with_author["users"]["id"]),
                username=comment_with_author["users"]["username"],
                profile_pic=comment_with_author["users"].get("profile_pic")
            ),
            created_at=comment_with_author["created_at"],
            updated_at=comment_with_author["updated_at"]
        )
        
        return CommentSingleResponse(
            success=True,
            data=comment_response,
            message="Comment created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get(
    "/posts/{post_id}/comments",
    response_model=PaginatedResponse[CommentResponse],
    status_code=status.HTTP_200_OK
)
async def get_post_comments(
    post_id: str,
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, le=100, description="Number of comments per page"),
):
    """
    Get all comments for a post (paginated, ordered chronologically)
    
    Public endpoint - no authentication required
    Comments are ordered by created_at ASC (oldest first)
    """
    # -------- validate post id --------
    try:
        try:
            UUID(post_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid post ID format"
            )

        post = await get_post_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found"
            )

        # -------- normalize page + limit --------
        page, limit = normalize_page_limit(page, limit)
        start, end = page_to_range(page, limit)

        client = get_supabase_client()

        # -------- total count --------
        count_response = (
            client
            .table("comments")
            .select("id", count="exact")
            .eq("post_id", post_id)
            .is_("deleted_at", "null")
            .execute()
        )

        total_count = int(count_response.count or 0)

        # -------- fetch paginated slice --------
        response = (
            client.table("comments")
            .select("*, users:user_id(id, username, profile_pic)")
            .eq("post_id", post_id)
            .is_("deleted_at", "null")
            .order("created_at", desc=False)
            .range(start, end)
            .execute()
        )

        comments = []
        for c in response.data or []:
            comments.append(
                CommentResponse(
                    id=str(c["id"]),
                    post_id=str(c["post_id"]),
                    content=c["content"],
                    author=CommentAuthor(
                        id=str(c["users"]["id"]),
                        username=c["users"]["username"],
                        profile_pic=c["users"].get("profile_pic")
                    ),
                    created_at=c["created_at"],
                    updated_at=c["updated_at"],
                )
            )

        # -------- build standard paginated response --------
        return build_paginated_response(
            items=comments,
            total_count=total_count,
            page=page,
            limit=limit,
            request=request,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch comments: {str(e)}"
        )


@router.put("/{comment_id}",
            response_model=CommentSingleResponse,
            status_code=status.HTTP_200_OK)
async def update_comment(
    comment_id: str,
    update_data: CommentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a comment (users can only edit their own comments)
    
    Protected endpoint - requires authentication
    """
    try:
        try:
            UUID(comment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid comment ID format"
            )
        
        comment = await get_comment_with_author(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with ID {comment_id} not found"
            )
        
        is_owner = await verify_comment_ownership(comment_id, current_user["id"])
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments"
            )
        
        client = get_supabase_client()
        response = client.table("comments").update(
            {"content": update_data.content}
        ).eq("id", comment_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update comment"
            )
        
        updated_comment = await get_comment_with_author(comment_id)
        
        comment_response = CommentResponse(
            id=str(updated_comment["id"]),
            post_id=str(updated_comment["post_id"]),
            content=updated_comment["content"],
            author=CommentAuthor(
                id=str(updated_comment["users"]["id"]),
                username=updated_comment["users"]["username"],
                profile_pic=updated_comment["users"].get("profile_pic")
            ),
            created_at=updated_comment["created_at"],
            updated_at=updated_comment["updated_at"]
        )
        
        return CommentSingleResponse(
            success=True,
            data=comment_response,
            message="Comment updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update comment: {str(e)}"
        )


@router.delete("/{comment_id}",
               status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a comment (soft delete - sets deleted_at timestamp)
    Users can only delete their own comments
    
    Protected endpoint - requires authentication
    """
    try:
        try:
            UUID(comment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid comment ID format"
            )
        
        comment = await get_comment_with_author(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with ID {comment_id} not found"
            )
        
        is_owner = await verify_comment_ownership(comment_id, current_user["id"])
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )
        
        client = get_supabase_client()
        response = client.table("comments").update(
            {"deleted_at": datetime.utcnow().isoformat()}
        ).eq("id", comment_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete comment"
            )
        
        return {
            "success": True,
            "message": "Comment deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete comment: {str(e)}"
        )
