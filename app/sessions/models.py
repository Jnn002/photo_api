"""
Session models for photography session management.

This module defines:
- Session: Main photography session entity
- SessionDetail: Line items for each session (denormalized for immutability)
- SessionPhotographer: Photographer assignments to sessions
- SessionPayment: Payment tracking for sessions
- SessionStatusHistory: Audit trail of status changes
"""

from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    """Photography session entity with state machine."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)

    # Client information
    client_id: int = Field(foreign_key='studio.client.id')

    # Session details
    session_type: str = Field(max_length=20)  # Studio | External
    session_date: date
    session_time: str | None = Field(default=None, max_length=10)  # e.g., "10:00"
    estimated_duration_hours: int | None = Field(default=None)
    location: str | None = Field(default=None)  # For external sessions

    # Room assignment (for studio sessions)
    room_id: int | None = Field(default=None, foreign_key='studio.room.id')

    # State machine
    status: str = Field(max_length=50)  # Request, Negotiation, Pre-scheduled, etc.

    # Financial
    total_amount: Decimal = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2)
    deposit_amount: Decimal = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2)
    balance_amount: Decimal = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2)
    paid_amount: Decimal = Field(default=Decimal('0.00'), max_digits=10, decimal_places=2)

    # Important dates
    payment_deadline: date | None = Field(default=None)
    changes_deadline: date | None = Field(default=None)
    delivery_deadline: date | None = Field(default=None)

    # Editing tracking
    editing_assigned_to: int | None = Field(default=None, foreign_key='studio.user.id')
    editing_started_at: datetime | None = Field(default=None)
    editing_completed_at: datetime | None = Field(default=None)

    # Delivery tracking
    delivery_method: str | None = Field(default=None, max_length=50)  # Digital, Physical, Both
    delivery_address: str | None = Field(default=None)
    delivered_at: datetime | None = Field(default=None)

    # Notes
    client_requirements: str | None = Field(default=None)
    internal_notes: str | None = Field(default=None)
    cancellation_reason: str | None = Field(default=None)

    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key='studio.user.id')
    cancelled_at: datetime | None = Field(default=None)
    cancelled_by: int | None = Field(default=None, foreign_key='studio.user.id')


class SessionDetail(SQLModel, table=True):
    """
    Session line items (denormalized for immutability).

    When a package is added, it "explodes" into individual items.
    Prices are denormalized to preserve historical accuracy.
    """

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key='studio.session.id')

    # Line item details
    line_type: str = Field(max_length=20)  # Item | Package | Adjustment
    reference_id: int | None = Field(default=None)  # Original item_id or package_id
    reference_type: str | None = Field(default=None, max_length=20)  # Item | Package

    # Denormalized data (CRITICAL for immutability)
    item_code: str = Field(max_length=50)
    item_name: str = Field(max_length=100)
    item_description: str | None = Field(default=None)

    # Pricing
    quantity: int = Field(default=1)
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    line_subtotal: Decimal = Field(max_digits=10, decimal_places=2)

    # Tracking
    is_delivered: bool = Field(default=False)
    delivered_at: datetime | None = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key='studio.user.id')


class SessionPhotographer(SQLModel, table=True):
    """Photographer assignments to sessions."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key='studio.session.id')
    photographer_id: int = Field(foreign_key='studio.user.id')

    # Assignment details
    role: str | None = Field(default=None, max_length=50)  # Lead, Assistant
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: int = Field(foreign_key='studio.user.id')

    # Completion tracking
    attended: bool = Field(default=False)
    attended_at: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)


class SessionPayment(SQLModel, table=True):
    """Payment records for sessions."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key='studio.session.id')

    # Payment details
    payment_type: str = Field(max_length=20)  # Deposit | Balance | Partial | Refund
    payment_method: str = Field(max_length=50)  # Cash, Card, Transfer, etc.
    amount: Decimal = Field(max_digits=10, decimal_places=2)

    # Transaction info
    transaction_reference: str | None = Field(default=None, max_length=100)
    payment_date: date
    notes: str | None = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key='studio.user.id')


class SessionStatusHistory(SQLModel, table=True):
    """Audit trail of session status changes."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key='studio.session.id')

    # Status transition
    from_status: str | None = Field(default=None, max_length=50)
    to_status: str = Field(max_length=50)

    # Context
    reason: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    # Audit
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    changed_by: int = Field(foreign_key='studio.user.id')
