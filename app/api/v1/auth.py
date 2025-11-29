"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserUpdate
from app.schemas.auth import User as UserSchema
from app.services.auth.auth_service import AuthService
from app.services.auth.user_service import UserService
from app.utils.jwt_utils import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme for JWT Bearer tokens
security = HTTPBearer()


# Google OAuth configuration
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
    }
}

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    return await AuthService.get_current_user(token, db)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Current active user

    Raises:
        HTTPException: If user is not active
    """
    return await AuthService.get_current_active_user(current_user)


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_in: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If email already registered
    """
    # Check if user already exists
    user = await UserService.get_by_email(db, user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    return await UserService.create(db, user_in)


@router.post("/login", response_model=Token)
async def login(response: Response, user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Args:
        response: FastAPI response object
        user_in: User login data
        db: Database session

    Returns:
        Token: JWT access token and user information

    Raises:
        HTTPException: If authentication fails
    """
    user = await AuthService.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    await UserService.update_last_login(db, user)

    # Create JWT tokens
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})

    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # Only secure in production
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # Convert user to schema
    user_schema = UserSchema.from_orm(user)

    return Token(access_token=access_token, token_type="bearer", user=user_schema)


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth login flow.

    Returns:
        dict: Contains authorization_url and state for OAuth flow

    Raises:
        HTTPException: If there's an error initiating the login flow
    """
    try:
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )

        return {"authorization_url": authorization_url, "state": state}
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating Google login: {error!s}",
        ) from error


@router.get("/google/callback", response_model=Token | None)
async def google_callback(
    request: Request, response: Response, code: str, db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Supports both JSON response (API) and HTML response (Web).
    """
    try:
        # Exchange authorization code for access token
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info from Google
        google_user_info = await AuthService.get_google_user_info(
            credentials.token, credentials.refresh_token
        )

        if not google_user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google",
            )

        # Get or create user in database
        user = await AuthService.get_or_create_user(db, google_user_info)

        # Create JWT tokens
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
        refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})

        # Set refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        # Convert user to schema
        user_schema = UserSchema.from_orm(user)
        token_data = Token(access_token=access_token, token_type="bearer", user=user_schema)

        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            # Redirect to frontend callback page with tokens in URL
            redirect_url = (
                f"{settings.FRONTEND_CALLBACK_URL}"
                f"?access_token={access_token}"
                f"&refresh_token={refresh_token}"
                f"&expires_in={settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}"
                f"&user={user_schema.model_dump_json()}"
            )
            redirect_response = RedirectResponse(url=redirect_url)
            redirect_response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=settings.ENVIRONMENT == "production",
                samesite="lax",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )
            return redirect_response

        return token_data

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Google callback: {error!s}",
        ) from error


@router.get("/me", response_model=UserSchema)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserSchema: User profile information
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user's profile.

    Args:
        update_data: Profile data to update (full_name, picture)
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserSchema: Updated user information

    Raises:
        HTTPException: If no fields to update or update fails
    """
    # Convert Pydantic model to dict, excluding unset fields
    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    # Update user
    return await AuthService.update_user(db, current_user, update_dict)


@router.delete("/me")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate current user's account (soft delete).

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    # Soft delete by setting is_active to False
    await AuthService.update_user(db, current_user, {"is_active": False})

    return {"message": "Account successfully deactivated"}


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """
    Logout current user.

    Note: Since we're using JWT tokens, the client should simply discard the token.
    We also clear the refresh token cookie.

    Args:
        response: FastAPI response object
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh JWT access token using refresh token from cookie.

    Args:
        response: FastAPI response object
        refresh_token: Refresh token from cookie
        db: Database session

    Returns:
        Token: New JWT access token and user information

    Raises:
        HTTPException: If refresh token is missing or invalid
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    token_data = verify_token(refresh_token)
    if not token_data or token_data.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = await UserService.get_by_email(db, token_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new JWT tokens
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})

    # Set new refresh token in HttpOnly cookie (rotate refresh token)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # Convert user to schema
    user_schema = UserSchema.from_orm(user)

    return Token(access_token=access_token, token_type="bearer", user=user_schema)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for authentication service.

    Returns:
        dict: Service status
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "google_oauth_configured": bool(settings.GOOGLE_CLIENT_ID),
    }
