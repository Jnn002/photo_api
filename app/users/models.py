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

from ..core.enums import Status
from ..core.time_utils import get_current_utc_time

if TYPE_CHECKING:
    from ..catalog.models import Item, Package
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

    user_id: int = Field(foreign_key='studio.user.id', primary_key=True)
    role_id: int = Field(foreign_key='studio.role.id', primary_key=True)
    assigned_at: datetime = Field(default_factory=get_current_utc_time)
    assigned_by: int | None = Field(foreign_key='studio.user.id')

    # Relationships
    user: 'User' = Relationship(
        back_populates='role_links',
        sa_relationship_kwargs={
            'foreign_keys': '[UserRole.user_id]',
        },
    )
    role: 'Role' = Relationship(back_populates='user_links')


class RolePermission(SQLModel, table=True):
    """Role-permission assignments (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    role_id: int = Field(foreign_key='studio.role.id', primary_key=True)
    permission_id: int = Field(foreign_key='studio.permission.id', primary_key=True)
    granted_at: datetime = Field(default_factory=get_current_utc_time)
    granted_by: int | None = Field(default=None, foreign_key='studio.user.id')

    # Relationships
    role: 'Role' = Relationship(
        back_populates='permission_links',
        sa_relationship_kwargs={
            'foreign_keys': '[RolePermission.role_id]',
        },
    )
    permission: 'Permission' = Relationship(
        back_populates='role_links',
        sa_relationship_kwargs={
            'foreign_keys': '[RolePermission.permission_id]',
        },
    )


class User(SQLModel, table=True):
    """System users and collaborators."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=100)
    password_hash: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )
    created_by: int | None = Field(default=None, foreign_key='studio.user.id')

    # Relationships (link models with extra fields)
    # Many-to-many: User <-> Role through UserRole
    # Note: UserRole has both user_id and assigned_by pointing to User,
    # so we must specify foreign_keys to avoid ambiguity.
    # We only want to use user_id and role_id for the many-to-many relationship,
    # not assigned_by.
    # The overlaps parameter tells SQLAlchemy that both relationships
    # write to the same columns, which is expected for many-to-many with link tables.
    roles: list['Role'] = Relationship(
        back_populates='users',
        link_model=UserRole,
        sa_relationship_kwargs={
            'foreign_keys': '[UserRole.user_id, UserRole.role_id]',
            'overlaps': 'user,role',
        },
    )
    role_links: list['UserRole'] = Relationship(
        back_populates='user',
        sa_relationship_kwargs={
            'foreign_keys': '[UserRole.user_id]',
            'overlaps': 'roles',
        },
    )

    # Client relationships
    created_clients: list['Client'] = Relationship(
        back_populates='creator',
        sa_relationship_kwargs={
            'foreign_keys': '[Client.created_by]',
        },
    )

    # Session relationships
    created_sessions: list['Session'] = Relationship(
        back_populates='creator',
        sa_relationship_kwargs={
            'foreign_keys': '[Session.created_by]',
        },
    )
    sessions_as_editor: list['Session'] = Relationship(
        back_populates='editor',
        sa_relationship_kwargs={
            'foreign_keys': '[Session.editing_assigned_to]',
        },
    )
    cancelled_sessions: list['Session'] = Relationship(
        back_populates='canceller',
        sa_relationship_kwargs={
            'foreign_keys': '[Session.cancelled_by]',
        },
    )

    # SessionDetail relationships
    created_session_details: list['SessionDetail'] = Relationship(
        back_populates='creator',
        sa_relationship_kwargs={
            'foreign_keys': '[SessionDetail.created_by]',
        },
    )

    # SessionPhotographer relationships
    photographer_assignments: list['SessionPhotographer'] = Relationship(
        back_populates='photographer',
        sa_relationship_kwargs={
            'foreign_keys': '[SessionPhotographer.photographer_id]',
        },
    )
    assigned_photographer_sessions: list['SessionPhotographer'] = Relationship(
        back_populates='assigner',
        sa_relationship_kwargs={
            'foreign_keys': '[SessionPhotographer.assigned_by]',
        },
    )

    # SessionPayment relationships
    created_payments: list['SessionPayment'] = Relationship(
        back_populates='creator',
        sa_relationship_kwargs={
            'foreign_keys': '[SessionPayment.created_by]',
        },
    )

    # SessionStatusHistory relationships
    status_changes: list['SessionStatusHistory'] = Relationship(
        back_populates='changed_by_user',
        sa_relationship_kwargs={
            'foreign_keys': '[SessionStatusHistory.changed_by]',
        },
    )

    # Catalog relationships
    created_items: list['Item'] = Relationship(
        back_populates='creator',
        sa_relationship_kwargs={
            'foreign_keys': '[Item.created_by]',
        },
    )
    created_packages: list['Package'] = Relationship(
        back_populates='creator',
        sa_relationship_kwargs={
            'foreign_keys': '[Package.created_by]',
        },
    )


class Role(SQLModel, table=True):
    """System roles (Admin, Coordinator, Photographer, Editor)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None)
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )

    # Relationships (link models with extra fields)
    # Many-to-many: Role <-> User through UserRole
    users: list['User'] = Relationship(
        back_populates='roles',
        link_model=UserRole,
        sa_relationship_kwargs={
            'foreign_keys': '[UserRole.user_id, UserRole.role_id]',
            'overlaps': 'user,role',
        },
    )
    user_links: list['UserRole'] = Relationship(
        back_populates='role',
        sa_relationship_kwargs={
            'overlaps': 'users',
        },
    )

    # Many-to-many: Role <-> Permission through RolePermission
    permissions: list['Permission'] = Relationship(
        back_populates='roles',
        link_model=RolePermission,
        sa_relationship_kwargs={
            'overlaps': 'role,permission',
        },
    )
    permission_links: list['RolePermission'] = Relationship(
        back_populates='role',
        sa_relationship_kwargs={
            'overlaps': 'permissions',
        },
    )


class Permission(SQLModel, table=True):
    """System permissions (session.create, user.edit, etc.)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=100)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    module: str = Field(max_length=50)  # session, client, user, report, etc.
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )

    # Relationships (link models with extra fields)
    # Many-to-many: Permission <-> Role through RolePermission
    roles: list['Role'] = Relationship(
        back_populates='permissions',
        link_model=RolePermission,
        sa_relationship_kwargs={
            'overlaps': 'role,permission',
        },
    )
    role_links: list['RolePermission'] = Relationship(
        back_populates='permission',
        sa_relationship_kwargs={
            'overlaps': 'roles',
        },
    )
