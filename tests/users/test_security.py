"""
Tests for security functions (JWT, password hashing, authentication).

This module tests core security functionality including:
- Password hashing and verification
- JWT token creation and validation
- Access and refresh tokens
- Token claim validation
- Permission caching
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    InactiveUserException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.users.models import User


# ==================== Password Hashing Tests ====================


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing_creates_hash(self):
        """Test that password hashing creates a non-empty hash."""
        password = 'SecurePass123!'
        hashed = hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Hash should be different from plain password

    def test_password_verification_success(self):
        """Test that correct password verifies successfully."""
        password = 'SecurePass123!'
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test that incorrect password fails verification."""
        password = 'SecurePass123!'
        hashed = hash_password(password)

        assert verify_password('WrongPassword!', hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = 'SecurePass123!'
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different salts should produce different hashes
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_hash_format(self):
        """Test that password hash has expected bcrypt format."""
        password = 'SecurePass123!'
        hashed = hash_password(password)

        # Bcrypt 2b format starts with $2b$
        assert hashed.startswith('$2b$')


# ==================== Access Token Tests ====================


class TestAccessToken:
    """Test JWT access token creation and validation."""

    def test_create_access_token_with_default_expiration(self):
        """Test creating access token with default expiration."""
        data = {'sub': 'test@example.com'}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiration(self):
        """Test creating access token with custom expiration."""
        data = {'sub': 'test@example.com'}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)

        assert token is not None

    def test_access_token_contains_required_claims(self):
        """Test that access token contains all required JWT claims."""
        email = 'test@example.com'
        token = create_access_token({'sub': email})
        decoded = decode_access_token(token)

        # Verify all required claims
        assert decoded['sub'] == email
        assert 'jti' in decoded  # JWT ID
        assert 'iat' in decoded  # Issued at
        assert 'exp' in decoded  # Expiration
        assert decoded['iss'] == settings.JWT_ISSUER  # Issuer
        assert decoded['aud'] == settings.JWT_AUDIENCE  # Audience
        assert decoded['type'] == 'access'  # Token type

    def test_access_token_jti_is_unique(self):
        """Test that each access token has unique JTI."""
        data = {'sub': 'test@example.com'}
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)

        assert decoded1['jti'] != decoded2['jti']

    def test_decode_valid_access_token(self):
        """Test decoding a valid access token."""
        email = 'test@example.com'
        token = create_access_token({'sub': email})

        payload = decode_access_token(token)

        assert payload is not None
        assert payload['sub'] == email

    def test_decode_invalid_token_signature(self):
        """Test decoding token with invalid signature."""
        # Create token with different secret
        token = jwt.encode(
            {'sub': 'test@example.com', 'exp': datetime.now(timezone.utc) + timedelta(minutes=30)},
            'wrong-secret',
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(InvalidTokenException) as exc_info:
            decode_access_token(token)

        assert 'Invalid token' in str(exc_info.value)

    def test_decode_expired_token(self):
        """Test decoding expired token raises TokenExpiredException."""
        # Create token that expired 1 hour ago
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token = jwt.encode(
            {
                'sub': 'test@example.com',
                'exp': past_time,
                'iss': settings.JWT_ISSUER,
                'aud': settings.JWT_AUDIENCE,
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(TokenExpiredException) as exc_info:
            decode_access_token(token)

        assert 'expired' in str(exc_info.value).lower()

    def test_decode_token_with_wrong_issuer(self):
        """Test decoding token with wrong issuer fails."""
        token = jwt.encode(
            {
                'sub': 'test@example.com',
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
                'iss': 'wrong-issuer',
                'aud': settings.JWT_AUDIENCE,
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(InvalidTokenException) as exc_info:
            decode_access_token(token)

        assert 'issuer' in str(exc_info.value).lower()

    def test_decode_token_with_wrong_audience(self):
        """Test decoding token with wrong audience fails."""
        token = jwt.encode(
            {
                'sub': 'test@example.com',
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
                'iss': settings.JWT_ISSUER,
                'aud': 'wrong-audience',
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(InvalidTokenException) as exc_info:
            decode_access_token(token)

        assert 'audience' in str(exc_info.value).lower()

    def test_decode_malformed_token(self):
        """Test decoding malformed token raises InvalidTokenException."""
        with pytest.raises(InvalidTokenException):
            decode_access_token('not.a.valid.token')


# ==================== Refresh Token Tests ====================


class TestRefreshToken:
    """Test JWT refresh token creation and validation."""

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {'sub': 'test@example.com'}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_refresh_token_contains_required_claims(self):
        """Test that refresh token contains required claims."""
        email = 'test@example.com'
        token = create_refresh_token({'sub': email})

        # Decode without type checking to inspect claims
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )

        assert decoded['sub'] == email
        assert decoded['type'] == 'refresh'
        assert 'jti' in decoded
        assert 'iat' in decoded
        assert 'exp' in decoded

    def test_refresh_token_has_longer_expiration(self):
        """Test that refresh token expires later than access token."""
        data = {'sub': 'test@example.com'}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = decode_access_token(access_token)
        # Decode refresh without type checking
        refresh_payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )

        assert refresh_payload['exp'] > access_payload['exp']

    def test_verify_valid_refresh_token(self):
        """Test verifying valid refresh token."""
        email = 'test@example.com'
        token = create_refresh_token({'sub': email})

        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload['sub'] == email
        assert payload['type'] == 'refresh'

    def test_verify_access_token_as_refresh_fails(self):
        """Test that access token cannot be used as refresh token."""
        access_token = create_access_token({'sub': 'test@example.com'})

        with pytest.raises(InvalidTokenException) as exc_info:
            verify_refresh_token(access_token)

        assert 'not a refresh token' in str(exc_info.value).lower()

    def test_verify_expired_refresh_token(self):
        """Test verifying expired refresh token raises exception."""
        # Create refresh token that expired 1 day ago
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        token = jwt.encode(
            {
                'sub': 'test@example.com',
                'exp': past_time,
                'type': 'refresh',
                'iss': settings.JWT_ISSUER,
                'aud': settings.JWT_AUDIENCE,
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(TokenExpiredException):
            verify_refresh_token(token)


# ==================== Authentication Dependency Tests ====================


class TestGetCurrentUser:
    """Test get_current_user FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting current user with valid token."""
        token = create_access_token({'sub': test_user.email})

        user = await get_current_user(token, db_session)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_caches_permissions(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that get_current_user caches permissions on user object."""
        token = create_access_token({'sub': test_user.email})

        user = await get_current_user(token, db_session)

        # Check that _cached_permissions attribute exists
        assert hasattr(user, '_cached_permissions')
        assert isinstance(user._cached_permissions, set)  # type: ignore

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session: AsyncSession):
        """Test get_current_user with invalid token."""
        with pytest.raises(InvalidTokenException):
            await get_current_user('invalid.token.here', db_session)

    @pytest.mark.asyncio
    async def test_get_current_user_missing_subject(self, db_session: AsyncSession):
        """Test get_current_user with token missing subject claim."""
        # Create token without 'sub' claim
        token = jwt.encode(
            {
                'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
                'iss': settings.JWT_ISSUER,
                'aud': settings.JWT_AUDIENCE,
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(InvalidTokenException) as exc_info:
            await get_current_user(token, db_session)

        assert 'subject claim' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session: AsyncSession):
        """Test get_current_user with token for non-existent user."""
        token = create_access_token({'sub': 'nonexistent@example.com'})

        with pytest.raises(UserNotFoundException):
            await get_current_user(token, db_session)


# ==================== Token Expiration Tests ====================


class TestTokenExpiration:
    """Test token expiration behavior."""

    def test_access_token_default_expiration_time(self):
        """Test that access token expires at correct time."""
        before = datetime.now(timezone.utc)
        token = create_access_token({'sub': 'test@example.com'})
        after = datetime.now(timezone.utc)

        decoded = decode_access_token(token)
        exp_time = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        expected_min = before + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expected_max = after + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        assert expected_min <= exp_time <= expected_max

    def test_refresh_token_default_expiration_time(self):
        """Test that refresh token expires at correct time."""
        before = datetime.now(timezone.utc)
        token = create_refresh_token({'sub': 'test@example.com'})
        after = datetime.now(timezone.utc)

        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
        exp_time = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        expected_min = before + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expected_max = after + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        assert expected_min <= exp_time <= expected_max


# ==================== Security Best Practices Tests ====================


class TestSecurityBestPractices:
    """Test security best practices implementation."""

    def test_jwt_secret_is_secure(self):
        """Test that JWT secret meets minimum length requirement."""
        # This should pass due to validation in settings
        assert len(settings.JWT_SECRET) >= 32

    def test_jwt_algorithm_is_secure(self):
        """Test that JWT algorithm is one of the secure algorithms."""
        allowed = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        assert settings.JWT_ALGORITHM in allowed

    def test_bcrypt_uses_sufficient_rounds(self):
        """Test that bcrypt uses sufficient work factor."""
        from app.core.security import pwd_context

        # bcrypt__rounds should be at least 12
        assert pwd_context.context_kwds['bcrypt__rounds'] >= 12

    def test_token_includes_issued_at_timestamp(self):
        """Test that tokens include iat claim for audit trail."""
        token = create_access_token({'sub': 'test@example.com'})
        decoded = decode_access_token(token)

        assert 'iat' in decoded
        iat_time = datetime.fromtimestamp(decoded['iat'], tz=timezone.utc)
        # iat should be recent (within last minute)
        assert datetime.now(timezone.utc) - iat_time < timedelta(minutes=1)
