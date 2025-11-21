"""
JWT token utilities for creating and verifying access tokens.
"""

from datetime import datetime, timedelta, timezone

from jwt import PyJWTError, decode, encode

from app.config import settings
from app.schemas.auth import TokenData


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional token expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> TokenData | None:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None:
            return None

        return TokenData(email=email, user_id=user_id)
    except PyJWTError:
        return None
