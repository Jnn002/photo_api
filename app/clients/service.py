"""
Client service layer for business logic.

This module implements business logic and orchestration for client operations.
It uses the repository for data access and handles transactions.
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from app.clients.models import Client
from app.clients.repository import ClientRepository
from app.clients.schemas import ClientCreate, ClientUpdate
from app.core.enums import ClientType, Status
from app.core.exceptions import (
    ClientNotFoundException,
    DuplicateEmailException,
    InactiveClientException,
)


class ClientService:
    """Service for Client business logic and orchestration."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.repo = ClientRepository(db)

    async def create_client(self, data: ClientCreate, created_by: int) -> Client:
        """
        Create a new client.

        Args:
            data: Client creation data
            created_by: ID of the user creating the client

        Returns:
            Created client

        Raises:
            DuplicateEmailException: If email already exists
        """
        # Check if email already exists
        if await self.repo.email_exists(data.email):
            raise DuplicateEmailException(f'Email {data.email} is already registered')

        # Create client entity
        client = Client(
            full_name=data.full_name,
            email=data.email,
            primary_phone=data.primary_phone,
            secondary_phone=data.secondary_phone,
            delivery_address=data.delivery_address,
            client_type=data.client_type,
            notes=data.notes,
            created_by=created_by,
        )

        # Save to database
        client = await self.repo.create(client)
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def get_client(self, client_id: int) -> Client:
        """
        Get client by ID.

        Args:
            client_id: Client ID to retrieve

        Returns:
            Client entity

        Raises:
            ClientNotFoundException: If client not found
        """
        client = await self.repo.get_by_id(client_id)

        if not client:
            raise ClientNotFoundException(f'Client with ID {client_id} not found')

        return client

    async def get_active_client(self, client_id: int) -> Client:
        """
        Get active client by ID.

        Args:
            client_id: Client ID to retrieve

        Returns:
            Client entity

        Raises:
            ClientNotFoundException: If client not found
            InactiveClientException: If client is inactive
        """
        client = await self.get_client(client_id)

        if client.status != Status.ACTIVE:
            raise InactiveClientException(
                f'Client {client.full_name} (ID: {client_id}) is inactive'
            )

        return client

    async def list_clients(
        self,
        active_only: bool = False,
        client_type: ClientType | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Client]:
        """
        List clients with optional filters.

        Args:
            active_only: If True, only return active clients
            client_type: Filter by client type (Individual/Institutional)
            search: Search by name (case-insensitive partial match)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of clients matching filters
        """
        # If search is provided, use search method
        if search:
            return await self.repo.search_by_name(search, limit, offset)

        # If client type is provided, filter by type
        if client_type:
            return await self.repo.list_by_type(client_type, limit, offset)

        # If active only, use active list method
        if active_only:
            return await self.repo.list_active(limit, offset)

        # Otherwise, list all clients
        return await self.repo.list_all(limit, offset)

    async def update_client(
        self, client_id: int, data: ClientUpdate, updated_by: int
    ) -> Client:
        """
        Update client information.

        Args:
            client_id: Client ID to update
            data: Client update data
            updated_by: ID of the user performing the update

        Returns:
            Updated client

        Raises:
            ClientNotFoundException: If client not found
            DuplicateEmailException: If new email already exists
        """
        # Get existing client
        client = await self.get_client(client_id)

        # Prepare update data (only include fields that were provided)
        update_dict = data.model_dump(exclude_unset=True)

        # If email is being changed, check uniqueness
        if 'email' in update_dict and update_dict['email'] != client.email:
            if await self.repo.email_exists(update_dict['email'], exclude_id=client_id):
                raise DuplicateEmailException(
                    f'Email {update_dict["email"]} is already registered'
                )

        # Update client
        client = await self.repo.update(client, update_dict)
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def deactivate_client(self, client_id: int, deactivated_by: int) -> Client:
        """
        Deactivate a client (soft delete).

        Args:
            client_id: Client ID to deactivate
            deactivated_by: ID of the user performing the deactivation

        Returns:
            Deactivated client

        Raises:
            ClientNotFoundException: If client not found
        """
        client = await self.get_client(client_id)

        # Soft delete
        client = await self.repo.soft_delete(client)
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def reactivate_client(self, client_id: int, reactivated_by: int) -> Client:
        """
        Reactivate a deactivated client.

        Args:
            client_id: Client ID to reactivate
            reactivated_by: ID of the user performing the reactivation

        Returns:
            Reactivated client

        Raises:
            ClientNotFoundException: If client not found
        """
        client = await self.get_client(client_id)

        # Restore
        client = await self.repo.restore(client)
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def find_by_email(self, email: str) -> Client | None:
        """
        Find client by email address.

        Args:
            email: Email address to search for

        Returns:
            Client if found, None otherwise
        """
        return await self.repo.find_by_email(email)
