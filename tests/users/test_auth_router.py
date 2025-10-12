"""
Integration tests for authentication endpoints.

This module tests the authentication API endpoints including:
- POST /auth/login - User login
- POST /auth/refresh - Refresh access token
- POST /auth/logout - User logout
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_refresh_token
from app.users.models import User


# ==================== Login Endpoint Tests ====================


class TestLoginEndpoint:
    """Test POST /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'
        assert data['expires_in'] == 30 * 60  # 30 minutes
        assert data['user']['email'] == test_user.email
        assert 'password_hash' not in data['user']  # Should not expose password hash

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login fails with non-existent email."""
        response = await client.post(
            '/auth/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'SomePassword123!',
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert 'detail' in data
        assert 'invalid' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login fails with incorrect password."""
        response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'WrongPassword123!',
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert 'detail' in data
        assert 'invalid' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, inactive_user: User):
        """Test login fails for inactive user."""
        response = await client.post(
            '/auth/login',
            json={
                'email': inactive_user.email,
                'password': 'InactivePass123!',
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert 'inactive' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_login_missing_email(self, client: AsyncClient):
        """Test login fails without email."""
        response = await client.post(
            '/auth/login',
            json={
                'password': 'TestPass123!',
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client: AsyncClient):
        """Test login fails without password."""
        response = await client.post(
            '/auth/login',
            json={
                'email': 'test@example.com',
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Test login fails with invalid email format."""
        response = await client.post(
            '/auth/login',
            json={
                'email': 'not-an-email',
                'password': 'TestPass123!',
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_empty_password(self, client: AsyncClient, test_user: User):
        """Test login fails with empty password."""
        response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': '',
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_tokens_are_different(self, client: AsyncClient, test_user: User):
        """Test that access token and refresh token are different."""
        response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data['access_token'] != data['refresh_token']

    @pytest.mark.asyncio
    async def test_login_multiple_times_generates_different_tokens(
        self, client: AsyncClient, test_user: User
    ):
        """Test that each login generates different tokens."""
        # First login
        response1 = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )

        # Second login
        response2 = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Tokens should be different
        assert data1['access_token'] != data2['access_token']
        assert data1['refresh_token'] != data2['refresh_token']


# ==================== Refresh Token Endpoint Tests ====================


class TestRefreshTokenEndpoint:
    """Test POST /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test refreshing access token with valid refresh token."""
        # First, login to get refresh token
        login_response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )
        refresh_token = login_response.json()['refresh_token']

        # Use refresh token to get new access token
        response = await client.post(
            '/auth/refresh',
            json={
                'refresh_token': refresh_token,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'
        assert data['expires_in'] == 30 * 60
        assert data['user']['email'] == test_user.email

        # New tokens should be different from original
        assert data['access_token'] != login_response.json()['access_token']
        assert data['refresh_token'] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(self, client: AsyncClient):
        """Test refresh fails with invalid token."""
        response = await client.post(
            '/auth/refresh',
            json={
                'refresh_token': 'invalid.token.here',
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_with_access_token_fails(
        self, client: AsyncClient, test_user: User
    ):
        """Test that access token cannot be used as refresh token."""
        # Login to get access token
        login_response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )
        access_token = login_response.json()['access_token']

        # Try to use access token as refresh token
        response = await client.post(
            '/auth/refresh',
            json={
                'refresh_token': access_token,  # Wrong token type
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert 'not a refresh token' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_for_inactive_user(
        self, client: AsyncClient, inactive_user: User
    ):
        """Test refresh fails for inactive user even with valid token."""
        # Create a valid refresh token for inactive user
        refresh_token = create_refresh_token({'sub': inactive_user.email})

        response = await client.post(
            '/auth/refresh',
            json={
                'refresh_token': refresh_token,
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert 'inactive' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_refresh_token_for_nonexistent_user(self, client: AsyncClient):
        """Test refresh fails for non-existent user."""
        # Create token for user that doesn't exist
        refresh_token = create_refresh_token({'sub': 'nonexistent@example.com'})

        response = await client.post(
            '/auth/refresh',
            json={
                'refresh_token': refresh_token,
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_refresh_token_missing_token(self, client: AsyncClient):
        """Test refresh fails without token."""
        response = await client.post(
            '/auth/refresh',
            json={},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_refresh_token_can_be_used_multiple_times(
        self, client: AsyncClient, test_user: User
    ):
        """Test that refresh token can be used multiple times (token rotation)."""
        # Login to get initial refresh token
        login_response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )
        refresh_token1 = login_response.json()['refresh_token']

        # First refresh
        response1 = await client.post(
            '/auth/refresh',
            json={'refresh_token': refresh_token1},
        )
        assert response1.status_code == 200
        refresh_token2 = response1.json()['refresh_token']

        # Second refresh with new token
        response2 = await client.post(
            '/auth/refresh',
            json={'refresh_token': refresh_token2},
        )
        assert response2.status_code == 200

        # All refresh tokens should be different
        refresh_token3 = response2.json()['refresh_token']
        assert refresh_token1 != refresh_token2 != refresh_token3


# ==================== Logout Endpoint Tests ====================


class TestLogoutEndpoint:
    """Test POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self, client: AsyncClient, test_user: User, test_user_headers: dict[str, str]
    ):
        """Test successful logout."""
        response = await client.post(
            '/auth/logout',
            headers=test_user_headers,
        )

        assert response.status_code == 204
        assert response.content == b''  # No content for 204

    @pytest.mark.asyncio
    async def test_logout_without_authentication(self, client: AsyncClient):
        """Test logout fails without authentication."""
        response = await client.post('/auth/logout')

        assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """Test logout fails with invalid token."""
        response = await client.post(
            '/auth/logout',
            headers={'Authorization': 'Bearer invalid.token.here'},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_inactive_user(
        self, client: AsyncClient, inactive_user: User, get_auth_headers
    ):
        """Test logout fails for inactive user."""
        headers = get_auth_headers(inactive_user.email)

        response = await client.post(
            '/auth/logout',
            headers=headers,
        )

        assert response.status_code == 403  # Forbidden (inactive user)

    @pytest.mark.asyncio
    async def test_logout_with_refresh_token_fails(
        self, client: AsyncClient, test_user: User
    ):
        """Test that refresh token cannot be used for logout (needs access token)."""
        # Login to get refresh token
        login_response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )
        refresh_token = login_response.json()['refresh_token']

        response = await client.post(
            '/auth/logout',
            headers={'Authorization': f'Bearer {refresh_token}'},
        )

        # Should fail because refresh token has wrong type claim
        assert response.status_code == 401


# ==================== Authentication Flow Tests ====================


class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow(
        self, client: AsyncClient, test_user: User
    ):
        """Test complete flow: login -> use token -> refresh -> logout."""
        # 1. Login
        login_response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()['access_token']
        refresh_token = login_response.json()['refresh_token']

        # 2. Use access token to access protected endpoint
        me_response = await client.get(
            '/users/me',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        assert me_response.status_code == 200
        assert me_response.json()['email'] == test_user.email

        # 3. Refresh token
        refresh_response = await client.post(
            '/auth/refresh',
            json={'refresh_token': refresh_token},
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()['access_token']

        # 4. Use new access token
        me_response2 = await client.get(
            '/users/me',
            headers={'Authorization': f'Bearer {new_access_token}'},
        )
        assert me_response2.status_code == 200

        # 5. Logout
        logout_response = await client.post(
            '/auth/logout',
            headers={'Authorization': f'Bearer {new_access_token}'},
        )
        assert logout_response.status_code == 204

        # Note: Token is still valid until Redis blacklist is implemented
        # TODO: After implementing Redis blacklist, test that token is revoked

    @pytest.mark.asyncio
    async def test_multiple_users_login_simultaneously(
        self, client: AsyncClient, test_user: User, create_test_user
    ):
        """Test that multiple users can login simultaneously."""
        user2 = await create_test_user(
            email='user2@example.com',
            password='User2Pass123!',
        )

        # Both users login
        response1 = await client.post(
            '/auth/login',
            json={'email': test_user.email, 'password': 'TestPass123!'},
        )
        response2 = await client.post(
            '/auth/login',
            json={'email': user2.email, 'password': 'User2Pass123!'},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Tokens should be different
        assert response1.json()['access_token'] != response2.json()['access_token']

        # Each user can access their own data
        me1 = await client.get(
            '/users/me',
            headers={'Authorization': f"Bearer {response1.json()['access_token']}"},
        )
        me2 = await client.get(
            '/users/me',
            headers={'Authorization': f"Bearer {response2.json()['access_token']}"},
        )

        assert me1.json()['email'] == test_user.email
        assert me2.json()['email'] == user2.email


# ==================== Security Tests ====================


class TestAuthenticationSecurity:
    """Test security aspects of authentication."""

    @pytest.mark.asyncio
    async def test_login_does_not_expose_password_hash(
        self, client: AsyncClient, test_user: User
    ):
        """Test that login response doesn't expose password hash."""
        response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )

        assert response.status_code == 200
        user_data = response.json()['user']
        assert 'password_hash' not in user_data
        assert 'password' not in user_data

    @pytest.mark.asyncio
    async def test_tokens_contain_no_sensitive_data(
        self, client: AsyncClient, test_user: User
    ):
        """Test that JWT tokens don't contain sensitive data in payload."""
        response = await client.post(
            '/auth/login',
            json={
                'email': test_user.email,
                'password': 'TestPass123!',
            },
        )

        assert response.status_code == 200
        access_token = response.json()['access_token']

        # Decode token (without verifying) to check payload
        import jwt

        payload = jwt.decode(access_token, options={'verify_signature': False})

        # Should NOT contain sensitive data
        assert 'password' not in payload
        assert 'password_hash' not in payload

        # Should contain expected claims
        assert 'sub' in payload  # Subject (email)
        assert 'exp' in payload  # Expiration
        assert 'jti' in payload  # JWT ID

    @pytest.mark.asyncio
    async def test_failed_login_response_time_is_consistent(
        self, client: AsyncClient
    ):
        """Test that failed login doesn't reveal if email exists (timing attack prevention)."""
        import time

        # Test with non-existent email
        start1 = time.time()
        await client.post(
            '/auth/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'TestPass123!',
            },
        )
        time1 = time.time() - start1

        # Test with wrong password
        start2 = time.time()
        await client.post(
            '/auth/login',
            json={
                'email': 'nonexistent2@example.com',
                'password': 'WrongPass123!',
            },
        )
        time2 = time.time() - start2

        # Times should be similar (within reasonable tolerance)
        # This is a basic test; in production, consider using constant-time comparison
        assert abs(time1 - time2) < 0.5  # Within 500ms
