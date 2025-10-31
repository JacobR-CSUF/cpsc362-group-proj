from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"

security = HTTPBearer()

def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency for protected routes - extracts and validates user from token"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    return user_id