"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
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
from app.utils.jwt_utils import create_access_token

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
]


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================


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


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


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
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Args:
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

    # Create JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

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
async def google_callback(request: Request, code: str, db: AsyncSession = Depends(get_db)):
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
        google_user_info = await AuthService.get_google_user_info(credentials.token)

        if not google_user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google",
            )

        # Get or create user in database
        user = await AuthService.get_or_create_user(db, google_user_info)

        # Create JWT token
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

        # Convert user to schema
        user_schema = UserSchema.from_orm(user)
        token_data = Token(access_token=access_token, token_type="bearer", user=user_schema)

        # Check if client wants HTML (Browser)
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            html_content = f"""
            <html>
                <head>
                    <title>Authenticating...</title>
                    <script>
                        localStorage.setItem('token', '{access_token}');
                        localStorage.setItem('user', JSON.stringify({user_schema.model_dump_json()}));
                        window.location.href = '/static/dashboard.html';
                    </script>
                </head>
                <body>
                    <p>Authenticating, please wait...</p>
                </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        return token_data

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Google callback: {error!s}",
        ) from error


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================


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


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.

    Note: Since we're using JWT tokens, the client should simply discard the token.
    This endpoint is provided for consistency and can be extended for token blacklisting.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh JWT access token.

    Args:
        current_user: Current authenticated user

    Returns:
        Token: New JWT access token and user information
    """
    # Create new JWT token
    access_token = create_access_token(data={"sub": current_user.email, "user_id": current_user.id})

    # Convert user to schema
    user_schema = UserSchema.from_orm(current_user)

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
