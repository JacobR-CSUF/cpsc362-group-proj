from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field, validator
import re
import bcrypt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import httpx
import uuid
import jwt
from collections import defaultdict
from typing import Dict
import time
import traceback

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiting storage
login_attempts: Dict[str, list] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    username: str = Field(..., min_length=3, max_length=30, description="Username (3-30 chars)")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>)')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class RegisterResponse(BaseModel):
    message: str
    user: dict


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


class ErrorResponse(BaseModel):
    detail: str


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_jwt_token(user_data: dict, token_type: str = "access") -> str:
    """Generate JWT token for user authentication"""
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise ValueError("JWT_SECRET not configured")
    if not user_data or "id" not in user_data:
        raise ValueError("User data with an id is required")

    now = datetime.now(timezone.utc)
    expiration_hours = 3 if token_type == "access" else 168  # 1 hour or 7 days
    expiration = now + timedelta(hours=expiration_hours)

    app_role = user_data.get("role", "user")
    payload = {
        "sub": user_data["id"],
        "username": user_data.get("username", ""),
        "email": user_data.get("email", ""),
        "pfp_url": user_data.get("profile_pic") or user_data.get("pfp_url") or "",
        # Supabase/PostgREST expects this to map to the database role; keep it as 'authenticated'
        "role": "authenticated",
        # App-level role retained separately if provided
        "app_role": app_role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp())
    }

    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return token


def check_rate_limit(ip_address: str) -> bool:
    """Check if IP address has exceeded login rate limit"""
    current_time = time.time()
    attempts = login_attempts[ip_address]
    
    
    login_attempts[ip_address] = [
        attempt_time for attempt_time in attempts 
        if current_time - attempt_time < RATE_LIMIT_WINDOW
    ]
    
    return len(login_attempts[ip_address]) < MAX_LOGIN_ATTEMPTS


def record_login_attempt(ip_address: str, email: str, success: bool):
    """Record login attempt for rate limiting and logging"""
    current_time = time.time()
    login_attempts[ip_address].append(current_time)
    
    log_message = f"{'Successful' if success else 'Failed'} login attempt for {email} from {ip_address}"
    print(f"[{datetime.utcnow().isoformat()}] {log_message}")


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Invalid input"},
        409: {"description": "Email or username already exists"},
        500: {"description": "Internal server error"}
    }
)
async def register(request: RegisterRequest):
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Must contain uppercase, lowercase, digit, and special character (min 8 chars)
    - **username**: 3-30 characters, alphanumeric and underscores only
    """
    user_id = str(uuid.uuid4())
    
    try:
        rest_url = os.getenv("POSTGREST_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not rest_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="POSTGREST_URL environment variable not set"
            )
        
        if not service_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_SERVICE_ROLE_KEY environment variable not set"
            )
        
        async with httpx.AsyncClient(verify=False) as client:
            # Check if username already exists
            username_check = await client.get(
                f"{rest_url}/users?username=eq.{request.username}",
                headers={
                    "apikey": service_key,
                    "Authorization": f"Bearer {service_key}"
                }
            )
            
            if username_check.status_code == 200 and username_check.json():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken"
                )
            
            # Check if email already exists
            email_check = await client.get(
                f"{rest_url}/users?email=eq.{request.email}",
                headers={
                    "apikey": service_key,
                    "Authorization": f"Bearer {service_key}"
                }
            )
            
            if email_check.status_code == 200 and email_check.json():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = hash_password(request.password)
            
            # Prepare user data
            profile_data = {
                "id": user_id,
                "email": request.email,
                "username": request.username,
                "password_hash": hashed_password
            }
            
            # Create user in database
            profile_response = await client.post(
                f"{rest_url}/users",
                headers={
                    "apikey": service_key,
                    "Authorization": f"Bearer {service_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                json=profile_data
            )
            
            if profile_response.status_code not in [200, 201]:
                error_detail = {
                    "status": profile_response.status_code,
                    "error": profile_response.text,
                    "url": rest_url
                }
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create user profile: {error_detail}"
                )
            
            created_user = profile_response.json()
            if isinstance(created_user, list) and len(created_user) > 0:
                created_user = created_user[0]
        
        return RegisterResponse(
            message="User registered successfully",
            user={
                "id": user_id,
                "email": request.email,
                "username": request.username,
                "created_at": created_user.get("created_at", datetime.utcnow().isoformat())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Registration error: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Too many login attempts"},
        500: {"description": "Internal server error"}
    }
)
async def login(request: LoginRequest, req: Request):
    """
    Login with email and password
    
    Returns JWT access token (1 hour) and refresh token (7 days)
    
    Rate limited to 5 attempts per 15 minutes per IP address
    """
    client_ip = req.client.host if req.client else "unknown"
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        record_login_attempt(client_ip, request.email, False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    try:
        rest_url = os.getenv("POSTGREST_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not rest_url or not service_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error"
            )
        
        async with httpx.AsyncClient(verify=False) as client:
            # Get user by email
            user_response = await client.get(
                f"{rest_url}/users?email=eq.{request.email}",
                headers={
                    "apikey": service_key,
                    "Authorization": f"Bearer {service_key}"
                }
            )
            
            if user_response.status_code != 200 or not user_response.json():
                record_login_attempt(client_ip, request.email, False)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            user_data = user_response.json()[0]
            
            # Verify password
            if not verify_password(request.password, user_data.get("password_hash", "")):
                record_login_attempt(client_ip, request.email, False)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Record successful login
            record_login_attempt(client_ip, request.email, True)
            
            # Generate tokens
            access_token = generate_jwt_token(user_data, "access")
            refresh_token = generate_jwt_token(user_data, "refresh")
            
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=3600,
                user={
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "username": user_data["username"]
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        record_login_attempt(client_ip, request.email, False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
