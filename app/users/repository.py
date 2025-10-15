"""
Users repositories for database operations.

This module provides data access methods for User, Role, and Permission entities
using SQLModel's native async methods.
"""

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import Status
from app.users.models import Permission, Role, RolePermission, User, UserRole

# ==================== Permission Repository ====================


class PermissionRepository:
    """Repository for Permission database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, permission_id: int) -> Permission | None:
        """Get permission by ID."""
        return await self.db.get(Permission, permission_id)

    async def find_by_code(self, code: str) -> Permission | None:
        """Find permission by unique code."""
        statement = select(Permission).where(Permission.code == code)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Permission]:
        """List all permissions with pagination."""
        statement = (
            select(Permission)
            .order_by(Permission.module, Permission.code)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Permission]:
        """List active permissions with pagination."""
        statement = (
            select(Permission)
            .where(Permission.status == Status.ACTIVE)
            .order_by(Permission.module, Permission.code)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_module(
        self, module: str, limit: int = 100, offset: int = 0
    ) -> list[Permission]:
        """List permissions by module."""
        statement = (
            select(Permission)
            .where(Permission.module == module)
            .where(Permission.status == Status.ACTIVE)
            .order_by(Permission.code)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, permission: Permission) -> Permission:
        """Create a new permission."""
        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)
        return permission

    async def update(self, permission: Permission, data: dict) -> Permission:
        """Update an existing permission."""
        permission.sqlmodel_update(data)
        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)
        return permission

    async def soft_delete(self, permission: Permission) -> Permission:
        """Soft delete a permission."""
        permission.status = Status.INACTIVE
        self.db.add(permission)
        await self.db.flush()
        await self.db.refresh(permission)
        return permission

    async def code_exists(self, code: str, exclude_id: int | None = None) -> bool:
        """Check if permission code already exists."""
        statement = select(Permission).where(Permission.code == code)

        if exclude_id:
            statement = statement.where(Permission.id != exclude_id)

        result = await self.db.exec(statement)
        return result.first() is not None

    async def count_permissions(
        self, module: str | None = None, active_only: bool = False
    ) -> int:
        """
        Count permissions matching filters.

        Args:
            module: Filter by module (optional)
            active_only: If True, only count active permissions

        Returns:
            Total count of permissions matching filters
        """
        from sqlalchemy import func

        statement = select(func.count(Permission.id))

        if module:
            statement = statement.where(Permission.module == module)

        if active_only:
            statement = statement.where(Permission.status == Status.ACTIVE)

        result = await self.db.exec(statement)
        return result.one()


# ==================== Role Repository ====================


class RoleRepository:
    """Repository for Role database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, role_id: int) -> Role | None:
        """Get role by ID."""
        return await self.db.get(Role, role_id)

    async def get_with_permissions(self, role_id: int) -> Role | None:
        """
        Get role by ID with permissions eagerly loaded.

        Uses selectinload for optimized query performance.
        """
        statement = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))  # type: ignore
        )
        result = await self.db.exec(statement)
        return result.first()

    async def find_by_name(self, name: str) -> Role | None:
        """Find role by unique name."""
        statement = select(Role).where(Role.name == name)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Role]:
        """List all roles with pagination."""
        statement = select(Role).order_by(Role.name).offset(offset).limit(limit)
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Role]:
        """List active roles with pagination."""
        statement = (
            select(Role)
            .where(Role.status == Status.ACTIVE)
            .order_by(Role.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, role: Role) -> Role:
        """Create a new role."""
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def update(self, role: Role, data: dict) -> Role:
        """Update an existing role."""
        role.sqlmodel_update(data)
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def soft_delete(self, role: Role) -> Role:
        """Soft delete a role."""
        role.status = Status.INACTIVE
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if role name already exists."""
        statement = select(Role).where(Role.name == name)

        if exclude_id:
            statement = statement.where(Role.id != exclude_id)

        result = await self.db.exec(statement)
        return result.first() is not None

    async def assign_permission(
        self, role_id: int, permission_id: int, granted_by: int
    ) -> RolePermission:
        """Assign a permission to a role."""
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by,
        )
        self.db.add(role_permission)
        await self.db.flush()
        await self.db.refresh(role_permission)
        return role_permission

    async def remove_permission(self, role_id: int, permission_id: int) -> None:
        """Remove a permission from a role."""
        statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
        result = await self.db.exec(statement)
        role_permission = result.first()

        if role_permission:
            await self.db.delete(role_permission)
            await self.db.flush()

    async def count_roles(self, active_only: bool = False) -> int:
        """
        Count roles matching filters.

        Args:
            active_only: If True, only count active roles

        Returns:
            Total count of roles matching filters
        """
        from sqlalchemy import func

        statement = select(func.count(Role.id))

        if active_only:
            statement = statement.where(Role.status == Status.ACTIVE)

        result = await self.db.exec(statement)
        return result.one()


# ==================== User Repository ====================


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self.db.get(User, user_id)

    async def get_with_roles(self, user_id: int) -> User | None:
        """
        Get user by ID with roles eagerly loaded.

        Uses selectinload for optimized query performance.
        """
        statement = (
            select(User).where(User.id == user_id).options(selectinload(User.roles))  # type: ignore
        )
        result = await self.db.exec(statement)
        return result.first()

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email address."""
        statement = select(User).where(User.email == email)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users with pagination."""
        statement = select(User).order_by(User.full_name).offset(offset).limit(limit)
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List active users with pagination."""
        statement = (
            select(User)
            .where(User.status == Status.ACTIVE)
            .order_by(User.full_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_role(
        self, role_name: str, limit: int = 100, offset: int = 0
    ) -> list[User]:
        """List users by role name."""
        statement = (
            select(User)
            .join(UserRole)
            .join(Role)
            .where(Role.name == role_name)
            .where(User.status == Status.ACTIVE)
            .order_by(User.full_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, data: dict) -> User:
        """Update an existing user."""
        user.sqlmodel_update(data)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def soft_delete(self, user: User) -> User:
        """Soft delete a user."""
        user.status = Status.INACTIVE
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        """Check if email already exists."""
        statement = select(User).where(User.email == email)

        if exclude_id:
            statement = statement.where(User.id != exclude_id)

        result = await self.db.exec(statement)
        return result.first() is not None

    async def assign_role(
        self, user_id: int, role_id: int, assigned_by: int
    ) -> UserRole:
        """Assign a role to a user."""
        user_role = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.db.add(user_role)
        await self.db.flush()
        await self.db.refresh(user_role)
        return user_role

    async def remove_role(self, user_id: int, role_id: int) -> None:
        """Remove a role from a user."""
        statement = select(UserRole).where(
            UserRole.user_id == user_id, UserRole.role_id == role_id
        )
        result = await self.db.exec(statement)
        user_role = result.first()

        if user_role:
            await self.db.delete(user_role)
            await self.db.flush()

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        """Get all permissions for a user (through their roles)."""
        statement = (
            select(Permission)
            .join(RolePermission)
            .join(Role)
            .join(UserRole)
            .where(UserRole.user_id == user_id)
            .where(Permission.status == Status.ACTIVE)
            .where(Role.status == Status.ACTIVE)
            .distinct()
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def count_users(self, active_only: bool = False) -> int:
        """
        Count users matching filters.

        Args:
            active_only: If True, only count active users

        Returns:
            Total count of users matching filters
        """
        from sqlalchemy import func

        statement = select(func.count(User.id))

        if active_only:
            statement = statement.where(User.status == Status.ACTIVE)

        result = await self.db.exec(statement)
        return result.one()
