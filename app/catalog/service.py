"""
Catalog service layer for business logic.

This module provides business logic for catalog entities:
- ItemService: Individual service items (photos, videos, albums)
- PackageService: Service packages with included items
- RoomService: Studio spaces for sessions
"""

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.catalog.models import Item, Package, PackageItem, Room
from app.catalog.repository import ItemRepository, PackageRepository, RoomRepository
from app.catalog.schemas import (
    ItemCreate,
    ItemUpdate,
    PackageCreate,
    PackageItemCreate,
    PackageItemDetail,
    PackageUpdate,
    RoomCreate,
    RoomUpdate,
)
from app.core.enums import ItemType, SessionType, Status
from app.core.exceptions import (
    DuplicateCodeException,
    DuplicateNameException,
    InactiveResourceException,
    ItemNotFoundException,
    PackageItemNotFoundException,
    PackageNotFoundException,
    RoomNotFoundException,
)

# ==================== Item Service ====================


class ItemService:
    """Service for Item business logic and orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ItemRepository(db)

    async def create_item(self, data: ItemCreate, created_by: int) -> Item:
        """
        Create a new item.

        Validates code uniqueness before creation.
        """
        # Check if code already exists
        if await self.repo.code_exists(data.code):
            raise DuplicateCodeException(data.code, 'Item')

        item = Item(
            code=data.code,
            name=data.name,
            description=data.description,
            item_type=data.item_type,
            unit_price=data.unit_price,
            unit_measure=data.unit_measure,
            default_quantity=data.default_quantity,
            created_by=created_by,
        )

        item = await self.repo.create(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_item(self, item_id: int) -> Item:
        """Get item by ID."""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise ItemNotFoundException(f'Item with ID {item_id} not found')  # type: ignore
        return item

    async def get_active_item(self, item_id: int) -> Item:
        """Get active item by ID (validates status)."""
        item = await self.get_item(item_id)
        if item.status != Status.ACTIVE:
            raise InactiveResourceException(
                f'Item {item.name} (ID: {item_id}) is inactive'
            )
        return item

    async def list_items(
        self,
        active_only: bool = False,
        item_type: ItemType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Item]:
        """
        List items with optional filters.

        Priority: item_type > active_only > all
        """
        if item_type:
            return await self.repo.list_by_type(item_type, limit, offset)
        if active_only:
            return await self.repo.list_active(limit, offset)
        return await self.repo.list_all(limit, offset)

    async def update_item(
        self, item_id: int, data: ItemUpdate, updated_by: int
    ) -> Item:
        """
        Update an existing item.

        Validates code uniqueness if code is being changed.
        """
        item = await self.get_item(item_id)
        update_dict = data.model_dump(exclude_unset=True)

        # Check code uniqueness if being changed
        if 'code' in update_dict and update_dict['code'] != item.code:
            if await self.repo.code_exists(update_dict['code'], exclude_id=item_id):
                raise DuplicateCodeException(update_dict['code'], 'Item')

        item = await self.repo.update(item, update_dict)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def deactivate_item(self, item_id: int, deactivated_by: int) -> Item:
        """Soft delete an item (sets status to INACTIVE)."""
        item = await self.get_item(item_id)
        item = await self.repo.soft_delete(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def reactivate_item(self, item_id: int, reactivated_by: int) -> Item:
        """Reactivate an inactive item."""
        item = await self.get_item(item_id)
        if item.status == Status.ACTIVE:
            return item

        item.status = Status.ACTIVE
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def count_items(
        self, active_only: bool = False, item_type: ItemType | None = None
    ) -> int:
        """
        Count items matching filters.

        Args:
            active_only: If True, only count active items
            item_type: Filter by item type (optional)

        Returns:
            Total count of items matching filters
        """
        return await self.repo.count_items(active_only=active_only, item_type=item_type)


# ==================== Package Service ====================


class PackageService:
    """Service for Package business logic and orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PackageRepository(db)
        self.item_repo = ItemRepository(db)

    async def create_package(self, data: PackageCreate, created_by: int) -> Package:
        """
        Create a new package.

        Validates code uniqueness before creation.
        """
        # Check if code already exists
        if await self.repo.code_exists(data.code):
            raise DuplicateCodeException(data.code, 'Package')

        package = Package(
            code=data.code,
            name=data.name,
            description=data.description,
            session_type=data.session_type,
            base_price=data.base_price,
            estimated_editing_days=data.estimated_editing_days,
            created_by=created_by,
        )

        package = await self.repo.create(package)
        await self.db.commit()
        await self.db.refresh(package)
        return package

    async def get_package(self, package_id: int) -> Package:
        """Get package by ID."""
        package = await self.repo.get_by_id(package_id)
        if not package:
            raise PackageNotFoundException(f'Package with ID {package_id} not found')
        return package

    async def get_package_with_items(self, package_id: int) -> Package:
        """
        Get package by ID with items eagerly loaded.

        Returns package with full item details for displaying package contents.
        """
        package = await self.repo.get_with_items(package_id)
        if not package:
            raise PackageNotFoundException(f'Package with ID {package_id} not found')
        return package

    async def get_active_package(self, package_id: int) -> Package:
        """Get active package by ID (validates status)."""
        package = await self.get_package(package_id)
        if package.status != Status.ACTIVE:
            raise InactiveResourceException(
                f'Package {package.name} (ID: {package_id}) is inactive'
            )
        return package

    async def list_packages(
        self,
        active_only: bool = False,
        session_type: SessionType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Package]:
        """
        List packages with optional filters.

        Priority: session_type > active_only > all
        """
        if session_type:
            return await self.repo.list_by_session_type(session_type, limit, offset)
        if active_only:
            return await self.repo.list_active(limit, offset)
        return await self.repo.list_all(limit, offset)

    async def update_package(
        self, package_id: int, data: PackageUpdate, updated_by: int
    ) -> Package:
        """
        Update an existing package.

        Validates code uniqueness if code is being changed.
        """
        package = await self.get_package(package_id)
        update_dict = data.model_dump(exclude_unset=True)

        # Check code uniqueness if being changed
        if 'code' in update_dict and update_dict['code'] != package.code:
            if await self.repo.code_exists(update_dict['code'], exclude_id=package_id):
                raise DuplicateCodeException(update_dict['code'], 'Package')

        package = await self.repo.update(package, update_dict)
        await self.db.commit()
        await self.db.refresh(package)
        return package

    async def deactivate_package(self, package_id: int, deactivated_by: int) -> Package:
        """Soft delete a package (sets status to INACTIVE)."""
        package = await self.get_package(package_id)
        package = await self.repo.soft_delete(package)
        await self.db.commit()
        await self.db.refresh(package)
        return package

    async def reactivate_package(self, package_id: int, reactivated_by: int) -> Package:
        """Reactivate an inactive package."""
        package = await self.get_package(package_id)
        if package.status == Status.ACTIVE:
            return package

        package.status = Status.ACTIVE
        self.db.add(package)
        await self.db.commit()
        await self.db.refresh(package)
        return package

    # ==================== Package-Item Management ====================

    async def add_item_to_package(
        self, package_id: int, data: PackageItemCreate
    ) -> PackageItem:
        """
        Add an item to a package.

        Validates:
        - Package exists and is active
        - Item exists and is active
        - Item is not already in the package
        """
        # Validate package
        package = await self.get_active_package(package_id)

        # Validate item
        item = await self.item_repo.get_by_id(data.item_id)
        if not item:
            raise ItemNotFoundException(f'Item with ID {data.item_id} not found')
        if item.status != Status.ACTIVE:
            raise InactiveResourceException(
                f'Item {item.name} (ID: {data.item_id}) is inactive'
            )

        # Check if item is already in package
        statement = select(PackageItem).where(
            PackageItem.package_id == package_id, PackageItem.item_id == data.item_id
        )
        result = await self.db.exec(statement)
        existing = result.first()

        if existing:
            raise DuplicateCodeException(
                f'Item {item.name} is already in package {package.name}'
            )

        # Create package-item link
        package_item = PackageItem(
            package_id=package_id,
            item_id=data.item_id,
            quantity=data.quantity,
            display_order=data.display_order,
        )

        self.db.add(package_item)
        await self.db.flush()
        await self.db.refresh(package_item)
        await self.db.commit()

        return package_item

    async def remove_item_from_package(
        self, package_id: int, item_id: int
    ) -> PackageItem:
        """
        Remove an item from a package.

        Validates package and item exist before removal.
        """
        # Validate package exists
        await self.get_package(package_id)

        # Get package-item link
        statement = select(PackageItem).where(
            PackageItem.package_id == package_id, PackageItem.item_id == item_id
        )
        result = await self.db.exec(statement)
        package_item = result.first()

        if not package_item:
            raise PackageItemNotFoundException(
                f'Item with ID {item_id} is not in package {package_id}'
            )

        await self.db.delete(package_item)
        await self.db.commit()

        return package_item

    async def update_package_item(
        self, package_id: int, item_id: int, quantity: int, display_order: int | None
    ) -> PackageItem:
        """
        Update quantity or display order of an item in a package.

        Validates package and item link exist before updating.
        """
        # Validate package exists
        await self.get_package(package_id)

        # Get package-item link
        statement = select(PackageItem).where(
            PackageItem.package_id == package_id, PackageItem.item_id == item_id
        )
        result = await self.db.exec(statement)
        package_item = result.first()

        if not package_item:
            raise PackageItemNotFoundException(
                f'Item with ID {item_id} is not in package {package_id}'
            )

        # Update fields
        package_item.quantity = quantity
        if display_order is not None:
            package_item.display_order = display_order

        self.db.add(package_item)
        await self.db.flush()
        await self.db.refresh(package_item)
        await self.db.commit()

        return package_item

    async def get_package_items_detail(
        self, package_id: int
    ) -> list[PackageItemDetail]:
        """
        Get all items in a package with full details.

        Returns item details suitable for API response (PackageItemDetail schema).
        """
        # Validate package exists
        await self.get_package(package_id)

        # Get package items with item details eagerly loaded
        statement = (
            select(PackageItem)
            .where(PackageItem.package_id == package_id)
            .options(selectinload(PackageItem.item))  # type: ignore
            .order_by(PackageItem.display_order)
        )

        result = await self.db.exec(statement)
        package_items = result.all()

        # Transform to PackageItemDetail schema
        return [
            PackageItemDetail(
                item_id=pi.item_id,
                item_code=pi.item.code,
                item_name=pi.item.name,
                item_type=pi.item.item_type,
                item_unit_price=pi.item.unit_price,
                quantity=pi.quantity,
                display_order=pi.display_order,
            )
            for pi in package_items
        ]

    async def count_packages(
        self, active_only: bool = False, session_type: SessionType | None = None
    ) -> int:
        """
        Count packages matching filters.

        Args:
            active_only: If True, only count active packages
            session_type: Filter by session type (optional)

        Returns:
            Total count of packages matching filters
        """
        return await self.repo.count_packages(
            active_only=active_only, session_type=session_type
        )


