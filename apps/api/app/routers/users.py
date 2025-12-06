"""
User CRUD Endpoints
Handles user profile operations with authentication and authorization
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..services.supabase_client import get_supabase_client
from ..dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic Models
class UserPublicProfile(BaseModel):
    """Public user profile response"""
    id: str  # UUID as string
    username: str
    profile_pic: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserPrivateProfile(UserPublicProfile):
    """Private user profile (includes email)"""
    email: str


class UserUpdateRequest(BaseModel):
    """Request model for updating user profile"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_pic: Optional[str] = None

    class Config:
        # Only allow non-null fields
        exclude_none = True


class UserResponse(BaseModel):
    """Standard user response wrapper"""
    success: bool
    data: Optional[UserPublicProfile | UserPrivateProfile] = None
    message: Optional[str] = None


# Helper Functions
async def get_user_by_id(user_id: str) -> dict:
    """Fetch user from database by UUID"""
    try:
        client = get_supabase_client()
        response = client.table("users").select("*").eq("id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_user_by_username(username: str) -> dict:
    """Fetch user from database by username"""
    try:
        client = get_supabase_client()
        response = client.table("users").select("*").eq("username", username).execute()

        if not response.data or len(response.data) == 0:
            return None

        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


# Endpoints
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile (includes private info like email)
    
    Protected endpoint - requires authentication
    """
    try:
        user_data = await get_user_by_id(current_user["id"])
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            success=True,
            data=UserPrivateProfile(**user_data)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/username/{username}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_profile_by_username(username: str):
    """
    Get any user's public profile by username (does not include email)

    Public endpoint - no authentication required
    """
    try:
        user_data = await get_user_by_username(username)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username {username} not found"
            )

        public_data = {
            "id": str(user_data["id"]),
            "username": user_data["username"],
            "profile_pic": user_data.get("profile_pic"),
            "created_at": user_data["created_at"]
        }

        return UserResponse(
            success=True,
            data=UserPublicProfile(**public_data)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_profile(user_id: str):
    """
    Get any user's public profile (does not include email)
    
    Public endpoint - no authentication required
    Accepts UUID as user_id
    """
    try:
        # Validate UUID format
        try:
            UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format"
            )
        
        user_data = await get_user_by_id(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Return only public fields
        public_data = {
            "id": str(user_data["id"]),
            "username": user_data["username"],
            "profile_pic": user_data.get("profile_pic"),
            "created_at": user_data["created_at"]
        }
        
        return UserResponse(
            success=True,
            data=UserPublicProfile(**public_data)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current authenticated user's profile
    
    Protected endpoint - requires authentication
    Users can only update their own profile
    """
    try:
        # Prepare update data (only non-None fields)
        update_dict = update_data.model_dump(exclude_none=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        # Validate username if provided
        if "username" in update_dict:
            username = update_dict["username"]
            if len(username) < 3 or len(username) > 30:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username must be between 3 and 30 characters"
                )
        
        # Validate profile_pic URL if provided
        if "profile_pic" in update_dict:
            profile_pic = update_dict["profile_pic"]
            if profile_pic and not profile_pic.startswith(("http://", "https://")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Profile picture must be a valid URL"
                )
        
        # Update user in database
        client = get_supabase_client()
        response = client.table("users").update(update_dict).eq("id", current_user["id"]).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            success=True,
            data=UserPrivateProfile(**response.data[0]),
            message="Profile updated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user_account(current_user: dict = Depends(get_current_user)):
    """
    Delete current authenticated user's account
    
    Protected endpoint - requires authentication
    Users can only delete their own account
    
    WARNING: This is a permanent action
    """
    try:
        client = get_supabase_client()
        
        # Check if user exists
        user_data = await get_user_by_id(current_user["id"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete user (cascade deletes will handle related records)
        response = client.table("users").delete().eq("id", current_user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )
