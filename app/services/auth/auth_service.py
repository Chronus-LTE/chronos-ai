"""
Authentication service for handling OAuth and JWT operations.
"""

from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import GoogleUserInfo
from app.services.auth.user_service import UserService
from app.utils.jwt_utils import verify_token
from app.utils.security import verify_password


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    async def get_google_user_info(
        access_token: str, refresh_token: str | None = None
    ) -> GoogleUserInfo | None:
        """
        Get user information from Google using access token.

        Args:
            access_token: Google OAuth access token
            refresh_token: Google OAuth refresh token

        Returns:
            GoogleUserInfo if successful, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if response.status_code == 200:
                    user_data = response.json()
                    # Add tokens to user data
                    user_data["access_token"] = access_token
                    user_data["refresh_token"] = refresh_token
                    # Note: Refresh token is only returned on first consent or if access_type=offline
                    # We need to pass it from the flow credentials if available
                    return GoogleUserInfo(**user_data)

                return None
        except Exception as error:
            print(f"Error getting Google user info: {error}")
            return None

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: User password

        Returns:
            User if authentication successful, None otherwise
        """
        user = await UserService.get_by_email(db, email)
        if not user:
            return None

        if not user.hashed_password:
            # User exists but has no password (e.g. Google OAuth only)
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    async def get_or_create_user(db: AsyncSession, google_user_info: GoogleUserInfo) -> User:
        """
        Get existing user or create new user from Google OAuth data.

        Args:
            db: Database session
            google_user_info: Google user information

        Returns:
            User object
        """
        # Try to find user by Google ID
        user = await UserService.get_by_google_id(db, google_user_info.id)

        if user:
            # Update last login and picture if changed
            user.last_login = datetime.now(timezone.utc)
            if google_user_info.picture:
                user.picture = google_user_info.picture
            if google_user_info.access_token:
                user.google_access_token = google_user_info.access_token
            if google_user_info.refresh_token:
                user.google_refresh_token = google_user_info.refresh_token
            await db.commit()
            await db.refresh(user)
            return user

        # Try to find user by email
        user = await UserService.get_by_email(db, google_user_info.email)

        if user:
            # Link Google account to existing user
            user.google_id = google_user_info.id
            user.is_verified = google_user_info.verified_email
            user.last_login = datetime.now(timezone.utc)
            if google_user_info.picture:
                user.picture = google_user_info.picture
            if google_user_info.access_token:
                user.google_access_token = google_user_info.access_token
            if google_user_info.refresh_token:
                user.google_refresh_token = google_user_info.refresh_token
            await db.commit()
            await db.refresh(user)
            return user

        # Create new user
        return await UserService.create_from_google(db, google_user_info)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Get user by ID."""
        return await UserService.get_by_id(db, user_id)

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        """Get user by email."""
        return await UserService.get_by_email(db, email)

    @staticmethod
    async def update_user(db: AsyncSession, user: User, update_data: dict) -> User:
        """Update user information."""
        return await UserService.update(db, user, update_data)

    @staticmethod
    async def get_current_user(token: str, db: AsyncSession) -> User:
        """
        Get current user from JWT token.

        Args:
            token: JWT access token
            db: Database session

        Returns:
            Current user

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify token
        token_data = verify_token(token)

        if token_data is None or token_data.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = await AuthService.get_user_by_id(db, token_data.user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        return user

    @staticmethod
    async def get_current_active_user(current_user: User) -> User:
        """
        Verify user is active.

        Args:
            current_user: Current user

        Returns:
            Active user

        Raises:
            HTTPException: If user is not active
        """
        if not current_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        return current_user
