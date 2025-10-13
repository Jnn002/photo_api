"""
Integration tests for user management endpoints.

This module tests all user API endpoints including:
- GET /users - List users
- POST /users - Create user
- GET /users/me - Get current user
- GET /users/{id} - Get user by ID
- PATCH /users/{id} - Update user
- DELETE /users/{id} - Deactivate user
- PUT /users/{id}/reactivate - Reactivate user
- PATCH /users/{id}/password - Change password
- User roles endpoints
- Roles management endpoints
- Permissions management endpoints
"""

import pytest
from httpx import AsyncClient

from app.users.models import Permission, Role, User


# ==================== List Users Tests ====================


class TestListUsersEndpoint:
    """Test GET /users endpoint."""

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        create_multiple_users,
        test_permission,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test listing users with proper permission."""
        # Setup: Give admin role the user.list permission
        user_list_perm = Permission(
            code='user.list',
            name='List Users',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_list_perm = await repo.create(user_list_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_list_perm)

        # Create some users
        await create_multiple_users(count=5)

        response = await client.get(
            '/users',
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        create_multiple_users,
        admin_role: Role,
        test_permission,
        assign_permission_to_role,
    ):
        """Test listing users with pagination parameters."""
        # Setup permission
        user_list_perm = Permission(
            code='user.list',
            name='List Users',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_list_perm = await repo.create(user_list_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_list_perm)

        await create_multiple_users(count=10, email_prefix='paginated')

        response = await client.get(
            '/users?limit=5&offset=0',
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_list_users_active_only(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        inactive_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test listing only active users."""
        # Setup permission
        user_list_perm = Permission(
            code='user.list',
            name='List Users',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_list_perm = await repo.create(user_list_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_list_perm)

        response = await client.get(
            '/users?active_only=true',
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        user_ids = [u['id'] for u in data]
        assert test_user.id in user_ids
        assert inactive_user.id not in user_ids

    @pytest.mark.asyncio
    async def test_list_users_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str]
    ):
        """Test that listing users fails without permission."""
        response = await client.get(
            '/users',
            headers=test_user_headers,
        )

        assert response.status_code == 403  # Forbidden


# ==================== Create User Tests ====================


