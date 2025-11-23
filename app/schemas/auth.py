"""
Pydantic schemas for authentication
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user"""

    password: str
    google_id: str | None = None


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""

    full_name: str | None = None
    picture: str | None = None


class UserInDB(UserBase):
    """User schema as stored in database"""

    id: int
    picture: str | None = None
    google_id: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """User schema for API responses"""


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    token_type: str
    user: User


class TokenData(BaseModel):
    """Token payload data"""

    email: str | None = None
    user_id: int | None = None


class GoogleUserInfo(BaseModel):
    """Google user information from OAuth"""

    id: str
    email: str
    verified_email: bool
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    locale: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
