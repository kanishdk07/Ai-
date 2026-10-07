"""
Authentication API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import LoginRequest, Token, RefreshTokenRequest, UserResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.models import User
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint

    Returns JWT access token and refresh token
    """
    access_token, refresh_token = await AuthService.login(db, login_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    access_token = await AuthService.refresh_access_token(db, refresh_data.refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_data.refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    User logout endpoint

    In a stateless JWT setup, logout is handled client-side by removing the token.
    This endpoint is provided for consistency and can be extended to blacklist tokens.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return current_user
