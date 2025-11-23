"""
User service for user management operations.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import GoogleUserInfo, UserCreate
from app.utils.security import get_password_hash


class UserService:
    """Service for user management operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_google_id(db: AsyncSession, google_id: str) -> User | None:
        """
        Get user by Google ID.

        Args:
            db: Database session
            google_id: Google user ID

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_from_google(db: AsyncSession, google_user_info: GoogleUserInfo) -> User:
        """
        Create new user from Google OAuth data.

        Args:
            db: Database session
            google_user_info: Google user information

        Returns:
            Newly created user
        """
        new_user = User(
            email=google_user_info.email,
            full_name=google_user_info.name,
            picture=google_user_info.picture,
            google_id=google_user_info.id,
            google_access_token=google_user_info.access_token,
            google_refresh_token=google_user_info.refresh_token,
            is_verified=google_user_info.verified_email,
            is_active=True,
            last_login=datetime.now(timezone.utc),
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate) -> User:
        """
        Create new user from standard registration.

        Args:
            db: Database session
            user_in: User registration data

        Returns:
            Newly created user
        """
        hashed_password = get_password_hash(user_in.password)

        new_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,  # Email verification needed later
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    @staticmethod
    async def update(db: AsyncSession, user: User, update_data: dict) -> User:
        """
        Update user information.

        Args:
            db: Database session
            user: User to update
            update_data: Dictionary of fields to update

        Returns:
            Updated user
        """
        for field, value in update_data.items():
            if value is not None and hasattr(user, field):
                setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def update_last_login(db: AsyncSession, user: User) -> User:
        """
        Update user's last login timestamp.

        Args:
            db: Database session
            user: User to update

        Returns:
            Updated user
        """
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user
