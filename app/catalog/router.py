"""
Catalog routers for catalog management endpoints.

This module exposes REST endpoints for:
- Items: Individual service items (CRUD operations)
- Packages: Service packages with items (CRUD + item management)
- Rooms: Studio spaces (CRUD operations)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.catalog.models import Item, Package, Room
from app.catalog.schemas import (
    ItemCreate,
    ItemPublic,
    ItemUpdate,
    PackageCreate,
    PackageDetail,
    PackageItemCreate,
    PackageItemDetail,
    PackagePublic,
    PackageUpdate,
    RoomCreate,
    RoomPublic,
    RoomUpdate,
)
from app.catalog.service import ItemService, PackageService, RoomService
from app.core.dependencies import SessionDep
from app.core.enums import ItemType, SessionType
from app.core.permissions import require_permission
from app.users.models import User

# ==================== Items Router ====================

items_router = APIRouter(prefix='/items', tags=['items'])


@items_router.post(
    '',
    response_model=ItemPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create item',
    description='Create a new catalog item. Requires item.create permission.',
)
async def create_item(
    data: ItemCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('item.create'))],
) -> Item:
    """
    Create a new catalog item.

    **Required fields:**
    - code: Unique item code
    - name: Item name
    - item_type: Type (Photo, Video, Album, etc.)
    - unit_price: Price per unit (must be positive)
    - unit_measure: Unit of measurement (Unit, Hour, Package)

    **Optional fields:**
    - description: Item description
    - default_quantity: Default quantity when added to sessions

    **Permissions required:** item.create
    """
    service = ItemService(db)
    return await service.create_item(data, created_by=current_user.id)  # type: ignore


@items_router.get(
    '',
    response_model=list[ItemPublic],
    status_code=status.HTTP_200_OK,
    summary='List items',
    description='Get paginated list of items with optional filters. Requires item.view permission.',
)
async def list_items(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('item.create'))],
    active_only: Annotated[
        bool, Query(description='Filter for active items only')
    ] = False,
    item_type: Annotated[
        ItemType | None,
        Query(description='Filter by item type (Photo, Video, Album, etc.)'),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 100,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> list[Item]:
    """
    List items with pagination and optional filters.

    **Query parameters:**
    - active_only: If true, return only active items (default: false)
    - item_type: Filter by type (Photo/Video/Album/etc.)
    - limit: Maximum number of items to return (1-100, default: 100)
    - offset: Number of items to skip for pagination (default: 0)

    **Permissions required:** item.view
    """
    service = ItemService(db)
    return await service.list_items(
        active_only=active_only, item_type=item_type, limit=limit, offset=offset
    )


@items_router.get(
    '/{item_id}',
    response_model=ItemPublic,
    status_code=status.HTTP_200_OK,
    summary='Get item by ID',
    description='Get item information by ID. Requires item.create permission.',
)
async def get_item(
    item_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('item.create'))],
) -> Item:
    """
    Get item by ID.

    **Path parameters:**
    - item_id: Item ID to retrieve

    **Permissions required:** item.view
    """
    service = ItemService(db)
    return await service.get_item(item_id)


@items_router.patch(
    '/{item_id}',
    response_model=ItemPublic,
    status_code=status.HTTP_200_OK,
    summary='Update item',
    description='Update item information. Requires item.edit permission.',
)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('item.edit'))],
) -> Item:
    """
    Update item information.

    **Path parameters:**
    - item_id: Item ID to update

    **Optional fields (all):**
    - code: Updated unique code
    - name: Updated name
    - description: Updated description
    - item_type: Updated type
    - unit_price: Updated price
    - unit_measure: Updated unit of measurement
    - default_quantity: Updated default quantity
    - status: Updated status (ACTIVE/INACTIVE)

    **Permissions required:** item.edit
    """
    service = ItemService(db)
    return await service.update_item(item_id, data, updated_by=current_user.id)  # type: ignore


@items_router.delete(
    '/{item_id}',
    status_code=status.HTTP_200_OK,
    response_model=ItemPublic,
    summary='Deactivate item',
    description='Deactivate (soft delete) an item. Requires item.delete permission.',
)
async def deactivate_item(
    item_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('item.delete'))],
) -> Item:
    """
    Deactivate an item (soft delete).

    Sets item status to INACTIVE. Item can be reactivated later.

    **Path parameters:**
    - item_id: Item ID to deactivate

    **Permissions required:** item.delete
    """
    service = ItemService(db)
    return await service.deactivate_item(item_id, deactivated_by=current_user.id)  # type: ignore


@items_router.put(
    '/{item_id}/reactivate',
    response_model=ItemPublic,
    status_code=status.HTTP_200_OK,
    summary='Reactivate item',
    description='Reactivate a deactivated item. Requires item.edit permission.',
)
async def reactivate_item(
    item_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('item.edit'))],
) -> Item:
    """
    Reactivate a deactivated item.

    Sets item status back to ACTIVE.

    **Path parameters:**
    - item_id: Item ID to reactivate

    **Permissions required:** item.edit
    """
    service = ItemService(db)
    return await service.reactivate_item(item_id, reactivated_by=current_user.id)  # type: ignore


# ==================== Packages Router ====================

packages_router = APIRouter(prefix='/packages', tags=['packages'])


@packages_router.post(
    '',
    response_model=PackagePublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create package',
    description='Create a new service package. Requires package.create permission.',
)
async def create_package(
    data: PackageCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.create'))],
) -> Package:
    """
    Create a new service package.

    **Required fields:**
    - code: Unique package code
    - name: Package name
    - session_type: Type of session (Studio, External, Both)
    - base_price: Base price for the package
    - estimated_editing_days: Estimated days for editing (1-365)

    **Optional fields:**
    - description: Package description

    **Permissions required:** package.create
    """
    service = PackageService(db)
    return await service.create_package(data, created_by=current_user.id)  # type: ignore


@packages_router.get(
    '',
    response_model=list[PackagePublic],
    status_code=status.HTTP_200_OK,
    summary='List packages',
    description='Get paginated list of packages with optional filters. Requires package.create permission.',
)
async def list_packages(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.create'))],
    active_only: Annotated[
        bool, Query(description='Filter for active packages only')
    ] = False,
    session_type: Annotated[
        SessionType | None,
        Query(description='Filter by session type (Studio, External, Both)'),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 100,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> list[Package]:
    """
    List packages with pagination and optional filters.

    **Query parameters:**
    - active_only: If true, return only active packages (default: false)
    - session_type: Filter by session type (Studio/External/Both)
    - limit: Maximum number of packages to return (1-100, default: 100)
    - offset: Number of packages to skip for pagination (default: 0)

    **Permissions required:** package.view
    """
    service = PackageService(db)
    return await service.list_packages(
        active_only=active_only, session_type=session_type, limit=limit, offset=offset
    )


@packages_router.get(
    '/{package_id}',
    response_model=PackageDetail,
    status_code=status.HTTP_200_OK,
    summary='Get package by ID with items',
    description='Get package information by ID with included items. Requires package.create permission.',
)
async def get_package(
    package_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.create'))],
) -> PackageDetail:
    """
    Get package by ID with all included items.

    Returns package information along with the list of items it contains.

    **Path parameters:**
    - package_id: Package ID to retrieve

    **Permissions required:** package.view
    """
    service = PackageService(db)
    package = await service.get_package_with_items(package_id)
    items = await service.get_package_items_detail(package_id)

    # Convert to PackageDetail schema
    return PackageDetail(
        id=package.id,  # type: ignore
        code=package.code,
        name=package.name,
        description=package.description,
        session_type=package.session_type,
        base_price=package.base_price,
        estimated_editing_days=package.estimated_editing_days,
        status=package.status,
        created_at=package.created_at,
        updated_at=package.updated_at,
        items=items,
    )


@packages_router.patch(
    '/{package_id}',
    response_model=PackagePublic,
    status_code=status.HTTP_200_OK,
    summary='Update package',
    description='Update package information. Requires package.edit permission.',
)
async def update_package(
    package_id: int,
    data: PackageUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.edit'))],
) -> Package:
    """
    Update package information.

    **Path parameters:**
    - package_id: Package ID to update

    **Optional fields (all):**
    - code: Updated unique code
    - name: Updated name
    - description: Updated description
    - session_type: Updated session type
    - base_price: Updated base price
    - estimated_editing_days: Updated editing days (1-365)
    - status: Updated status (ACTIVE/INACTIVE)

    **Permissions required:** package.edit
    """
    service = PackageService(db)
    return await service.update_package(package_id, data, updated_by=current_user.id)  # type: ignore


@packages_router.delete(
    '/{package_id}',
    status_code=status.HTTP_200_OK,
    response_model=PackagePublic,
    summary='Deactivate package',
    description='Deactivate (soft delete) a package. Requires package.delete permission.',
)
async def deactivate_package(
    package_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.delete'))],
) -> Package:
    """
    Deactivate a package (soft delete).

    Sets package status to INACTIVE. Package can be reactivated later.

    **Path parameters:**
    - package_id: Package ID to deactivate

    **Permissions required:** package.delete
    """
    service = PackageService(db)
    return await service.deactivate_package(package_id, deactivated_by=current_user.id)  # type: ignore


@packages_router.put(
    '/{package_id}/reactivate',
    response_model=PackagePublic,
    status_code=status.HTTP_200_OK,
    summary='Reactivate package',
    description='Reactivate a deactivated package. Requires package.edit permission.',
)
async def reactivate_package(
    package_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.edit'))],
) -> Package:
    """
    Reactivate a deactivated package.

    Sets package status back to ACTIVE.

    **Path parameters:**
    - package_id: Package ID to reactivate

    **Permissions required:** package.edit
    """
    service = PackageService(db)
    return await service.reactivate_package(package_id, reactivated_by=current_user.id)  # type: ignore


# ==================== Package-Item Management Endpoints ====================


@packages_router.post(
    '/{package_id}/items',
    response_model=PackageItemDetail,
    status_code=status.HTTP_201_CREATED,
    summary='Add item to package',
    description='Add an item to a package. Requires package.edit permission.',
)
async def add_item_to_package(
    package_id: int,
    data: PackageItemCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.edit'))],
) -> PackageItemDetail:
    """
    Add an item to a package.

    **Path parameters:**
    - package_id: Package ID

    **Request body:**
    - item_id: Item ID to add
    - quantity: Quantity of the item (default: 1)
    - display_order: Display order in package (optional)

    **Permissions required:** package.edit
    """
    service = PackageService(db)
    package_item = await service.add_item_to_package(package_id, data)

    # Load item details to return PackageItemDetail
    await db.refresh(package_item, ['item'])

    return PackageItemDetail(
        item_id=package_item.item_id,
        item_code=package_item.item.code,
        item_name=package_item.item.name,
        quantity=package_item.quantity,
        display_order=package_item.display_order,
    )


@packages_router.delete(
    '/{package_id}/items/{item_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remove item from package',
    description='Remove an item from a package. Requires package.edit permission.',
)
async def remove_item_from_package(
    package_id: int,
    item_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.edit'))],
) -> None:
    """
    Remove an item from a package.

    **Path parameters:**
    - package_id: Package ID
    - item_id: Item ID to remove

    **Permissions required:** package.edit
    """
    service = PackageService(db)
    await service.remove_item_from_package(package_id, item_id)


@packages_router.get(
    '/{package_id}/items',
    response_model=list[PackageItemDetail],
    status_code=status.HTTP_200_OK,
    summary='Get package items',
    description='Get all items in a package with details. Requires package.create permission.',
)
async def get_package_items(
    package_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('package.create'))],
) -> list[PackageItemDetail]:
    """
    Get all items included in a package.

    **Path parameters:**
    - package_id: Package ID

    **Permissions required:** package.view
    """
    service = PackageService(db)
    return await service.get_package_items_detail(package_id)


# ==================== Rooms Router ====================

rooms_router = APIRouter(prefix='/rooms', tags=['rooms'])


@rooms_router.post(
    '',
    response_model=RoomPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create room',
    description='Create a new studio room. Requires room.create permission.',
)
async def create_room(
    data: RoomCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.create'))],
) -> Room:
    """
    Create a new studio room.

    **Required fields:**
    - name: Unique room name

    **Optional fields:**
    - description: Room description
    - capacity: Maximum capacity (number of people)
    - hourly_rate: Hourly rental rate (optional)

    **Permissions required:** room.create
    """
    service = RoomService(db)
    return await service.create_room(data)


@rooms_router.get(
    '',
    response_model=list[RoomPublic],
    status_code=status.HTTP_200_OK,
    summary='List rooms',
    description='Get paginated list of rooms with optional filters. Requires room.create permission.',
)
async def list_rooms(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.create'))],
    active_only: Annotated[
        bool, Query(description='Filter for active rooms only')
    ] = False,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 100,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> list[Room]:
    """
    List rooms with pagination and optional filters.

    **Query parameters:**
    - active_only: If true, return only active rooms (default: false)
    - limit: Maximum number of rooms to return (1-100, default: 100)
    - offset: Number of rooms to skip for pagination (default: 0)

    **Permissions required:** room.view
    """
    service = RoomService(db)
    return await service.list_rooms(active_only=active_only, limit=limit, offset=offset)


@rooms_router.get(
    '/{room_id}',
    response_model=RoomPublic,
    status_code=status.HTTP_200_OK,
    summary='Get room by ID',
    description='Get room information by ID. Requires room.create permission.',
)
async def get_room(
    room_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.create'))],
) -> Room:
    """
    Get room by ID.

    **Path parameters:**
    - room_id: Room ID to retrieve

    **Permissions required:** room.view
    """
    service = RoomService(db)
    return await service.get_room(room_id)


@rooms_router.patch(
    '/{room_id}',
    response_model=RoomPublic,
    status_code=status.HTTP_200_OK,
    summary='Update room',
    description='Update room information. Requires room.edit permission.',
)
async def update_room(
    room_id: int,
    data: RoomUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.edit'))],
) -> Room:
    """
    Update room information.

    **Path parameters:**
    - room_id: Room ID to update

    **Optional fields (all):**
    - name: Updated unique name
    - description: Updated description
    - capacity: Updated capacity
    - hourly_rate: Updated hourly rate
    - status: Updated status (ACTIVE/INACTIVE/MAINTENANCE)

    **Permissions required:** room.edit
    """
    service = RoomService(db)
    return await service.update_room(room_id, data)


@rooms_router.delete(
    '/{room_id}',
    status_code=status.HTTP_200_OK,
    response_model=RoomPublic,
    summary='Deactivate room',
    description='Deactivate (soft delete) a room. Requires room.delete permission.',
)
async def deactivate_room(
    room_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.delete'))],
) -> Room:
    """
    Deactivate a room (soft delete).

    Sets room status to INACTIVE. Room can be reactivated later.

    **Path parameters:**
    - room_id: Room ID to deactivate

    **Permissions required:** room.delete
    """
    service = RoomService(db)
    return await service.deactivate_room(room_id)


@rooms_router.put(
    '/{room_id}/reactivate',
    response_model=RoomPublic,
    status_code=status.HTTP_200_OK,
    summary='Reactivate room',
    description='Reactivate a deactivated room. Requires room.edit permission.',
)
async def reactivate_room(
    room_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.edit'))],
) -> Room:
    """
    Reactivate a deactivated room.

    Sets room status back to ACTIVE.

    **Path parameters:**
    - room_id: Room ID to reactivate

    **Permissions required:** room.edit
    """
    service = RoomService(db)
    return await service.reactivate_room(room_id)


@rooms_router.put(
    '/{room_id}/maintenance',
    response_model=RoomPublic,
    status_code=status.HTTP_200_OK,
    summary='Set room to maintenance',
    description='Set room status to MAINTENANCE. Requires room.edit permission.',
)
async def set_room_maintenance(
    room_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('room.edit'))],
) -> Room:
    """
    Set room status to MAINTENANCE.

    Indicates room is temporarily unavailable for sessions.

    **Path parameters:**
    - room_id: Room ID

    **Permissions required:** room.edit
    """
    service = RoomService(db)
    return await service.set_maintenance(room_id)


# ==================== Main Router for Export ====================

router = APIRouter()
router.include_router(items_router)
router.include_router(packages_router)
router.include_router(rooms_router)
