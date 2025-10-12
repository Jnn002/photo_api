"""
User-specific test fixtures and factories.

This module provides fixtures for creating test users, roles, permissions,
and generating authentication tokens for testing.
"""

from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import Status
from app.core.security import create_access_token, hash_password
from app.users.models import Permission, Role, User
from app.users.repository import PermissionRepository, RoleRepository, UserRepository


# ==================== Permission Factories ====================


@pytest_asyncio.fixture
async def create_test_permission(db_session: AsyncSession):
    """
    Factory fixture for creating test permissions.

    Usage:
        permission = await create_test_permission(
            code='test.permission',
            name='Test Permission'
        )
    """
    async def _create_permission(
        code: str = 'test.permission',
        name: str = 'Test Permission',
        description: str | None = 'Test permission description',
        module: str = 'test',
        status: Status = Status.ACTIVE,
    ) -> Permission:
        permission = Permission(
            code=code,
            name=name,
            description=description,
            module=module,
            status=status,
        )
        repo = PermissionRepository(db_session)
        permission = await repo.create(permission)
        await db_session.commit()
        return permission

    return _create_permission


@pytest_asyncio.fixture
async def test_permission(create_test_permission) -> Permission:
    """Pre-created test permission for convenience."""
    return await create_test_permission(
        code='test.read',
        name='Test Read Permission',
        module='test',
    )


# ==================== Role Factories ====================


@pytest_asyncio.fixture
async def create_test_role(db_session: AsyncSession):
    """
    Factory fixture for creating test roles.

    Usage:
        role = await create_test_role(
            name='TestRole',
            description='A test role'
        )
    """
    async def _create_role(
        name: str = 'TestRole',
        description: str | None = 'Test role description',
        status: Status = Status.ACTIVE,
    ) -> Role:
        role = Role(
            name=name,
            description=description,
            status=status,
        )
        repo = RoleRepository(db_session)
        role = await repo.create(role)
        await db_session.commit()
        return role

    return _create_role


@pytest_asyncio.fixture
async def test_role(create_test_role) -> Role:
    """Pre-created test role for convenience."""
    return await create_test_role(name='TestRole', description='A test role')


@pytest_asyncio.fixture
async def admin_role(create_test_role) -> Role:
    """Pre-created admin role for testing."""
    return await create_test_role(name='Admin', description='Administrator role')


@pytest_asyncio.fixture
async def coordinator_role(create_test_role) -> Role:
    """Pre-created coordinator role for testing."""
    return await create_test_role(name='Coordinator', description='Coordinator role')


@pytest_asyncio.fixture
async def photographer_role(create_test_role) -> Role:
    """Pre-created photographer role for testing."""
    return await create_test_role(name='Photographer', description='Photographer role')


# ==================== User Factories ====================


@pytest_asyncio.fixture
async def create_test_user(db_session: AsyncSession):
    """
    Factory fixture for creating test users.

    Usage:
        user = await create_test_user(
            email='test@example.com',
            password='SecurePass123!'
        )
    """
    async def _create_user(
        full_name: str = 'Test User',
        email: str = 'test@example.com',
        password: str = 'SecurePass123!',
        phone: str | None = '+502 1234-5678',
        status: Status = Status.ACTIVE,
        created_by: int | None = None,
    ) -> User:
        # Hash password
        password_hash = hash_password(password)

        user = User(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            phone=phone,
            status=status,
            created_by=created_by,
        )
        repo = UserRepository(db_session)
        user = await repo.create(user)
        await db_session.commit()
        return user

    return _create_user


@pytest_asyncio.fixture
async def test_user(create_test_user) -> User:
    """Pre-created test user for convenience."""
    return await create_test_user(
        full_name='Test User',
        email='testuser@example.com',
        password='TestPass123!',
    )


@pytest_asyncio.fixture
async def inactive_user(create_test_user) -> User:
    """Pre-created inactive user for testing."""
    return await create_test_user(
        full_name='Inactive User',
        email='inactive@example.com',
        password='InactivePass123!',
        status=Status.INACTIVE,
    )


