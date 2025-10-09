"""
User models for authentication and RBAC system.

This module defines the core user-related models including:
- User: System users (admin, coordinators, photographers, editors)
- Role: User roles (Admin, Coordinator, Photographer, Editor)
- Permission: Granular permissions (session.create, user.edit, etc.)
- UserRole: Many-to-many relationship between users and roles
- RolePermission: Many-to-many relationship between roles and permissions
"""

from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class UserRole(SQLModel, table=True):
    """User-role assignments (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='studio.user.id')
    role_id: int = Field(foreign_key='studio.role.id')
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: int = Field(foreign_key='studio.user.id')


class RolePermission(SQLModel, table=True):
    """Role-permission assignments (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key='studio.role.id')
    permission_id: int = Field(foreign_key='studio.permission.id')
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    granted_by: int | None = Field(default=None, foreign_key='studio.user.id')


class User(SQLModel, table=True):
    """System users and collaborators."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=100)
    password_hash: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int | None = Field(default=None, foreign_key='studio.user.id')

    # Relationships
    roles: list['Role'] = Relationship(
        back_populates='users', link_model=UserRole
    )


class Role(SQLModel, table=True):
    """System roles (Admin, Coordinator, Photographer, Editor)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: list['User'] = Relationship(
        back_populates='roles', link_model=UserRole
    )
    permissions: list['Permission'] = Relationship(
        back_populates='roles', link_model=RolePermission
    )


class Permission(SQLModel, table=True):
    """System permissions (session.create, user.edit, etc.)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=100)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    module: str = Field(max_length=50)  # session, client, user, report, etc.
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    roles: list['Role'] = Relationship(
        back_populates='permissions', link_model=RolePermission
    )
