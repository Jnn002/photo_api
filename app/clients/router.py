"""
Client routers for client management endpoints.

This module exposes REST endpoints for:
- Client CRUD operations
- Client search and filtering
- Client activation/deactivation
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field

from app.clients.models import Client
from app.clients.schemas import ClientCreate, ClientPublic, ClientUpdate
from app.clients.service import ClientService
from app.core.dependencies import SessionDep
from app.core.enums import ClientType
from app.core.permissions import require_permission
from app.core.schemas import PaginatedResponse
from app.users.models import User

# ==================== Clients Router ====================

clients_router = APIRouter(prefix='/clients', tags=['clients'])


@clients_router.post(
    '',
    response_model=ClientPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create client',
    description='Create a new client. Requires client.create permission.',
)
async def create_client(
    data: ClientCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('client.create'))],
) -> Client:
    """
    Create a new client.

    **Required fields:**
    - full_name: Client's full name
    - email: Unique email address
    - primary_phone: Primary contact phone number
    - client_type: Type of client (Individual or Institutional)

    **Optional fields:**
    - secondary_phone: Secondary contact phone number
    - delivery_address: Address for material delivery
    - notes: Additional notes about the client

    **Permissions required:** client.create
    """
    service = ClientService(db)
    return await service.create_client(data, created_by=current_user.id)  # type: ignore


@clients_router.get(
    '',
    response_model=PaginatedResponse[ClientPublic],
    status_code=status.HTTP_200_OK,
    summary='List clients',
    description='Get paginated list of clients with optional filters. Requires client.view permission.',
)
async def list_clients(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('client.view'))],
    active_only: Annotated[
        bool, Query(description='Filter for active clients only')
    ] = False,
    client_type: Annotated[
        ClientType | None,
        Query(description='Filter by client type (Individual or Institutional)'),
    ] = None,
    search: Annotated[
        str | None,
        Query(description='Search by name (case-insensitive partial match)'),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[ClientPublic]:
    """
    List clients with pagination and optional filters.

    Returns paginated response with metadata for Angular Material tables.

    **Query parameters:**
    - active_only: If true, return only active clients (default: false)
    - client_type: Filter by type (Individual/Institutional)
    - search: Search by name (case-insensitive partial match)
    - limit: Maximum number of clients to return (1-100, default: 50)
    - offset: Number of clients to skip for pagination (default: 0)

    **Example response:**
    ```json
    {
        "items": [
            {"id": 1, "full_name": "John Doe", ...},
            {"id": 2, "full_name": "Jane Smith", ...}
        ],
        "total": 150,
        "limit": 50,
        "offset": 0,
        "has_more": true
    }
    ```

    **Permissions required:** client.view
    """
    service = ClientService(db)

    # Get items and total count in parallel would be more efficient, but for simplicity:
    items = await service.list_clients(
        active_only=active_only,
        client_type=client_type,
        search=search,
        limit=limit,
        offset=offset,
    )

    total = await service.count_clients(
        active_only=active_only, client_type=client_type, search=search
    )

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@clients_router.get(
    '/{client_id}',
    response_model=ClientPublic,
    status_code=status.HTTP_200_OK,
    summary='Get client by ID',
    description='Get client information by ID. Requires client.view permission.',
)
async def get_client(
    client_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('client.view'))],
) -> Client:
    """
    Get client by ID.

    **Path parameters:**
    - client_id: Client ID to retrieve

    **Permissions required:** client.read
    """
    service = ClientService(db)
    return await service.get_client(client_id)


@clients_router.patch(
    '/{client_id}',
    response_model=ClientPublic,
    status_code=status.HTTP_200_OK,
    summary='Update client',
    description='Update client information. Requires client.edit permission.',
)
async def update_client(
    client_id: Annotated[int, Field(gt=0)],
    data: ClientUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('client.edit'))],
) -> Client:
    """
    Update client information.

    **Path parameters:**
    - client_id: Client ID to update

    **Optional fields (all):**
    - full_name: Updated full name
    - email: Updated email (must be unique)
    - primary_phone: Updated primary phone
    - secondary_phone: Updated secondary phone
    - delivery_address: Updated delivery address
    - client_type: Updated client type
    - notes: Updated notes
    - status: Updated status (ACTIVE/INACTIVE)

    **Permissions required:** client.edit
    """
    service = ClientService(db)
    return await service.update_client(client_id, data, updated_by=current_user.id)  # type: ignore


@clients_router.delete(
    '/{client_id}',
    status_code=status.HTTP_200_OK,
    response_model=ClientPublic,
    summary='Deactivate client',
    description='Deactivate (soft delete) a client. Requires client.delete permission.',
)
async def deactivate_client(
    client_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('client.delete'))],
) -> Client:
    """
    Deactivate a client (soft delete).

    Sets client status to INACTIVE. Client can be reactivated later.

    **Path parameters:**
    - client_id: Client ID to deactivate

    **Permissions required:** client.delete
    """
    service = ClientService(db)
    return await service.deactivate_client(client_id, deactivated_by=current_user.id)  # type: ignore


@clients_router.put(
    '/{client_id}/reactivate',
    response_model=ClientPublic,
    status_code=status.HTTP_200_OK,
    summary='Reactivate client',
    description='Reactivate a deactivated client. Requires client.edit permission.',
)
async def reactivate_client(
    client_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('client.edit'))],
) -> Client:
    """
    Reactivate a deactivated client.

    Sets client status back to ACTIVE.

    **Path parameters:**
    - client_id: Client ID to reactivate

    **Permissions required:** client.edit
    """
    service = ClientService(db)
    return await service.reactivate_client(client_id, reactivated_by=current_user.id)  # type: ignore


# ==================== Main Router for Export ====================

router = APIRouter()
router.include_router(clients_router)