@pytest_asyncio.fixture
async def admin_user(create_test_user, admin_role, db_session) -> User:
    """Pre-created admin user with admin role."""
    user = await create_test_user(
        full_name='Admin User',
        email='admin@example.com',
        password='AdminPass123!',
    )
    # Assign admin role
    repo = UserRepository(db_session)
    await repo.assign_role(user.id, admin_role.id, user.id)  # type: ignore
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def coordinator_user(create_test_user, coordinator_role, db_session) -> User:
    """Pre-created coordinator user with coordinator role."""
    user = await create_test_user(
        full_name='Coordinator User',
        email='coordinator@example.com',
        password='CoordPass123!',
    )
    # Assign coordinator role
    repo = UserRepository(db_session)
    await repo.assign_role(user.id, coordinator_role.id, user.id)  # type: ignore
    await db_session.commit()
    return user


# ==================== User with Multiple Roles ====================


@pytest_asyncio.fixture
async def create_user_with_roles(db_session: AsyncSession, create_test_user):
    """
    Factory fixture for creating users with specific roles.

    Usage:
        user = await create_user_with_roles(
            email='multi@example.com',
            roles=[role1, role2]
        )
    """
    async def _create_user_with_roles(
        email: str,
        password: str = 'SecurePass123!',
        roles: list[Role] = [],
        **user_kwargs,
    ) -> User:
        user = await create_test_user(email=email, password=password, **user_kwargs)
        repo = UserRepository(db_session)
        for role in roles:
            await repo.assign_role(user.id, role.id, user.id)  # type: ignore
        await db_session.commit()
        return user

    return _create_user_with_roles


# ==================== Authentication Helpers ====================


@pytest.fixture
def get_auth_headers():
    """
    Factory function for generating JWT authentication headers.

    Usage:
        headers = get_auth_headers('user@example.com')
        response = await client.get('/users/me', headers=headers)
    """
    def _get_headers(email: str) -> dict[str, str]:
        token = create_access_token(data={'sub': email})
        return {'Authorization': f'Bearer {token}'}

    return _get_headers


@pytest_asyncio.fixture
async def test_user_headers(test_user, get_auth_headers) -> dict[str, str]:
    """Pre-generated auth headers for test user."""
    return get_auth_headers(test_user.email)


@pytest_asyncio.fixture
async def admin_headers(admin_user, get_auth_headers) -> dict[str, str]:
    """Pre-generated auth headers for admin user."""
    return get_auth_headers(admin_user.email)


@pytest_asyncio.fixture
async def coordinator_headers(coordinator_user, get_auth_headers) -> dict[str, str]:
    """Pre-generated auth headers for coordinator user."""
    return get_auth_headers(coordinator_user.email)


# ==================== Permission Assignment Helpers ====================


@pytest_asyncio.fixture
async def assign_permission_to_role(db_session: AsyncSession):
    """
    Helper fixture for assigning permissions to roles.

    Usage:
        await assign_permission_to_role(role, permission)
    """
    async def _assign(role: Role, permission: Permission, granted_by: int = 1) -> None:
        repo = RoleRepository(db_session)
        await repo.assign_permission(role.id, permission.id, granted_by)  # type: ignore
        await db_session.commit()

    return _assign


# ==================== Batch Data Creation ====================


@pytest_asyncio.fixture
async def create_multiple_users(create_test_user):
    """
    Factory for creating multiple users at once.

    Usage:
        users = await create_multiple_users(count=5)
    """
    async def _create_multiple(
        count: int = 5,
        email_prefix: str = 'user',
        **user_kwargs,
    ) -> list[User]:
        users = []
        for i in range(count):
            user = await create_test_user(
                email=f'{email_prefix}{i}@example.com',
                full_name=f'User {i}',
                **user_kwargs,
            )
            users.append(user)
        return users

    return _create_multiple
