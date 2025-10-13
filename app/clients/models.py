"""
Client model for customer management.

This module defines the Client model for storing customer information
(individuals and institutions).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from ..core.enums import ClientType, Status
from ..core.time_utils import get_current_utc_time

if TYPE_CHECKING:
    from ..sessions.models import Session
    from ..users.models import User


class Client(SQLModel, table=True):
    """Customer information (individuals or institutions)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100, index=True)
    email: str = Field(unique=True, index=True, max_length=100)
    primary_phone: str = Field(max_length=20)
    secondary_phone: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = Field(default=None)
    client_type: ClientType
    notes: str | None = Field(default=None)
    status: Status = Field(default=Status.ACTIVE)
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    sessions: list['Session'] = Relationship(back_populates='client')
    creator: 'User' = Relationship(
        back_populates='created_clients',
    )
