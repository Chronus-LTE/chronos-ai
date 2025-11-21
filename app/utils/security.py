"""
Security utilities for password hashing and verification.
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from the database

    Returns:
        True if the password matches, False otherwise
    """
    # Truncate password to 72 bytes for bcrypt compatibility
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.

    Args:
        password: The plain text password

    Returns:
        The hashed password
    """
    # Truncate password to 72 bytes for bcrypt compatibility
    password = password[:72]
    return pwd_context.hash(password)
