"""
Session schemas for request/response DTOs.

This module defines Pydantic v2 schemas for session operations:
- Session schemas: Main photography session entity
- SessionDetail schemas: Line items for sessions
- SessionPhotographer schemas: Photographer assignments
- SessionPayment schemas: Payment tracking
- SessionStatusHistory schemas: Status change audit trail

For business rules and state machine, see files/business_rules_doc.md
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..core.enums import (
    DeliveryMethod,
    LineType,
    PaymentType,
    PhotographerRole,
    ReferenceType,
    SessionStatus,
    SessionType,
)

# ==================== Session Schemas ====================


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    client_id: int = Field(..., gt=0)
    session_type: SessionType
    session_date: date
    session_time: str | None = Field(default=None, max_length=10)
    estimated_duration_hours: int | None = Field(default=None, ge=1, le=24)
    location: str | None = None
    room_id: int | None = Field(default=None, gt=0)
    client_requirements: str | None = None

    @field_validator('session_date')
    @classmethod
    def validate_future_date(cls, v: date) -> date:
        """Ensure session_date is in the future."""
        if v < date.today():
            raise ValueError('session_date must be in the future')
        return v

    @field_validator('session_time')
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        """Validate time format (HH:MM)."""
        if v is None:
            return None

        if not v or not v.strip():
            return None

        # Basic format validation (HH:MM)
        parts = v.strip().split(':')
        if len(parts) != 2:
            raise ValueError('session_time must be in format HH:MM')

        try:
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError('Invalid time values')
        except ValueError:
            raise ValueError('session_time must be in format HH:MM')

        return v.strip()

    @model_validator(mode='after')
    def validate_session_requirements(self) -> Self:
        """Validate session type-specific requirements."""
        if self.session_type == SessionType.EXTERNAL and not self.location:
            raise ValueError('location is required for External sessions')

        if self.session_type == SessionType.STUDIO and not self.room_id:
            raise ValueError('room_id is required for Studio sessions')

        if self.session_type == SessionType.EXTERNAL and self.room_id:
            raise ValueError('room_id should not be set for External sessions')

        return self


class SessionUpdate(BaseModel):
    """Schema for updating an existing session (all fields optional)."""

    session_date: date | None = None
    session_time: str | None = Field(default=None, max_length=10)
    estimated_duration_hours: int | None = Field(default=None, ge=1, le=24)
    location: str | None = None
    room_id: int | None = Field(default=None, gt=0)
    client_requirements: str | None = None
    internal_notes: str | None = None
    delivery_method: DeliveryMethod | None = None
    delivery_address: str | None = None

    @field_validator('session_date')
    @classmethod
    def validate_future_date(cls, v: date | None) -> date | None:
        """Ensure session_date is in the future if provided."""
        if v is not None and v < date.today():
            raise ValueError('session_date must be in the future')
        return v

    @field_validator('session_time')
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        """Validate time format (HH:MM) if provided."""
        if v is None or not v.strip():
            return None

        parts = v.strip().split(':')
        if len(parts) != 2:
            raise ValueError('session_time must be in format HH:MM')

        try:
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError('Invalid time values')
        except ValueError:
            raise ValueError('session_time must be in format HH:MM')

        return v.strip()


class SessionPublic(BaseModel):
    """Public session response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    session_type: SessionType
    session_date: date
    session_time: str | None
    estimated_duration_hours: int | None
    location: str | None
    room_id: int | None
    status: SessionStatus
    total_amount: Decimal
    deposit_amount: Decimal
    balance_amount: Decimal
    paid_amount: Decimal
    payment_deadline: date | None
    changes_deadline: date | None
    delivery_deadline: date | None
    client_requirements: str | None
    created_at: datetime
    updated_at: datetime


class SessionDetail(SessionPublic):
    """Detailed session response with additional fields."""

    editing_assigned_to: int | None
    editing_started_at: datetime | None
    editing_completed_at: datetime | None
    delivery_method: DeliveryMethod | None
    delivery_address: str | None
    delivered_at: datetime | None
    internal_notes: str | None
    cancellation_reason: str | None
    cancelled_at: datetime | None
    cancelled_by: int | None


# ==================== Session Detail (Line Items) Schemas ====================


