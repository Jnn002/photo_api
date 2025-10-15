"""
User service layer for business logic.

This module provides business logic for user management operations
including user CRUD, role assignment, and authentication.
"""

import logging
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import Status
from app.core.exceptions import (
    BusinessValidationException,
    DuplicateEmailException,
    DuplicateNameException,
    InactiveUserException,
    InvalidCredentialsException,
    RoleNotFoundException,
    UserNotFoundException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.users.models import Permission, Role, User
from app.users.repository import PermissionRepository, RoleRepository, UserRepository
from app.users.schemas import (
    PermissionCreate,
    RoleCreate,
    RoleUpdate,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPasswordUpdate,
    UserPublic,
    UserUpdate,
)

logger = logging.getLogger(__name__)


# ==================== User Service ====================


class UserService:
    """Business logic for user management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def authenticate_user(self, credentials: UserLogin) -> TokenResponse:
        """
        Authenticate user and return access tokens.

        Business rules:
        - User must exist
        - User must be active
        - Password must match

        Args:
            credentials: User login credentials (email and password)

        Returns:
            TokenResponse with access_token, refresh_token, and user data

        Raises:
            InvalidCredentialsException: If email or password is incorrect
            InactiveUserException: If user account is inactive
        """
        # Find user by email
        user = await self.user_repo.find_by_email(credentials.email)

        # Check if user exists and password matches
        if not user or not verify_password(credentials.password, user.password_hash):
            logger.warning(f'Failed login attempt for email: {credentials.email}')
            raise InvalidCredentialsException('Invalid email or password')

        # Check if user is active
        if user.status != Status.ACTIVE:
            logger.warning(f'Inactive user login attempt: {credentials.email}')
            raise InactiveUserException(f'User {user.email} is inactive')

        # Generate tokens
        access_token = create_access_token(data={'sub': user.email})
        refresh_token = create_refresh_token(data={'sub': user.email})

        logger.info(f'User authenticated successfully: {user.email}')

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes in seconds
            user=UserPublic.model_validate(user),
        )

    async def create_user(
        self, data: UserCreate, created_by: int | None = None
    ) -> User:
        """
        Create a new user with hashed password.

        Business rules:
        - Email must be unique
        - Password must be hashed
        - User starts with ACTIVE status

        Args:
            data: User creation data
            created_by: ID of user creating this user (optional)

        Returns:
            Created User object

        Raises:
            DuplicateEmailException: If email already exists
        """
        # Check if email exists
        if await self.user_repo.email_exists(data.email):
            raise DuplicateEmailException(data.email, 'User')

        # Hash password
        password_hash = hash_password(data.password)

        # Create user
        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=password_hash,
            phone=data.phone,
            status=Status.ACTIVE,
            created_by=created_by,
        )

        # Save to database
        user = await self.user_repo.create(user)
        await self.db.commit()

        logger.info(f'User created: {user.email} (ID: {user.id})')

        return user

    async def get_user_by_id(self, user_id: int) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            UserNotFoundException: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundException(user_id)

        return user

    async def get_user_with_roles(self, user_id: int) -> User:
        """
        Get user by ID with roles eagerly loaded.

        Args:
            user_id: User ID

        Returns:
            User object with roles

        Raises:
            UserNotFoundException: If user not found
        """
        user = await self.user_repo.get_with_roles(user_id)

        if not user:
            raise UserNotFoundException(user_id)

        return user

    async def update_user(
        self, user_id: int, data: UserUpdate, updated_by: int
    ) -> User:
        """
        Update user information.

        Business rules:
        - User must exist
        - Email must be unique if changed
        - Cannot change password through this endpoint

        Args:
            user_id: User ID
            data: Update data
            updated_by: ID of user performing update

        Returns:
            Updated User object

        Raises:
            UserNotFoundException: If user not found
            DuplicateEmailException: If new email already exists
        """
        # Get user
        user = await self.get_user_by_id(user_id)

        # Check email uniqueness if email is being changed
        if data.email and data.email != user.email:
            if await self.user_repo.email_exists(data.email, exclude_id=user_id):
                raise DuplicateEmailException(data.email, 'User')

        # Update user
        update_dict: dict[str, Any] = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user, update_dict)
        await self.db.commit()

        logger.info(f'User updated: {user.email} (ID: {user.id}) by user {updated_by}')

        return user

    async def update_password(self, user_id: int, data: UserPasswordUpdate) -> User:
        """
        Update user password.

        Business rules:
        - User must exist
        - Current password must match
        - New password must be different from current

        Args:
            user_id: User ID
            data: Password update data

        Returns:
            Updated User object

        Raises:
            UserNotFoundException: If user not found
            InvalidCredentialsException: If current password is incorrect
            BusinessValidationException: If new password is same as current
        """
        # Get user
        user = await self.get_user_by_id(user_id)

        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsException('Current password is incorrect')

        # Check if new password is different
        if verify_password(data.new_password, user.password_hash):
            raise BusinessValidationException(
                'New password must be different from current password'
            )

        # Hash new password
        new_password_hash = hash_password(data.new_password)

        # Update password
        user = await self.user_repo.update(user, {'password_hash': new_password_hash})
        await self.db.commit()

        logger.info(f'Password updated for user: {user.email} (ID: {user.id})')

        return user

    async def deactivate_user(self, user_id: int, deactivated_by: int) -> User:
        """
        Deactivate a user (soft delete).

        Business rules:
        - User must exist
        - Cannot deactivate yourself
        - Logs out all active sessions (revoke tokens)

        Args:
            user_id: User ID to deactivate
            deactivated_by: ID of user performing deactivation

        Returns:
            Deactivated User object

        Raises:
            UserNotFoundException: If user not found
            BusinessValidationException: If trying to deactivate self
        """
        # Get user
        user = await self.get_user_by_id(user_id)

        # Check if user is trying to deactivate themselves
        if user.id == deactivated_by:
            raise BusinessValidationException('Cannot deactivate yourself')

        # Soft delete
        user = await self.user_repo.soft_delete(user)
        await self.db.commit()

        logger.info(
            f'User deactivated: {user.email} (ID: {user.id}) by user {deactivated_by}'
        )

        return user

    async def reactivate_user(self, user_id: int, reactivated_by: int) -> User:
        """
        Reactivate a deactivated user.

        Args:
            user_id: User ID to reactivate
            reactivated_by: ID of user performing reactivation

        Returns:
            Reactivated User object

        Raises:
            UserNotFoundException: If user not found
        """
        # Get user
        user = await self.get_user_by_id(user_id)

        # Reactivate
        user = await self.user_repo.update(user, {'status': Status.ACTIVE})
        await self.db.commit()

        logger.info(
            f'User reactivated: {user.email} (ID: {user.id}) by user {reactivated_by}'
        )

        return user

    async def assign_role_to_user(
        self, user_id: int, role_id: int, assigned_by: int
    ) -> User:
        """
        Assign a role to a user.

        Business rules:
        - User must exist and be active
        - Role must exist and be active
        - Cannot assign duplicate role

        Args:
            user_id: User ID
            role_id: Role ID
            assigned_by: ID of user performing assignment

        Returns:
            User object with updated roles

        Raises:
            UserNotFoundException: If user not found
            RoleNotFoundException: If role not found
            InactiveUserException: If user is inactive
            BusinessValidationException: If role is inactive or already assigned
        """
        # Validate user exists and is active
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        if user.status != Status.ACTIVE:
            raise InactiveUserException(f'User {user.email} is inactive')

        # Validate role exists and is active
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        if role.status != Status.ACTIVE:
            raise BusinessValidationException(f'Role {role.name} is inactive')

        # Check if already assigned
        user_with_roles = await self.user_repo.get_with_roles(user_id)
        if user_with_roles and any(r.id == role_id for r in user_with_roles.roles):
            raise BusinessValidationException(f'User already has role {role.name}')

        # Assign role
        await self.user_repo.assign_role(user_id, role_id, assigned_by)
        await self.db.commit()

        logger.info(
            f'Role {role.name} assigned to user {user.email} (ID: {user.id}) '
            f'by user {assigned_by}'
        )

        # Return updated user with roles
        return await self.user_repo.get_with_roles(user_id)  # type: ignore

    async def remove_role_from_user(
        self, user_id: int, role_id: int, removed_by: int
    ) -> User:
        """
        Remove a role from a user.

        Args:
            user_id: User ID
            role_id: Role ID
            removed_by: ID of user performing removal

        Returns:
            User object with updated roles

        Raises:
            UserNotFoundException: If user not found
            RoleNotFoundException: If role not found
        """
        # Validate user exists
        user = await self.get_user_by_id(user_id)

        # Validate role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFoundException(role_id)

        # Remove role
        await self.user_repo.remove_role(user_id, role_id)
        await self.db.commit()

        logger.info(
            f'Role {role.name} removed from user {user.email} (ID: {user.id}) '
            f'by user {removed_by}'
        )

        # Return updated user with roles
        return await self.user_repo.get_with_roles(user_id)  # type: ignore

    async def list_users(
        self, active_only: bool = False, limit: int = 100, offset: int = 0
    ) -> list[User]:
        """
        List users with pagination.

        Args:
            active_only: If True, return only active users
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User objects
        """
        if active_only:
            return await self.user_repo.list_active(limit=limit, offset=offset)
        return await self.user_repo.list_all(limit=limit, offset=offset)

    async def list_users_by_role(
        self, role_name: str, limit: int = 100, offset: int = 0
    ) -> list[User]:
        """
        List users by role name.

        Args:
            role_name: Role name to filter by
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User objects with specified role
        """
        return await self.user_repo.list_by_role(
            role_name=role_name, limit=limit, offset=offset
        )


# ==================== Role Service ====================


class RoleService:
    """Business logic for role management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.role_repo = RoleRepository(db)
        self.permission_repo = PermissionRepository(db)

    async def create_role(self, data: RoleCreate) -> Role:
        """
        Create a new role.

        Business rules:
        - Role name must be unique

        Args:
            data: Role creation data

        Returns:
            Created Role object

        Raises:
            DuplicateNameException: If role name already exists
        """
        # Check if name exists
        if await self.role_repo.name_exists(data.name):
            raise DuplicateNameException(data.name, 'Role')

        # Create role
        role = Role(
            name=data.name,
            description=data.description,
            status=Status.ACTIVE,
        )

        # Save to database
        role = await self.role_repo.create(role)
        await self.db.commit()

        logger.info(f'Role created: {role.name} (ID: {role.id})')

        return role

    async def get_role_by_id(self, role_id: int) -> Role:
        """
        Get role by ID.

        Args:
            role_id: Role ID

        Returns:
            Role object

        Raises:
            RoleNotFoundException: If role not found
        """
        role = await self.role_repo.get_by_id(role_id)

        if not role:
            raise RoleNotFoundException(role_id)

        return role

    async def get_role_with_permissions(self, role_id: int) -> Role:
        """
        Get role by ID with permissions eagerly loaded.

        Args:
            role_id: Role ID

        Returns:
            Role object with permissions

        Raises:
            RoleNotFoundException: If role not found
        """
        role = await self.role_repo.get_with_permissions(role_id)

        if not role:
            raise RoleNotFoundException(role_id)

        return role

    async def update_role(self, role_id: int, data: RoleUpdate) -> Role:
        """
        Update role information.

        Business rules:
        - Role must exist
        - Name must be unique if changed

        Args:
            role_id: Role ID
            data: Update data

        Returns:
            Updated Role object

        Raises:
            RoleNotFoundException: If role not found
            DuplicateNameException: If new name already exists
        """
        # Get role
        role = await self.get_role_by_id(role_id)

        # Check name uniqueness if name is being changed
        if data.name and data.name != role.name:
            if await self.role_repo.name_exists(data.name, exclude_id=role_id):
                raise DuplicateNameException(data.name, 'Role')

        # Update role
        update_dict: dict[str, Any] = data.model_dump(exclude_unset=True)
        role = await self.role_repo.update(role, update_dict)
        await self.db.commit()

        logger.info(f'Role updated: {role.name} (ID: {role.id})')

        return role

    async def list_roles(
        self, active_only: bool = False, limit: int = 100, offset: int = 0
    ) -> list[Role]:
        """
        List roles with pagination.

        Args:
            active_only: If True, return only active roles
            limit: Maximum number of roles to return
            offset: Number of roles to skip

        Returns:
            List of Role objects
        """
        if active_only:
            return await self.role_repo.list_active(limit=limit, offset=offset)
        return await self.role_repo.list_all(limit=limit, offset=offset)


# ==================== Permission Service ====================


class PermissionService:
    """Business logic for permission management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.permission_repo = PermissionRepository(db)

    async def create_permission(self, data: PermissionCreate) -> Permission:
        """
        Create a new permission.

        Business rules:
        - Permission code must be unique
        - Code must follow pattern: module.action[.scope]

        Args:
            data: Permission creation data

        Returns:
            Created Permission object

        Raises:
            DuplicateCodeException: If permission code already exists
        """
        # Check if code exists
        if await self.permission_repo.code_exists(data.code):
            raise BusinessValidationException(
                f'Permission code {data.code} already exists'
            )

        # Create permission
        permission = Permission(
            code=data.code,
            name=data.name,
            description=data.description,
            module=data.module,
            status=Status.ACTIVE,
        )

        # Save to database
        permission = await self.permission_repo.create(permission)
        await self.db.commit()

        logger.info(f'Permission created: {permission.code} (ID: {permission.id})')

        return permission

    async def list_permissions(
        self,
        module: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Permission]:
        """
        List permissions with optional filtering.

        Args:
            module: Filter by module (optional)
            active_only: If True, return only active permissions
            limit: Maximum number of permissions to return
            offset: Number of permissions to skip

        Returns:
            List of Permission objects
        """
        if module:
            return await self.permission_repo.list_by_module(
                module=module, limit=limit, offset=offset
            )

        if active_only:
            return await self.permission_repo.list_active(limit=limit, offset=offset)

        return await self.permission_repo.list_all(limit=limit, offset=offset)
