"""
Catalog schemas for request/response DTOs.

This module defines Pydantic v2 schemas for catalog operations:
- Item schemas: Individual service items
- Package schemas: Service packages with items
- Room schemas: Studio spaces
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ==================== Item Schemas ====================


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    item_type: str = Field(
        ..., pattern='^(Digital Photo|Printed Photo|Album|Video|Other)$'
    )
    unit_price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    unit_measure: str = Field(..., pattern='^(Unit|Hour|Package)$')
    default_quantity: int | None = Field(default=None, ge=1)

    @field_validator('code', 'name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('unit_price')
    @classmethod
    def validate_positive_price(cls, v: Decimal) -> Decimal:
        """Ensure price is positive."""
        if v <= 0:
            raise ValueError('unit_price must be greater than 0')
        return v


class ItemUpdate(BaseModel):
    """Schema for updating an existing item (all fields optional)."""

    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    item_type: str | None = Field(
        default=None, pattern='^(Digital Photo|Printed Photo|Album|Video|Other)$'
    )
    unit_price: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    unit_measure: str | None = Field(default=None, pattern='^(Unit|Hour|Package)$')
    default_quantity: int | None = Field(default=None, ge=1)
    status: str | None = Field(default=None, pattern='^(Active|Inactive)$')

    @field_validator('code', 'name')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure fields are not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None

    @field_validator('unit_price')
    @classmethod
    def validate_positive_price(cls, v: Decimal | None) -> Decimal | None:
        """Ensure price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('unit_price must be greater than 0')
        return v


class ItemPublic(BaseModel):
    """Public item response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    item_type: str
    unit_price: Decimal
    unit_measure: str
    default_quantity: int | None
    status: str
    created_at: datetime
    updated_at: datetime


# ==================== Package Schemas ====================


class PackageItemDetail(BaseModel):
    """Item detail within a package (for PackageDetail response)."""

    model_config = ConfigDict(from_attributes=True)

    item_id: int
    item_code: str
    item_name: str
    quantity: int
    display_order: int | None


class PackageCreate(BaseModel):
    """Schema for creating a new package."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    session_type: str = Field(..., pattern='^(Studio|External|Both)$')
    base_price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    estimated_editing_days: int = Field(..., ge=1, le=365)

    @field_validator('code', 'name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('base_price')
    @classmethod
    def validate_positive_price(cls, v: Decimal) -> Decimal:
        """Ensure price is positive."""
        if v <= 0:
            raise ValueError('base_price must be greater than 0')
        return v


class PackageUpdate(BaseModel):
    """Schema for updating an existing package (all fields optional)."""

    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    session_type: str | None = Field(default=None, pattern='^(Studio|External|Both)$')
    base_price: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    estimated_editing_days: int | None = Field(default=None, ge=1, le=365)
    status: str | None = Field(default=None, pattern='^(Active|Inactive)$')

    @field_validator('code', 'name')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure fields are not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None

    @field_validator('base_price')
    @classmethod
    def validate_positive_price(cls, v: Decimal | None) -> Decimal | None:
        """Ensure price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('base_price must be greater than 0')
        return v


class PackagePublic(BaseModel):
    """Public package response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    session_type: str
    base_price: Decimal
    estimated_editing_days: int
    status: str
    created_at: datetime
    updated_at: datetime


class PackageDetail(PackagePublic):
    """Package with included items."""

    items: list[PackageItemDetail] = []


# ==================== Room Schemas ====================


class RoomCreate(BaseModel):
    """Schema for creating a new room."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    capacity: int | None = Field(default=None, ge=1)
    hourly_rate: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )

    @field_validator('name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('hourly_rate')
    @classmethod
    def validate_non_negative_rate(cls, v: Decimal | None) -> Decimal | None:
        """Ensure hourly rate is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('hourly_rate must be non-negative')
        return v


class RoomUpdate(BaseModel):
    """Schema for updating an existing room (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    capacity: int | None = Field(default=None, ge=1)
    hourly_rate: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    status: str | None = Field(default=None, pattern='^(Active|Inactive|Maintenance)$')

    @field_validator('name')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure name is not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None

    @field_validator('hourly_rate')
    @classmethod
    def validate_non_negative_rate(cls, v: Decimal | None) -> Decimal | None:
        """Ensure hourly rate is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('hourly_rate must be non-negative')
        return v


class RoomPublic(BaseModel):
    """Public room response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    capacity: int | None
    hourly_rate: Decimal | None
    status: str
    created_at: datetime
    updated_at: datetime


# ==================== Package-Item Link Schemas ====================


class PackageItemCreate(BaseModel):
    """Schema for adding an item to a package."""

    item_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1)
    display_order: int | None = Field(default=None, ge=0)

    @field_validator('item_id')
    @classmethod
    def validate_positive_id(cls, v: int) -> int:
        """Ensure item_id is positive."""
        if v <= 0:
            raise ValueError('item_id must be greater than 0')
        return v
