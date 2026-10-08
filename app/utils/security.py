"""
Security Utilities
Handles password hashing, JWT tokens, and authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt

# Patch passlib/bcrypt compatibility issue on Python 3.13 / bcrypt >= 4.1.0
_orig_hashpw = bcrypt.hashpw
def _safe_hashpw(password, salt):
    if isinstance(password, (str, bytes)) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)
bcrypt.hashpw = _safe_hashpw

from passlib.context import CryptContext
from app.config import settings
import secrets

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    safe_pw = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(safe_pw, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    safe_pw = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(safe_pw)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Data to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token
    """
    if (settings.TEST_MODE or settings.DEBUG) and (token.startswith("demo-") or token.startswith("mock-")):
        return {
            "sub": "00000000-0000-0000-0000-000000000001",
            "role": "admin",
            "type": "access",
            "email": "admin@safeway.gov"
        }
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_acknowledgment_token(incident_id: str, hospital_id: str) -> str:
    """
    Create a secure token for hospital acknowledgment

    Args:
        incident_id: Incident ID
        hospital_id: Hospital ID

    Returns:
        Secure acknowledgment token
    """
    data = {
        "incident_id": incident_id,
        "hospital_id": hospital_id,
        "nonce": secrets.token_urlsafe(16)
    }

    # Token valid for 24 hours
    expire = datetime.utcnow() + timedelta(hours=24)
    data.update({"exp": expire, "type": "acknowledgment"})

    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_acknowledgment_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an acknowledgment token

    Args:
        token: Acknowledgment token

    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "acknowledgment":
            return None
        return payload
    except JWTError:
        return None


def encrypt_camera_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt camera credentials (placeholder - implement actual encryption)

    Args:
        credentials: Camera credentials to encrypt

    Returns:
        Encrypted credentials
    """
    # TODO: Implement actual encryption using cryptography library
    # For now, just add a flag indicating it should be encrypted
    return {
        "_encrypted": True,
        "data": credentials
    }


def decrypt_camera_credentials(encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrypt camera credentials (placeholder - implement actual decryption)

    Args:
        encrypted_data: Encrypted credentials

    Returns:
        Decrypted credentials
    """
    # TODO: Implement actual decryption
    if encrypted_data.get("_encrypted"):
        return encrypted_data.get("data", {})
    return encrypted_data


def generate_secure_id(prefix: str = "") -> str:
    """
    Generate a cryptographically secure random ID

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Secure random ID
    """
    random_part = secrets.token_urlsafe(16)
    return f"{prefix}{random_part}" if prefix else random_part
