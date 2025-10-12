"""
Role-Based Access Control (RBAC) system for the Photography Studio API.

This module provides permission checking and role-based authorization
using FastAPI dependencies.
"""

from typing import Callable

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import CurrentActiveUser, SessionDep
from app.core.enums import Status
from app.core.exceptions import InsufficientPermissionsException
from app.users.models import User
from app.users.repository import UserRepository


async def get_user_permissions(user: User, db: AsyncSession) -> set[str]:
    """
    Get all permission codes for a user through their roles.

    Args:
        user: The user to get permissions for
        db: Database session

    Returns:
        Set of permission codes (e.g., {'session.create', 'client.read'})
    """
    user_repo = UserRepository(db)
    permissions = await user_repo.get_user_permissions(user.id)
    return {perm.code for perm in permissions}


async def check_user_permission(
    user: User, permission_code: str, db: AsyncSession
) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: User to check permissions for
        permission_code: Permission code to check (e.g., 'session.create')
        db: Database session

    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = await get_user_permissions(user, db)
    return permission_code in user_permissions


async def check_user_role(user: User, role_name: str, db: AsyncSession) -> bool:
    """
    Check if a user has a specific role.

    Args:
        user: User to check roles for
        role_name: Role name to check (e.g., 'Admin', 'Coordinator')
        db: Database session

    Returns:
        True if user has role, False otherwise
    """
    # Eager load roles if not already loaded
    if not user.roles:
        from app.users.repository import UserRepository

        # TODO: check this type ignore
        user_repo = UserRepository(db)
        user = await user_repo.get_with_roles(user.id)  # type: ignore
        if not user:
            return False

    # Check if user has the role and it's active
    for role in user.roles:
        if role.name == role_name and role.status == Status.ACTIVE:
            return True

    return False


def require_permission(permission_code: str) -> Callable:
    """
    Dependency factory to require a specific permission.

    Creates a FastAPI dependency that checks if the current user
    has the specified permission.

    Args:
        permission_code: Permission code required (e.g., 'session.create')

    Returns:
        Dependency function that validates permission

    Raises:
        InsufficientPermissionsException: If user lacks the permission

    Example:
        @router.post('/sessions')
        async def create_session(
            user: Annotated[User, Depends(require_permission('session.create'))],
            db: SessionDep
        ):
            # User is guaranteed to have 'session.create' permission
            ...
    """

    async def permission_checker(
        current_user: CurrentActiveUser,
        db: SessionDep,
    ) -> User:
        """Check if current user has required permission."""
        has_permission = await check_user_permission(current_user, permission_code, db)

        if not has_permission:
            raise InsufficientPermissionsException()

        return current_user

    return permission_checker


def require_role(role_name: str) -> Callable:
    """
    Dependency factory to require a specific role.

    Creates a FastAPI dependency that checks if the current user
    has the specified role.

    Args:
        role_name: Role name required (e.g., 'Admin', 'Coordinator')

    Returns:
        Dependency function that validates role

    Raises:
        InsufficientPermissionsException: If user lacks the role

    Example:
        @router.delete('/users/{user_id}')
        async def delete_user(
            user: Annotated[User, Depends(require_role('Admin'))],
            user_id: int
        ):
            # User is guaranteed to have 'Admin' role
            ...
    """

    async def role_checker(
        current_user: CurrentActiveUser,
        db: SessionDep,
    ) -> User:
        """Check if current user has required role."""
        has_role = await check_user_role(current_user, role_name, db)

        if not has_role:
            raise InsufficientPermissionsException()

        return current_user

    return role_checker


def require_any_permission(*permission_codes: str) -> Callable:
    """
    Dependency factory to require ANY of the specified permissions.

    User needs at least one of the permissions to pass.

    Args:
        *permission_codes: Variable number of permission codes

    Returns:
        Dependency function that validates permissions

    Raises:
        InsufficientPermissionsException: If user lacks all permissions

    Example:
        @router.get('/reports')
        async def get_reports(
            user: Annotated[User, Depends(require_any_permission(
                'report.admin',
                'report.view'
            ))]
        ):
            # User has either 'report.admin' OR 'report.view'
            ...
    """

    async def permission_checker(
        current_user: CurrentActiveUser,
        db: SessionDep,
    ) -> User:
        """Check if current user has any of the required permissions."""
        user_permissions = await get_user_permissions(current_user, db)

        has_any_permission = any(perm in user_permissions for perm in permission_codes)

        if not has_any_permission:
            raise InsufficientPermissionsException()

        return current_user

    return permission_checker


def require_all_permissions(*permission_codes: str) -> Callable:
    """
    Dependency factory to require ALL of the specified permissions.

    User needs all permissions to pass.

    Args:
        *permission_codes: Variable number of permission codes

    Returns:
        Dependency function that validates permissions

    Raises:
        InsufficientPermissionsException: If user lacks any permission

    Example:
        @router.post('/sessions/{id}/finalize')
        async def finalize_session(
            user: Annotated[User, Depends(require_all_permissions(
                'session.edit',
                'payment.validate'
            ))]
        ):
            # User has both 'session.edit' AND 'payment.validate'
            ...
    """

    async def permission_checker(
        current_user: CurrentActiveUser,
        db: SessionDep,
    ) -> User:
        """Check if current user has all required permissions."""
        user_permissions = await get_user_permissions(current_user, db)

        has_all_permissions = all(perm in user_permissions for perm in permission_codes)

        if not has_all_permissions:
            raise InsufficientPermissionsException()

        return current_user

    return permission_checker


def require_any_role(*role_names: str) -> Callable:
    """
    Dependency factory to require ANY of the specified roles.

    User needs at least one of the roles to pass.

    Args:
        *role_names: Variable number of role names

    Returns:
        Dependency function that validates roles

    Raises:
        InsufficientPermissionsException: If user lacks all roles

    Example:
        @router.get('/dashboard')
        async def get_dashboard(
            user: Annotated[User, Depends(require_any_role(
                'Admin',
                'Coordinator'
            ))]
        ):
            # User is either Admin OR Coordinator
            ...
    """

    async def role_checker(
        current_user: CurrentActiveUser,
        db: SessionDep,
    ) -> User:
        """Check if current user has any of the required roles."""
        for role_name in role_names:
            if await check_user_role(current_user, role_name, db):
                return current_user

        raise InsufficientPermissionsException()

    return role_checker


# ==================== Common Permission Combinations ====================

# Admin-only dependency
require_admin = require_role('Admin')

# Coordinator or Admin dependency
require_coordinator_or_admin = require_any_role('Admin', 'Coordinator')

# Any staff member (not just clients)
require_staff = require_any_role('Admin', 'Coordinator', 'Photographer', 'Editor')


# ==================== Type Aliases for Common Permissions ====================

from typing import Annotated

AdminUser = Annotated[User, Depends(require_admin)]
"""
Dependency for requiring Admin role.

Usage:
    @router.delete('/users/{user_id}')
    async def delete_user(user: AdminUser, user_id: int):
        ...
"""

CoordinatorOrAdmin = Annotated[User, Depends(require_coordinator_or_admin)]
"""
Dependency for requiring Coordinator or Admin role.

Usage:
    @router.post('/sessions')
    async def create_session(user: CoordinatorOrAdmin):
        ...
"""

StaffUser = Annotated[User, Depends(require_staff)]
"""
Dependency for requiring any staff role (Admin, Coordinator, Photographer, Editor).

Usage:
    @router.get('/dashboard')
    async def get_dashboard(user: StaffUser):
        ...
"""
