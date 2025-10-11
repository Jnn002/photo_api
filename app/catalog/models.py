"""
Catalog models for managing items, packages, and rooms.

This module defines:
- Item: Individual services (photos, videos, albums)
- Package: Predefined service packages
- PackageItem: Many-to-many relationship between packages and items
- Room: Studio spaces for sessions
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from ..sessions.models import Session
    from ..users.models import User


class PackageItem(SQLModel, table=True):
    """Package-item relationship (many-to-many link table)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    package_id: int = Field(foreign_key='studio.package.id')
    item_id: int = Field(foreign_key='studio.item.id')
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
    item_type: str = Field(max_length=50)  # Digital Photo, Printed Photo, Album, Video
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    unit_measure: str = Field(max_length=20)  # Unit, Hour, Package
    default_quantity: int | None = Field(default=None)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={'onupdate': datetime.now(timezone.utc)},
    )
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    packages: list['Package'] = Relationship(
        back_populates='items',
        link_model=PackageItem,
    )
    package_links: list[PackageItem] = Relationship(back_populates='item')
    creator: 'User' = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Item.created_by]'}
    )


class Package(SQLModel, table=True):
    """Predefined service packages."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=50, index=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    session_type: str = Field(max_length=20)  # Studio | External | Both
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    estimated_editing_days: int = Field(default=5)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={'onupdate': datetime.now(timezone.utc)},
    )
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    items: list['Item'] = Relationship(
        back_populates='packages', link_model=PackageItem
    )
    item_links: list[PackageItem] = Relationship(back_populates='package')
    creator: 'User' = Relationship(
        sa_relationship_kwargs={'foreign_keys': '[Package.created_by]'}
    )


class Room(SQLModel, table=True):
    """Studio spaces for photo sessions."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None)
    capacity: int | None = Field(default=None)  # Number of people
    hourly_rate: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    status: str = Field(
        default='Active', max_length=20
    )  # Active | Inactive | Maintenance
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={'onupdate': datetime.now(timezone.utc)},
    )

    # Relationships
    sessions: list['Session'] = Relationship(back_populates='room')
