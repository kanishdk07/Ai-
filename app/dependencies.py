"""
Dependencies
Shared dependencies for FastAPI routes
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal, get_db
from app.models import User, UserRole
from app.utils.security import decode_token
from app.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token

    Args:
        credentials: HTTP bearer credentials
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user has admin role

    Args:
        current_user: Current user from get_current_user

    Returns:
        Admin user

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_operator_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user has operator or admin role

    Args:
        current_user: Current user from get_current_user

    Returns:
        Operator or admin user

    Raises:
        HTTPException: If user doesn't have required role
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator or admin access required"
        )
    return current_user


async def check_maintenance_mode(request: Request):
    """
    Dependency to check if system is in maintenance mode

    Args:
        request: FastAPI request

    Raises:
        HTTPException: If system is in maintenance mode (except for admin endpoints)
    """
    if settings.MAINTENANCE_MODE:
        # Allow health check and admin endpoints during maintenance
        path = request.url.path
        allowed_paths = [
            "/api/v1/admin/health",
            "/api/v1/admin/maintenance",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        if not any(path.startswith(allowed_path) for allowed_path in allowed_paths):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="System is currently in maintenance mode"
            )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise
    Used for endpoints that work with or without authentication

    Args:
        credentials: Optional HTTP bearer credentials
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None or payload.get("type") != "access":
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        return user if user and user.is_active else None

    except Exception as e:
        logger.warning(f"Optional auth failed: {str(e)}")
        return None


def verify_test_mode():
    """
    Dependency to ensure system is in test mode for sensitive operations

    Raises:
        HTTPException: If attempting sensitive operation in production mode
    """
    if not settings.TEST_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires TEST_MODE to be disabled. Configure the system for production use."
        )
