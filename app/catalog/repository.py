"""
Catalog repositories for database operations.

This module provides data access methods for catalog entities (Items, Packages, Rooms)
using SQLModel's native methods.
"""

from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.catalog.models import Item, Package, PackageItem, Room
from app.core.enums import ItemType, SessionType, Status

# ==================== Item Repository ====================


class ItemRepository:
    """Repository for Item database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, item_id: int) -> Item | None:
        """Get item by ID."""
        return await self.db.get(Item, item_id)

    async def find_by_code(self, code: str) -> Item | None:
        """Find item by unique code."""
        statement = select(Item).where(Item.code == code)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Item]:
        """List all items with pagination."""
        statement = (
            select(Item)
            .order_by(col(Item.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Item]:
        """List active items with pagination."""
        statement = (
            select(Item)
            .where(Item.status == Status.ACTIVE)
            .order_by(Item.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_type(
        self, item_type: ItemType, limit: int = 100, offset: int = 0
    ) -> list[Item]:
        """List items by type."""
        statement = (
            select(Item)
            .where(Item.item_type == item_type)
            .where(Item.status == Status.ACTIVE)
            .order_by(Item.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, item: Item) -> Item:
        """Create a new item."""
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item: Item, data: dict) -> Item:
        """Update an existing item."""
        item.sqlmodel_update(data)
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def soft_delete(self, item: Item) -> Item:
        """Soft delete an item."""
        item.status = Status.INACTIVE
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def code_exists(self, code: str, exclude_id: int | None = None) -> bool:
        """Check if item code already exists."""
        statement = select(Item).where(Item.code == code)

        if exclude_id:
            statement = statement.where(Item.id != exclude_id)

        result = await self.db.exec(statement)
        return result.first() is not None


# ==================== Package Repository ====================


class PackageRepository:
    """Repository for Package database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, package_id: int) -> Package | None:
        """Get package by ID."""
        return await self.db.get(Package, package_id)

    async def get_with_items(self, package_id: int) -> Package | None:
        """
        Get package by ID with items eagerly loaded.

        Uses selectinload for optimized query performance.
        """
        statement = (
            select(Package)
            .where(Package.id == package_id)
            .options(selectinload(Package.items))  # type: ignore
        )

        result = await self.db.exec(statement)
        return result.first()

    async def find_by_code(self, code: str) -> Package | None:
        """Find package by unique code."""
        statement = select(Package).where(Package.code == code)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Package]:
        """List all packages with pagination."""
        statement = (
            select(Package)
            .order_by(col(Package.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Package]:
        """List active packages with pagination."""
        statement = (
            select(Package)
            .where(Package.status == Status.ACTIVE)
            .order_by(Package.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_session_type(
        self, session_type: SessionType, limit: int = 100, offset: int = 0
    ) -> list[Package]:
        """
        List packages by session type (Studio, External, or Both).

        Args:
            session_type: SessionType enum value
        """
        statement = (
            select(Package)
            .where(
                (Package.session_type == session_type)
                | (Package.session_type == SessionType.BOTH)
            )
            .where(Package.status == Status.ACTIVE)
            .order_by(Package.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, package: Package) -> Package:
        """Create a new package."""
        self.db.add(package)
        await self.db.flush()
        await self.db.refresh(package)
        return package

    async def update(self, package: Package, data: dict) -> Package:
        """Update an existing package."""
        package.sqlmodel_update(data)
        self.db.add(package)
        await self.db.flush()
        await self.db.refresh(package)
        return package

    async def soft_delete(self, package: Package) -> Package:
        """Soft delete a package."""
        package.status = Status.INACTIVE
        self.db.add(package)
        await self.db.flush()
        await self.db.refresh(package)
        return package

    async def code_exists(self, code: str, exclude_id: int | None = None) -> bool:
        """Check if package code already exists."""
        statement = select(Package).where(Package.code == code)

        if exclude_id:
            statement = statement.where(Package.id != exclude_id)

        result = await self.db.exec(statement)
        return result.first() is not None

    async def get_package_items(self, package_id: int) -> list[PackageItem]:
        """Get all items associated with a package."""
        statement = (
            select(PackageItem)
            .where(PackageItem.package_id == package_id)
            .order_by(col(PackageItem.display_order))
        )
        result = await self.db.exec(statement)
        return list(result.all())

    # check validation column later


# ==================== Room Repository ====================


class RoomRepository:
    """Repository for Room database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, room_id: int) -> Room | None:
        """Get room by ID."""
        return await self.db.get(Room, room_id)

    async def find_by_name(self, name: str) -> Room | None:
        """Find room by unique name."""
        statement = select(Room).where(Room.name == name)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Room]:
        """List all rooms with pagination."""
        statement = select(Room).order_by(Room.name).offset(offset).limit(limit)
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Room]:
        """List active rooms with pagination."""
        statement = (
            select(Room)
            .where(Room.status == Status.ACTIVE)
            .order_by(Room.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, room: Room) -> Room:
        """Create a new room."""
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def update(self, room: Room, data: dict) -> Room:
        """Update an existing room."""
        room.sqlmodel_update(data)
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def soft_delete(self, room: Room) -> Room:
        """Soft delete a room."""
        room.status = Status.INACTIVE
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def set_maintenance(self, room: Room) -> Room:
        """Set room status to Maintenance."""
        room.status = Status.MAINTENANCE
        self.db.add(room)
        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        """Check if room name already exists."""
        statement = select(Room).where(Room.name == name)

        if exclude_id:
            statement = statement.where(Room.id != exclude_id)

        result = await self.db.exec(statement)
        return result.first() is not None
