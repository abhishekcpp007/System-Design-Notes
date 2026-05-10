from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from app.api.deps import get_current_user
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_token,
)
from app.utils.exceptions import (
    ConflictException,
    UnauthorizedException,
    BadRequestException,
)
from app.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    data: SignupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictException("Email already registered")

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role="user",  # Default role, first user can be promoted to admin manually
    )
    db.add(user)
    await db.flush()  # Get the user ID without committing

    # Generate tokens
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    refresh_token = generate_refresh_token()

    # Store refresh token hash in DB
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token_record)

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Constant-time comparison: always verify even if user not found
    if user is None:
        # Run bcrypt on dummy hash to prevent timing attacks
        verify_password(data.password, "$2b$12$LJ3m4ks92h3nFOoA.t0v3OdQnRJl5Iu5yFz7mKQ2j0E.n.Y7WdMi")
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    if not user.password_hash:
        raise BadRequestException("This account uses OAuth login. Please use Google or GitHub to sign in.")

    if not verify_password(data.password, user.password_hash):
        raise UnauthorizedException("Invalid email or password")

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Generate tokens
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    refresh_token = generate_refresh_token()

    # Store refresh token
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token_record)

    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=dict)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Get new access token using refresh token from cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("No refresh token provided")

    # Find token in DB
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if token_record is None:
        raise UnauthorizedException("Invalid refresh token")

    if token_record.is_revoked:
        # SECURITY: Token reuse detected! Revoke ALL user's tokens
        await db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == token_record.user_id)
        )
        # Mark all as revoked
        revoke_result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == token_record.user_id,
                RefreshToken.is_revoked == False,
            )
        )
        for token in revoke_result.scalars():
            token.is_revoked = True
        raise UnauthorizedException("Token reuse detected. All sessions revoked. Please login again.")

    if token_record.expires_at < datetime.now(timezone.utc):
        raise UnauthorizedException("Refresh token expired")

    # Revoke current token (rotation)
    token_record.is_revoked = True

    # Get user
    user_result = await db.execute(select(User).where(User.id == token_record.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    # Generate new tokens
    new_access_token = create_access_token({"user_id": user.id, "role": user.role})
    new_refresh_token = generate_refresh_token()

    # Store new refresh token
    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_token_record)

    # Set new cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke refresh token and clear cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash = hash_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True

    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile."""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url

    return UserResponse.model_validate(current_user)
