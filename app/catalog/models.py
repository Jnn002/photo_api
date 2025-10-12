"""
Catalog models for managing items, packages, and rooms.

This module defines:
- Item: Individual services (photos, videos, albums)
- Package: Predefined service packages
- PackageItem: Many-to-many relationship between packages and items
- Room: Studio spaces for sessions
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from ..core.enums import ItemType, SessionType, Status
from ..core.time_utils import get_current_utc_time

if TYPE_CHECKING:
    from ..sessions.models import Session
    from ..users.models import User


class PackageItem(SQLModel, table=True):
    """Package-item relationship (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    package_id: int = Field(foreign_key='studio.package.id', primary_key=True)
    item_id: int = Field(foreign_key='studio.item.id', primary_key=True)
    quantity: int = Field(default=1)
    display_order: int | None = Field(default=None)

    item: 'Item' = Relationship(back_populates='package_links')
    package: 'Package' = Relationship(back_populates='item_links')


class Item(SQLModel, table=True):
    """Individual services (photos, videos, albums, etc.)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=50, index=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    item_type: ItemType
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    unit_measure: str = Field(max_length=20)  # Unit, Hour, Package
    default_quantity: int | None = Field(default=None)
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    packages: list['Package'] = Relationship(
        back_populates='items',
        link_model=PackageItem,
    )
    package_links: list[PackageItem] = Relationship(back_populates='item')
    creator: 'User' = Relationship(
        back_populates='created_items',
        sa_relationship_kwargs={'foreign_keys': '[Item.created_by]'},
    )


class Package(SQLModel, table=True):
    """Predefined service packages."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=50, index=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    session_type: SessionType
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    estimated_editing_days: int = Field(default=5)
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    items: list['Item'] = Relationship(
        back_populates='packages', link_model=PackageItem
    )
    item_links: list[PackageItem] = Relationship(back_populates='package')
    creator: 'User' = Relationship(
        back_populates='created_packages',
        sa_relationship_kwargs={'foreign_keys': '[Package.created_by]'},
    )


class Room(SQLModel, table=True):
    """Studio spaces for photo sessions."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None)
    capacity: int | None = Field(default=None)  # Number of people
    hourly_rate: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )

    # Relationships
    sessions: list['Session'] = Relationship(back_populates='room')
