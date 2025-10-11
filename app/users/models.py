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
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from ..catalog.models import Item, Package, Room
    from ..clients.models import Client
    from ..sessions.models import (
        Session,
        SessionDetail,
        SessionPayment,
        SessionPhotographer,
        SessionStatusHistory,
    )


class UserRole(SQLModel, table=True):
    """User-role assignments (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='studio.user.id')
    role_id: int = Field(foreign_key='studio.role.id')
    assigned_at: datetime = Field(default_factory=datetime.now)
    assigned_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    user: 'User' = Relationship(back_populates='user_links')
    role: 'Role' = Relationship(back_populates='role_links')


class RolePermission(SQLModel, table=True):
    """Role-permission assignments (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key='studio.role.id')
    permission_id: int = Field(foreign_key='studio.permission.id')
    granted_at: datetime = Field(default_factory=datetime.now)
    granted_by: int | None = Field(default=None, foreign_key='studio.user.id')

    # Relationships
    role: 'Role' = Relationship(back_populates='permission_links')
    permission: 'Permission' = Relationship(back_populates='role_links')


class User(SQLModel, table=True):
    """System users and collaborators."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=100)
    password_hash: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: int | None = Field(default=None, foreign_key='studio.user.id')

    # Relationships (link models with extra fields)
    user_links: list['UserRole'] = Relationship(back_populates='user')
    roles: list['Role'] = Relationship(back_populates='users', link_model=UserRole)

    # Client relationships
    created_clients: list['Client'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[Client.created_by]',
        }
    )

    # Session relationships
    created_sessions: list['Session'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[Session.created_by]',
        }
    )
    sessions_as_editor: list['Session'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[Session.editing_assigned_to]',
        }
    )
    cancelled_sessions: list['Session'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[Session.cancelled_by]',
        }
    )

    # SessionDetail relationships
    created_session_details: list['SessionDetail'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[SessionDetail.created_by]',
        }
    )

    # SessionPhotographer relationships
    photographer_assignments: list['SessionPhotographer'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[SessionPhotographer.photographer_id]',
        }
    )
    assigned_photographer_sessions: list['SessionPhotographer'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[SessionPhotographer.assigned_by]',
        }
    )

    # SessionPayment relationships
    created_payments: list['SessionPayment'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[SessionPayment.created_by]',
        }
    )

    # SessionStatusHistory relationships
    status_changes: list['SessionStatusHistory'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[SessionStatusHistory.changed_by]',
        }
    )

    # Catalog relationships
    created_items: list['Item'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[Item.created_by]',
        }
    )
    created_packages: list['Package'] = Relationship(
        sa_relationship_kwargs={
            'foreign_keys': '[Package.created_by]',
        }
    )


class Role(SQLModel, table=True):
    """System roles (Admin, Coordinator, Photographer, Editor)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships (link models with extra fields)
    role_links: list['UserRole'] = Relationship(back_populates='role')
    users: list['User'] = Relationship(back_populates='roles', link_model=UserRole)
    permission_links: list['RolePermission'] = Relationship(back_populates='role')
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
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships (link models with extra fields)
    role_links: list['RolePermission'] = Relationship(back_populates='permission')
    roles: list['Role'] = Relationship(
        back_populates='permissions', link_model=RolePermission
    )
