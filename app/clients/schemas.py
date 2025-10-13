"""
Client schemas for request/response DTOs.

This module defines Pydantic v2 schemas for client operations:
- ClientCreate: For creating new clients
- ClientUpdate: For updating existing clients
- ClientPublic: Public response without sensitive data
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ..core.enums import ClientType, Status


class ClientCreate(BaseModel):
    """Schema for creating a new client."""

    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    primary_phone: str = Field(..., min_length=8, max_length=20)
    secondary_phone: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = None
    client_type: ClientType
    notes: str | None = None

    @field_validator('full_name', 'primary_phone')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required string fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('secondary_phone')
    @classmethod
    def validate_secondary_phone(cls, v: str | None) -> str | None:
        """Validate secondary phone if provided."""
        if v and not v.strip():
            return None
        return v.strip() if v else None


class ClientUpdate(BaseModel):
    """Schema for updating an existing client (all fields optional)."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=100)
    primary_phone: str | None = Field(default=None, min_length=8, max_length=20)
    secondary_phone: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = None
    client_type: ClientType | None = None
    notes: str | None = None
    status: Status | None = None

    @field_validator('full_name', 'primary_phone')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure string fields are not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None


class ClientPublic(BaseModel):
    """Public client response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    primary_phone: str
    secondary_phone: str | None
    delivery_address: str | None
    client_type: ClientType
    notes: str | None
    status: Status
    created_at: datetime
    updated_at: datetime
