"""
Client repository for database operations.

This module provides data access methods for Client entities using
SQLModel's native async methods (session.exec, session.get, sqlmodel_update).
"""

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.clients.models import Client


class ClientRepository:
    """Repository for Client database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, client_id: int) -> Client | None:
        """
        Get client by ID using SQLModel's native get method.

        Args:
            client_id: The client ID to search for

        Returns:
            Client if found, None otherwise
        """
        return await self.db.get(Client, client_id)

    async def find_by_email(self, email: str) -> Client | None:
        """
        Find client by email address.

        Args:
            email: The email address to search for

        Returns:
            Client if found, None otherwise
        """
        statement = select(Client).where(Client.email == email)
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Client]:
        """
        List all clients with pagination.

        Args:
            limit: Maximum number of clients to return (default: 100)
            offset: Number of clients to skip (default: 0)

        Returns:
            List of clients
        """
        statement = (
            select(Client)
            .order_by(col(Client.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Client]:
        """
        List active clients with pagination.

        Args:
            limit: Maximum number of clients to return (default: 100)
            offset: Number of clients to skip (default: 0)

        Returns:
            List of active clients
        """
        statement = (
            select(Client)
            .where(Client.status == 'Active')
            .order_by(col(Client.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_type(
        self, client_type: str, limit: int = 100, offset: int = 0
    ) -> list[Client]:
        """
        List clients by type (Individual or Institutional).

        Args:
            client_type: Type of client ('Individual' or 'Institutional')
            limit: Maximum number of clients to return (default: 100)
            offset: Number of clients to skip (default: 0)

        Returns:
            List of clients matching the type
        """
        statement = (
            select(Client)
            .where(Client.client_type == client_type)
            .where(Client.status == 'Active')
            .order_by(Client.full_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def search_by_name(
        self, name: str, limit: int = 100, offset: int = 0
    ) -> list[Client]:
        """
        Search clients by name (case-insensitive partial match).

        Args:
            name: Name to search for (partial match)
            limit: Maximum number of clients to return (default: 100)
            offset: Number of clients to skip (default: 0)

        Returns:
            List of clients matching the name search
        """
        search_pattern = f'%{name}%'
        statement = (
            select(Client)
            .where(col(Client.full_name).ilike(search_pattern))
            .where(Client.status == 'Active')
            .order_by(col(Client.full_name))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, client: Client) -> Client:
        """
        Create a new client.

        Args:
            client: Client entity to create

        Returns:
            Created client with ID assigned
        """
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def update(self, client: Client, data: dict) -> Client:
        """
        Update an existing client using SQLModel's native update method.

        Args:
            client: Client entity to update
            data: Dictionary with fields to update

        Returns:
            Updated client
        """
        client.sqlmodel_update(data)
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def soft_delete(self, client: Client) -> Client:
        """
        Soft delete a client by setting status to Inactive.

        Args:
            client: Client entity to soft delete

        Returns:
            Updated client with Inactive status
        """
        client.status = 'Inactive'
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def restore(self, client: Client) -> Client:
        """
        Restore a soft-deleted client by setting status to Active.

        Args:
            client: Client entity to restore

        Returns:
            Updated client with Active status
        """
        client.status = 'Active'
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def exists(self, client_id: int) -> bool:
        """
        Check if a client exists by ID.

        Args:
            client_id: The client ID to check

        Returns:
            True if client exists, False otherwise
        """
        client = await self.get_by_id(client_id)
        return client is not None

    async def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        """
        Check if an email already exists (for uniqueness validation).

        Args:
            email: Email to check
            exclude_id: Optional client ID to exclude from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        statement = select(Client).where(Client.email == email)

        if exclude_id:
            statement = statement.where(Client.id != exclude_id)

        result = await self.db.exec(statement)
        client = result.first()
        return client is not None
