from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, constr, validator
import bcrypt

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic model for registration request
class RegisterRequest(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)

    @validator("password")
    def password_complexity(cls, v):
        # simple check: must contain letters and numbers
        if v.isalpha() or v.isdigit() or v.islower():
            raise ValueError("Password must include uppercase, letters, and numbers")
        return v

# Mock database (just a dictionary for testing)
mock_users_db = {}

@router.post("/register")
async def register_user(payload: RegisterRequest):
    if payload.email in mock_users_db:
        raise HTTPException(status_code=409, detail="Email already exists")

    # hash password
    hashed_password = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()

    # save user to mock db
    mock_users_db[payload.email] = {
        "username": payload.username,
        "password": hashed_password
    }

    return {
        "message": "User created (mock)",
        "user": {
            "email": payload.email,
            "username": payload.username
        }
    }
