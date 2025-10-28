from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, constr, validator
from supabase import create_client, Client
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

router = APIRouter(tags=["auth"])

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_LENGTH = 72

def hash_password(password: str) -> str:
    # Truncate password to 72 bytes before hashing
    truncated = password.encode("utf-8")[:MAX_BCRYPT_LENGTH]
    return pwd_context.hash(truncated.decode("utf-8", "ignore"))

class RegisterRequest(BaseModel):
    email: EmailStr
    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(min_length=8, max_length=128)

    @validator("password")
    def password_complexity(cls, v):
        if len(v.encode("utf-8")) > MAX_BCRYPT_LENGTH:
            raise ValueError("Password too long for bcrypt (max 72 bytes)")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must include at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must include at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must include at least one number")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/~" for c in v):
            raise ValueError("Password must include at least one special character")
        return v

class RegisterResponse(BaseModel):
    id: str
    email: EmailStr
    username: str

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(req: RegisterRequest):
    # Truncate password for bcrypt and Supabase
    password_truncated = req.password.encode("utf-8")[:MAX_BCRYPT_LENGTH].decode("utf-8", "ignore")

    # Hash the password
    hashed_password = hash_password(req.password)

    # Sign up user with Supabase Auth
    try:
        user_response = supabase.auth.sign_up({
            "email": req.email,
            "password": password_truncated
        })
    except Exception as e:
        if "already registered" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not user_response.user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user")

    # Insert into users_profile table
    try:
        supabase.table("users_profile").insert({
            "id": user_response.user.id,
            "username": req.username,
            "email": req.email
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Profile creation failed: {str(e)}")

    return RegisterResponse(
        id=user_response.user.id,
        email=req.email,
        username=req.username
    )