class SessionDetailCreate(BaseModel):
    """Schema for creating a session detail line item."""

    line_type: LineType
    reference_id: int | None = Field(default=None, gt=0)
    reference_type: ReferenceType | None = None
    item_code: str = Field(..., min_length=1, max_length=50)
    item_name: str = Field(..., min_length=1, max_length=100)
    item_description: str | None = None
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)

    @field_validator('item_code', 'item_name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @model_validator(mode='after')
    def validate_reference_consistency(self) -> Self:
        """Ensure reference fields are consistent."""
        if self.line_type in [LineType.ITEM, LineType.PACKAGE]:
            if not self.reference_id or not self.reference_type:
                raise ValueError(
                    'reference_id and reference_type required for Item/Package lines'
                )
        return self


class SessionDetailPublic(BaseModel):
    """Public session detail response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    line_type: LineType
    reference_id: int | None
    reference_type: ReferenceType | None
    item_code: str
    item_name: str
    item_description: str | None
    quantity: int
    unit_price: Decimal
    line_subtotal: Decimal
    is_delivered: bool
    delivered_at: datetime | None
    created_at: datetime


# ==================== Session Photographer Schemas ====================


class SessionPhotographerAssign(BaseModel):
    """Schema for assigning a photographer to a session."""

    session_id: int = Field(..., gt=0)
    photographer_id: int = Field(..., gt=0)
    role: PhotographerRole | None = None

    @field_validator('session_id', 'photographer_id')
    @classmethod
    def validate_positive_id(cls, v: int) -> int:
        """Ensure IDs are positive."""
        if v <= 0:
            raise ValueError('ID must be greater than 0')
        return v


class SessionPhotographerUpdate(BaseModel):
    """Schema for updating photographer assignment."""

    attended: bool
    notes: str | None = None


class SessionPhotographerPublic(BaseModel):
    """Public session photographer response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    photographer_id: int
    role: PhotographerRole | None
    assigned_at: datetime
    assigned_by: int
    attended: bool
    attended_at: datetime | None
    notes: str | None


# ==================== Session Payment Schemas ====================


class SessionPaymentCreate(BaseModel):
    """Schema for creating a session payment."""

    session_id: int = Field(..., gt=0)
    payment_type: PaymentType
    payment_method: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    transaction_reference: str | None = Field(default=None, max_length=100)
    payment_date: date
    notes: str | None = None

    @field_validator('payment_method')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure payment_method is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('amount')
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount is positive."""
        if v <= 0:
            raise ValueError('amount must be greater than 0')
        return v

    @field_validator('payment_date')
    @classmethod
    def validate_past_or_present_date(cls, v: date) -> date:
        """Ensure payment_date is not in the future."""
        if v > date.today():
            raise ValueError('payment_date cannot be in the future')
        return v


class SessionPaymentPublic(BaseModel):
    """Public session payment response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    payment_type: PaymentType
    payment_method: str
    amount: Decimal
    transaction_reference: str | None
    payment_date: date
    notes: str | None
    created_at: datetime
    created_by: int


# ==================== Session Status History Schemas ====================


class SessionStatusHistoryCreate(BaseModel):
    """Schema for creating a session status history record."""

    session_id: int = Field(..., gt=0)
    from_status: str | None = Field(default=None, max_length=50)
    to_status: str = Field(..., max_length=50)
    reason: str | None = None
    notes: str | None = None

    @field_validator('to_status')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure to_status is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()


class SessionStatusHistoryPublic(BaseModel):
    """Public session status history response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    from_status: str | None
    to_status: str
    reason: str | None
    notes: str | None
    changed_at: datetime
    changed_by: int


# ==================== Session Action Schemas ====================


class SessionStatusTransition(BaseModel):
    """Schema for transitioning session status."""

    to_status: str = Field(..., min_length=1, max_length=50)
    reason: str | None = None
    notes: str | None = None

    @field_validator('to_status')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure to_status is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('to_status')
    @classmethod
    def validate_allowed_status(cls, v: str) -> str:
        """Validate that status is one of the allowed values."""
        allowed_statuses = {e.value for e in SessionStatus}
        if v not in allowed_statuses:
            raise ValueError(f'Invalid status. Must be one of: {allowed_statuses}')
        return v


class SessionCancellation(BaseModel):
    """Schema for canceling a session."""

    cancellation_reason: str = Field(..., min_length=1)
    initiated_by: str = Field(..., pattern='^(Client|Studio)$')
    notes: str | None = None

    @field_validator('cancellation_reason')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure cancellation_reason is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()


class SessionEditorAssignment(BaseModel):
    """Schema for assigning an editor to a session."""

    editor_id: int = Field(..., gt=0)

    @field_validator('editor_id')
    @classmethod
    def validate_positive_id(cls, v: int) -> int:
        """Ensure editor_id is positive."""
        if v <= 0:
            raise ValueError('editor_id must be greater than 0')
        return v


class SessionMarkReady(BaseModel):
    """Schema for marking session as ready for delivery (editor completed)."""

    notes: str | None = None


class SessionDelivery(BaseModel):
    """Schema for marking session as delivered."""

    delivery_method: DeliveryMethod
    delivery_address: str | None = None
    notes: str | None = None

    @model_validator(mode='after')
    def validate_delivery_requirements(self) -> Self:
        """Validate delivery method-specific requirements."""
        if self.delivery_method in [
            DeliveryMethod.PHYSICAL,
            DeliveryMethod.BOTH,
        ] and not self.delivery_address:
            raise ValueError('delivery_address required for Physical delivery')
        return self
