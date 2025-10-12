"""
Security functions for authentication and authorization.

This module provides password hashing, JWT token generation/validation,
and FastAPI dependencies for user authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

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

# Passlib context for bcrypt password hashing
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


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
    Create a JWT access token.

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

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add expiration claim to token payload
    to_encode.update({'exp': expire})

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing decoded token claims

    Raises:
        TokenExpiredException: If token has expired
        InvalidTokenException: If token is invalid or malformed

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
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredException('Token has expired') from e
    except jwt.InvalidTokenError as e:
        raise InvalidTokenException('Invalid token') from e


# ==================== FastAPI Security Dependencies ====================

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header (injected by oauth2_scheme)
        db: Async database session (injected by get_session)

    Returns:
        Authenticated User object

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
