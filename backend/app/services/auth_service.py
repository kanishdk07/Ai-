"""
Authentication Service
Handles user authentication, registration, and token management
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models import User
from app.schemas.user import UserCreate, LoginRequest
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management"""

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password

        Args:
            db: Database session
            username: Username or email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        result = await db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Authentication failed: User not found - {username}")
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password - {username}")
            return None

        if not user.is_active:
            logger.warning(f"Authentication failed: Inactive user - {username}")
            return None

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        await db.commit()

        logger.info(f"User authenticated successfully: {username}")
        return user

    @staticmethod
    async def login(db: AsyncSession, login_data: LoginRequest) -> Tuple[str, str]:
        """
        Login user and generate tokens

        Args:
            db: Database session
            login_data: Login credentials

        Returns:
            Tuple of (access_token, refresh_token)

        Raises:
            HTTPException: If authentication fails
        """
        user = await AuthService.authenticate_user(
            db, login_data.username, login_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username}
        )

        logger.info(f"Tokens generated for user: {user.username}")
        return access_token, refresh_token

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> str:
        """
        Generate new access token from refresh token

        Args:
            db: Database session
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            HTTPException: If refresh token is invalid
        """
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "role": user.role.value}
        )

        logger.info(f"Access token refreshed for user: {user.username}")
        return access_token

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """
        Create a new user

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created user

        Raises:
            HTTPException: If user already exists
        """
        # Check if username exists
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            role=user_data.role,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"New user created: {new_user.username}")
        return new_user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            User object or None
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
