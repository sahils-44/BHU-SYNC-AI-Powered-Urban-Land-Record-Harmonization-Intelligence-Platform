"""
BHU-SYNC Phase B: Authentication Router
Handles user sign-in, session logout, and profile/permission resolution.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status

from services.auth_service import auth_service
from dependencies.auth import get_current_user, get_current_profile

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = 3600
    user: Dict[str, Any]
    profile: Dict[str, Any]


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Authenticate user via Supabase Auth or verified test credentials.
    Returns Bearer access token and profile metadata.
    """
    session = auth_service.authenticate_credentials(request.email, request.password)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    return session


@router.post("/logout")
def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Sign out the currently authenticated user.
    """
    return {
        "status": "success",
        "message": "Successfully logged out"
    }


@router.get("/me")
def get_my_profile(profile: Dict[str, Any] = Depends(get_current_profile)):
    """
    Retrieve authenticated user profile, organization context, and assigned permissions.
    """
    return profile
