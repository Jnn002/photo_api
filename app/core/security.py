"""
Security functions for authentication and authorization.

This module provides password hashing, JWT token generation/validation,
and FastAPI dependencies for user authentication.
"""

__all__ = [
    'hash_password',
    'verify_password',
    'create_access_token',
    'create_refresh_token',
    'decode_access_token',
    'verify_refresh_token',
    'get_current_user',
    'get_current_active_user',
    'oauth2_scheme',
    'pwd_context',
]

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.exceptions import (
    InactiveUserException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)
from app.users.models import User
from app.users.repository import UserRepository

# ==================== Password Hashing ====================

# Passlib context for bcrypt password hashing with strengthened configuration
pwd_context = CryptContext(
    schemes=['bcrypt'],
    deprecated='auto',
    bcrypt__rounds=12,  # Work factor for bcrypt (12 is balanced, consider 13-14 for production)
    bcrypt__ident='2b',  # Use latest bcrypt variant
)


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT Token Management ====================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token with standard claims.

    Includes:
    - sub: Subject (user identifier)
    - exp: Expiration time
    - iat: Issued at time
    - jti: JWT ID (for token revocation/tracking)
    - iss: Issuer
    - aud: Audience
    - type: Token type (access)

    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional expiration time delta. If not provided,
                      uses ACCESS_TOKEN_EXPIRE_MINUTES from settings

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=30)
        )
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    # Calculate expiration time
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard JWT claims
    to_encode.update(
        {
            'exp': expire,
            'iat': now,  # Issued at time
            'jti': str(uuid4()),  # Unique token ID for revocation
            'iss': settings.JWT_ISSUER,  # Token issuer
            'aud': settings.JWT_AUDIENCE,  # Token audience
            'type': 'access',  # Token type
        }
    )

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a refresh token with longer expiration.

    Refresh tokens should only contain minimal claims (sub, jti)
    and are used to obtain new access tokens without re-authentication.

    Args:
        data: Dictionary containing claims to encode (typically just {"sub": user.email})

    Returns:
        Encoded JWT refresh token string

    Example:
        refresh_token = create_refresh_token(data={"sub": user.email})
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    # Refresh tokens typically last much longer (7-30 days)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Add standard JWT claims with refresh type
    to_encode.update(
        {
            'exp': expire,
            'iat': now,
            'jti': str(uuid4()),
            'iss': settings.JWT_ISSUER,
            'aud': settings.JWT_AUDIENCE,
            'type': 'refresh',  # Distinguish from access tokens
        }
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Validates:
    - Token signature
    - Expiration time
    - Issuer (iss claim)
    - Audience (aud claim)

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing decoded token claims

    Raises:
        TokenExpiredException: If token has expired
        InvalidTokenException: If token is invalid, malformed, or has wrong issuer/audience

    Example:
        try:
            payload = decode_access_token(token)
            email = payload.get("sub")
        except TokenExpiredException:
            # Handle expired token
        except InvalidTokenException:
            # Handle invalid token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,  # Validate issuer
            audience=settings.JWT_AUDIENCE,  # Validate audience
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredException('Token has expired') from e
    except jwt.InvalidIssuerError as e:
        raise InvalidTokenException('Invalid token issuer') from e
    except jwt.InvalidAudienceError as e:
        raise InvalidTokenException('Invalid token audience') from e
    except jwt.InvalidTokenError as e:
        raise InvalidTokenException('Invalid token') from e


def verify_refresh_token(token: str) -> dict:
    """
    Verify a refresh token and return payload.

    Ensures the token is specifically a refresh token by checking
    the 'type' claim.

    Args:
        token: JWT refresh token string to verify

    Returns:
        Dictionary containing decoded token claims

    Raises:
        TokenExpiredException: If token has expired
        InvalidTokenException: If token is not a refresh token or is invalid

    Example:
        try:
            payload = verify_refresh_token(token)
            email = payload.get("sub")
        except InvalidTokenException:
            # Handle invalid refresh token
    """
    payload = decode_access_token(token)

    # Ensure this is actually a refresh token
    if payload.get('type') != 'refresh':
        raise InvalidTokenException('Token is not a refresh token')

    return payload


# ==================== FastAPI Security Dependencies ====================

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Caches user permissions on the user object to avoid N+1 queries when
    checking multiple permissions in a single request.

    Args:
        token: JWT token from Authorization header (injected by oauth2_scheme)
        db: Async database session (injected by get_session)

    Returns:
        Authenticated User object with cached permissions

    Raises:
        InvalidTokenException: If token is invalid or email claim missing
        TokenExpiredException: If token has expired
        UserNotFoundException: If user not found in database

    Example:
        @router.get("/me")
        async def read_current_user(
            current_user: Annotated[User, Depends(get_current_user)]
        ):
            return current_user
    """
    # Decode token and extract email
    payload = decode_access_token(token)
    email: str | None = payload.get('sub')

    if email is None:
        raise InvalidTokenException('Token missing subject claim')

    # Fetch user from database
    user_repo = UserRepository(db)
    user = await user_repo.find_by_email(email)

    if user is None:
        raise UserNotFoundException(email)

    # Cache permissions on user object for this request to avoid N+1 queries
    # This is safe because User object is request-scoped
    permissions = await user_repo.get_user_permissions(user.id)
    user._cached_permissions = {perm.code for perm in permissions}  # type: ignore

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency to get current user only if they are active.

    Args:
        current_user: User object from get_current_user dependency

    Returns:
        Active User object

    Raises:
        InactiveUserException: If user status is not ACTIVE

    Example:
        @router.post("/sessions")
        async def create_session(
            user: Annotated[User, Depends(get_current_active_user)]
        ):
            # Only active users can create sessions
            ...
    """
    from app.core.enums import Status

    if current_user.status != Status.ACTIVE:
        raise InactiveUserException(f'User {current_user.email} is inactive')

    return current_user
