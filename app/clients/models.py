"""
Client model for customer management.

This module defines the Client model for storing customer information
(individuals and institutions).
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Client(SQLModel, table=True):
    """Customer information (individuals or institutions)."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100, index=True)
    email: str = Field(unique=True, index=True, max_length=100)
    primary_phone: str = Field(max_length=20)
    secondary_phone: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = Field(default=None)
    client_type: str = Field(max_length=20)  # Individual | Institutional
    notes: str | None = Field(default=None)
    status: str = Field(default='Active', max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key='studio.user.id')