# ==================== Room Service ====================


class RoomService:
    """Service for Room business logic and orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RoomRepository(db)

    async def create_room(self, data: RoomCreate) -> Room:
        """
        Create a new room.

        Validates name uniqueness before creation.
        """
        # Check if name already exists
        if await self.repo.name_exists(data.name):
            raise DuplicateNameException(data.name, 'Room')

        room = Room(
            name=data.name,
            description=data.description,
            capacity=data.capacity,
            hourly_rate=data.hourly_rate,
        )

        room = await self.repo.create(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_room(self, room_id: int) -> Room:
        """Get room by ID."""
        room = await self.repo.get_by_id(room_id)
        if not room:
            raise RoomNotFoundException(f'Room with ID {room_id} not found')
        return room

    async def get_active_room(self, room_id: int) -> Room:
        """Get active room by ID (validates status)."""
        room = await self.get_room(room_id)
        if room.status != Status.ACTIVE:
            raise InactiveResourceException(
                f'Room {room.name} (ID: {room_id}) is inactive'
            )
        return room

    async def list_rooms(
        self, active_only: bool = False, limit: int = 100, offset: int = 0
    ) -> list[Room]:
        """List rooms with optional active filter."""
        if active_only:
            return await self.repo.list_active(limit, offset)
        return await self.repo.list_all(limit, offset)

    async def update_room(self, room_id: int, data: RoomUpdate) -> Room:
        """
        Update an existing room.

        Validates name uniqueness if name is being changed.
        """
        room = await self.get_room(room_id)
        update_dict = data.model_dump(exclude_unset=True)

        # Check name uniqueness if being changed
        if 'name' in update_dict and update_dict['name'] != room.name:
            if await self.repo.name_exists(update_dict['name'], exclude_id=room_id):
                raise DuplicateNameException(update_dict['name'], 'Room')

        room = await self.repo.update(room, update_dict)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def deactivate_room(self, room_id: int) -> Room:
        """Soft delete a room (sets status to INACTIVE)."""
        room = await self.get_room(room_id)
        room = await self.repo.soft_delete(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def reactivate_room(self, room_id: int) -> Room:
        """Reactivate an inactive room."""
        room = await self.get_room(room_id)
        if room.status == Status.ACTIVE:
            return room

        room.status = Status.ACTIVE
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def set_maintenance(self, room_id: int) -> Room:
        """Set room status to MAINTENANCE."""
        room = await self.get_room(room_id)
        room = await self.repo.set_maintenance(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def count_rooms(self, active_only: bool = False) -> int:
        """
        Count rooms matching filters.

        Args:
            active_only: If True, only count active rooms

        Returns:
            Total count of rooms matching filters
        """
        return await self.repo.count_rooms(active_only=active_only)