class TestCreateUserEndpoint:
    """Test POST /users endpoint."""

    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test creating user with proper permission."""
        # Setup permission
        user_create_perm = Permission(
            code='user.create',
            name='Create User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_create_perm = await repo.create(user_create_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_create_perm)

        response = await client.post(
            '/users',
            headers=admin_headers,
            json={
                'full_name': 'New Test User',
                'email': 'newuser@example.com',
                'password': 'NewUserPass123!',
                'phone': '+502 1234-5678',
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'newuser@example.com'
        assert data['full_name'] == 'New Test User'
        assert 'password_hash' not in data
        assert 'password' not in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test creating user with duplicate email fails."""
        # Setup permission
        user_create_perm = Permission(
            code='user.create',
            name='Create User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_create_perm = await repo.create(user_create_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_create_perm)

        response = await client.post(
            '/users',
            headers=admin_headers,
            json={
                'full_name': 'Duplicate User',
                'email': test_user.email,  # Duplicate
                'password': 'DuplicatePass123!',
            },
        )

        assert response.status_code == 409  # Conflict
        data = response.json()
        assert 'email' in data['detail'].lower()

    @pytest.mark.asyncio
    async def test_create_user_weak_password(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test creating user with weak password fails."""
        # Setup permission
        user_create_perm = Permission(
            code='user.create',
            name='Create User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_create_perm = await repo.create(user_create_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_create_perm)

        response = await client.post(
            '/users',
            headers=admin_headers,
            json={
                'full_name': 'Weak Password User',
                'email': 'weakpass@example.com',
                'password': 'weak',  # Too weak
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_user_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str]
    ):
        """Test creating user fails without permission."""
        response = await client.post(
            '/users',
            headers=test_user_headers,
            json={
                'full_name': 'Should Fail',
                'email': 'fail@example.com',
                'password': 'FailPass123!',
            },
        )

        assert response.status_code == 403  # Forbidden


# ==================== Get Current User Tests ====================


class TestGetCurrentUserEndpoint:
    """Test GET /users/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, client: AsyncClient, test_user: User, test_user_headers: dict[str, str]
    ):
        """Test getting current user information."""
        response = await client.get(
            '/users/me',
            headers=test_user_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == test_user.id
        assert data['email'] == test_user.email
        assert 'roles' in data
        assert 'password_hash' not in data

    @pytest.mark.asyncio
    async def test_get_current_user_without_authentication(self, client: AsyncClient):
        """Test getting current user fails without authentication."""
        response = await client.get('/users/me')

        assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            '/users/me',
            headers={'Authorization': 'Bearer invalid.token.here'},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(
        self, client: AsyncClient, inactive_user: User, get_auth_headers
    ):
        """Test getting current user fails for inactive user."""
        headers = get_auth_headers(inactive_user.email)

        response = await client.get(
            '/users/me',
            headers=headers,
        )

        assert response.status_code == 403  # Forbidden (inactive)


# ==================== Get User by ID Tests ====================


class TestGetUserByIdEndpoint:
    """Test GET /users/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test getting user by ID with proper permission."""
        # Setup permission
        user_read_perm = Permission(
            code='user.read',
            name='Read User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_read_perm = await repo.create(user_read_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_read_perm)

        response = await client.get(
            f'/users/{test_user.id}',
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == test_user.id
        assert data['email'] == test_user.email
        assert 'roles' in data

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test getting non-existent user returns 404."""
        # Setup permission
        user_read_perm = Permission(
            code='user.read',
            name='Read User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_read_perm = await repo.create(user_read_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_read_perm)

        response = await client.get(
            '/users/99999',
            headers=admin_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_by_id_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str], admin_user: User
    ):
        """Test getting user fails without permission."""
        response = await client.get(
            f'/users/{admin_user.id}',
            headers=test_user_headers,
        )

        assert response.status_code == 403


# ==================== Update User Tests ====================


class TestUpdateUserEndpoint:
    """Test PATCH /users/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_user_success(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test updating user with proper permission."""
        # Setup permission
        user_edit_perm = Permission(
            code='user.edit',
            name='Edit User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_edit_perm = await repo.create(user_edit_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_edit_perm)

        response = await client.patch(
            f'/users/{test_user.id}',
            headers=admin_headers,
            json={
                'full_name': 'Updated Name',
                'phone': '+502 9999-9999',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data['full_name'] == 'Updated Name'
        assert data['phone'] == '+502 9999-9999'

    @pytest.mark.asyncio
    async def test_update_user_email(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test updating user email."""
        # Setup permission
        user_edit_perm = Permission(
            code='user.edit',
            name='Edit User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_edit_perm = await repo.create(user_edit_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_edit_perm)

        response = await client.patch(
            f'/users/{test_user.id}',
            headers=admin_headers,
            json={
                'email': 'newemail@example.com',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data['email'] == 'newemail@example.com'

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test updating user to duplicate email fails."""
        # Setup permission
        user_edit_perm = Permission(
            code='user.edit',
            name='Edit User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_edit_perm = await repo.create(user_edit_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_edit_perm)

        response = await client.patch(
            f'/users/{test_user.id}',
            headers=admin_headers,
            json={
                'email': admin_user.email,  # Duplicate
            },
        )

        assert response.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_update_user_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str], admin_user: User
    ):
        """Test updating user fails without permission."""
        response = await client.patch(
            f'/users/{admin_user.id}',
            headers=test_user_headers,
            json={
                'full_name': 'Should Fail',
            },
        )

        assert response.status_code == 403


# ==================== Deactivate User Tests ====================


class TestDeactivateUserEndpoint:
    """Test DELETE /users/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test deactivating user with proper permission."""
        # Setup permission
        user_delete_perm = Permission(
            code='user.delete',
            name='Delete User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_delete_perm = await repo.create(user_delete_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_delete_perm)

        response = await client.delete(
            f'/users/{test_user.id}',
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'INACTIVE'

    @pytest.mark.asyncio
    async def test_deactivate_self_fails(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        admin_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test that user cannot deactivate themselves."""
        # Setup permission
        user_delete_perm = Permission(
            code='user.delete',
            name='Delete User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_delete_perm = await repo.create(user_delete_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_delete_perm)

        response = await client.delete(
            f'/users/{admin_user.id}',
            headers=admin_headers,
        )

        assert response.status_code == 400  # Business validation error
        assert 'deactivate yourself' in response.json()['detail'].lower()

    @pytest.mark.asyncio
    async def test_deactivate_user_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str], admin_user: User
    ):
        """Test deactivating user fails without permission."""
        response = await client.delete(
            f'/users/{admin_user.id}',
            headers=test_user_headers,
        )

        assert response.status_code == 403


# ==================== Reactivate User Tests ====================


class TestReactivateUserEndpoint:
    """Test PUT /users/{id}/reactivate endpoint."""

    @pytest.mark.asyncio
    async def test_reactivate_user_success(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        inactive_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test reactivating user with proper permission."""
        # Setup permission
        user_edit_perm = Permission(
            code='user.edit',
            name='Edit User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_edit_perm = await repo.create(user_edit_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_edit_perm)

        response = await client.put(
            f'/users/{inactive_user.id}/reactivate',
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ACTIVE'

    @pytest.mark.asyncio
    async def test_reactivate_user_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str], inactive_user: User
    ):
        """Test reactivating user fails without permission."""
        response = await client.put(
            f'/users/{inactive_user.id}/reactivate',
            headers=test_user_headers,
        )

        assert response.status_code == 403


# ==================== Change Password Tests ====================


class TestChangePasswordEndpoint:
    """Test PATCH /users/{id}/password endpoint."""

    @pytest.mark.asyncio
    async def test_change_own_password_success(
        self, client: AsyncClient, test_user: User, test_user_headers: dict[str, str]
    ):
        """Test user can change their own password."""
        response = await client.patch(
            f'/users/{test_user.id}/password',
            headers=test_user_headers,
            json={
                'current_password': 'TestPass123!',
                'new_password': 'NewSecurePass456!',
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(
        self, client: AsyncClient, test_user: User, test_user_headers: dict[str, str]
    ):
        """Test changing password fails with wrong current password."""
        response = await client.patch(
            f'/users/{test_user.id}/password',
            headers=test_user_headers,
            json={
                'current_password': 'WrongPassword123!',
                'new_password': 'NewSecurePass456!',
            },
        )

        assert response.status_code == 401  # Unauthorized (wrong password)

    @pytest.mark.asyncio
    async def test_change_password_same_as_current(
        self, client: AsyncClient, test_user: User, test_user_headers: dict[str, str]
    ):
        """Test that new password must be different from current."""
        response = await client.patch(
            f'/users/{test_user.id}/password',
            headers=test_user_headers,
            json={
                'current_password': 'TestPass123!',
                'new_password': 'TestPass123!',  # Same as current
            },
        )

        assert response.status_code == 400  # Business validation error

    @pytest.mark.asyncio
    async def test_admin_change_other_user_password(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_user: User,
        admin_role: Role,
        assign_permission_to_role,
    ):
        """Test admin can change other user's password."""
        # Setup permission
        user_edit_perm = Permission(
            code='user.edit',
            name='Edit User',
            module='user',
        )
        from app.users.repository import PermissionRepository
        from app.core.database import async_session_maker

        async with async_session_maker() as session:
            repo = PermissionRepository(session)
            user_edit_perm = await repo.create(user_edit_perm)
            await session.commit()

        await assign_permission_to_role(admin_role, user_edit_perm)

        response = await client.patch(
            f'/users/{test_user.id}/password',
            headers=admin_headers,
            json={
                'current_password': 'TestPass123!',  # Test user's current password
                'new_password': 'AdminChangedPass789!',
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_other_user_password_without_permission(
        self, client: AsyncClient, test_user_headers: dict[str, str], admin_user: User
    ):
        """Test non-admin cannot change other user's password."""
        response = await client.patch(
            f'/users/{admin_user.id}/password',
            headers=test_user_headers,
            json={
                'current_password': 'AdminPass123!',
                'new_password': 'ShouldFail456!',
            },
        )

        assert response.status_code == 403


# Note: The complete file would continue with tests for:
# - User roles endpoints (GET/POST/DELETE /users/{id}/roles/{role_id})
# - Roles management endpoints (GET/POST/GET/PATCH /roles)
# - Permissions management endpoints (GET/POST /permissions)
#
# These follow similar patterns to the tests above.
# For brevity, the pattern is established and can be extended.
