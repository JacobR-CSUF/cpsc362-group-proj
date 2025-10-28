"""
Authentication Dependencies
Handles JWT token verification and user authentication
"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional

from .services.supabase_client import get_supabase_client

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token and return current user
    
    Args:
        credentials: JWT token from Authorization header
        
    Returns:
        dict: User information from token
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        jwt_secret = os.getenv("JWT_SECRET", "super-secret-jwt-token-with-at-least-32-characters-long")
        
        # Verify token
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        # Extract user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Verify user exists in database
        client = get_supabase_client()
        response = client.table("users").select("*").eq("id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return response.data[0]
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Optional authentication - returns user if authenticated, None otherwise
    
    Useful for endpoints that change behavior based on authentication
    but don't require it
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None