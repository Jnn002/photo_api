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
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from ..core.enums import (
    DeliveryMethod,
    LineType,
    PaymentType,
    PhotographerRole,
    ReferenceType,
    SessionStatus,
    SessionType,
)
from ..core.time_utils import get_current_utc_time

if TYPE_CHECKING:
    from ..catalog.models import Room
    from ..clients.models import Client
    from ..users.models import User


class Session(SQLModel, table=True):
    """Photography session entity with state machine."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)

    # Client information
    client_id: int = Field(foreign_key='studio.client.id')

    # Session details
    session_type: SessionType
    session_date: date
    session_time: str | None = Field(default=None, max_length=10)  # e.g., "10:00"
    estimated_duration_hours: int | None = Field(default=None)
    location: str | None = Field(default=None)  # For external sessions

    # Room assignment (for studio sessions)
    room_id: int | None = Field(default=None, foreign_key='studio.room.id')

    # State machine
    status: SessionStatus

    # Financial
    total_amount: Decimal = Field(
        default=Decimal('0.00'), max_digits=10, decimal_places=2
    )
    deposit_amount: Decimal = Field(
        default=Decimal('0.00'), max_digits=10, decimal_places=2
    )
    balance_amount: Decimal = Field(
        default=Decimal('0.00'), max_digits=10, decimal_places=2
    )
    paid_amount: Decimal = Field(
        default=Decimal('0.00'), max_digits=10, decimal_places=2
    )

    # Important dates
    payment_deadline: date | None = Field(default=None)
    changes_deadline: date | None = Field(default=None)
    delivery_deadline: date | None = Field(default=None)

    # Editing tracking
    editing_assigned_to: int | None = Field(default=None, foreign_key='studio.user.id')
    editing_started_at: datetime | None = Field(default=None)
    editing_completed_at: datetime | None = Field(default=None)

    # Delivery tracking
    delivery_method: DeliveryMethod | None = Field(default=None)
    delivery_address: str | None = Field(default=None)
    delivered_at: datetime | None = Field(default=None)

    # Notes
    client_requirements: str | None = Field(default=None)
    internal_notes: str | None = Field(default=None)
    cancellation_reason: str | None = Field(default=None)

    # Audit fields
    created_at: datetime = Field(default_factory=get_current_utc_time)
    updated_at: datetime = Field(
        default_factory=get_current_utc_time,
        sa_column_kwargs={'onupdate': get_current_utc_time},
    )
    created_by: int = Field(foreign_key='studio.user.id')
    cancelled_at: datetime | None = Field(default=None)
    cancelled_by: int | None = Field(default=None, foreign_key='studio.user.id')

    # Relationships
    client: 'Client' = Relationship(back_populates='sessions')
    room: 'Room' = Relationship(back_populates='sessions')
    details: list['SessionDetail'] = Relationship(back_populates='session')

    photographers: list['SessionPhotographer'] = Relationship(back_populates='session')
    payments: list['SessionPayment'] = Relationship(back_populates='session')
    status_history: list['SessionStatusHistory'] = Relationship(
        back_populates='session'
    )
    # User relationships (multiple FKs to User)
    editor: 'User' = Relationship(
        back_populates='sessions_as_editor',
        sa_relationship_kwargs={'foreign_keys': 'Session.editing_assigned_to'},
    )
    creator: 'User' = Relationship(
        back_populates='created_sessions',
        sa_relationship_kwargs={'foreign_keys': 'Session.created_by'},
    )
    canceller: 'User' = Relationship(
        back_populates='cancelled_sessions',
        sa_relationship_kwargs={'foreign_keys': 'Session.cancelled_by'},
    )


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
    line_type: LineType
    reference_id: int | None = Field(default=None)  # Original item_id or package_id
    reference_type: ReferenceType | None = Field(default=None)

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
    created_at: datetime = Field(default_factory=get_current_utc_time)
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    session: 'Session' = Relationship(back_populates='details')
    creator: 'User' = Relationship(
        back_populates='created_session_details',
    )


class SessionPhotographer(SQLModel, table=True):
    """Photographer assignments to sessions."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key='studio.session.id')
    photographer_id: int = Field(foreign_key='studio.user.id')

    # Assignment details
    role: PhotographerRole | None = Field(default=None)
    assigned_at: datetime = Field(default_factory=get_current_utc_time)
    assigned_by: int = Field(foreign_key='studio.user.id')

    # Completion tracking
    attended: bool = Field(default=False)
    attended_at: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)

    # Relationships
    session: 'Session' = Relationship(back_populates='photographers')
    photographer: 'User' = Relationship(
        back_populates='photographer_assignments',
        sa_relationship_kwargs={
            'foreign_keys': 'SessionPhotographer.photographer_id',
        },
    )
    assigner: 'User' = Relationship(
        back_populates='assigned_photographer_sessions',
        sa_relationship_kwargs={
            'foreign_keys': 'SessionPhotographer.assigned_by',
        },
    )


class SessionPayment(SQLModel, table=True):
    """Payment records for sessions."""

    __table_args__ = {'schema': 'studio'}

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key='studio.session.id')

    # Payment details
    payment_type: PaymentType
    payment_method: str = Field(max_length=50)  # Cash, Card, Transfer, etc.
    amount: Decimal = Field(max_digits=10, decimal_places=2)

    # Transaction info
    transaction_reference: str | None = Field(default=None, max_length=100)
    payment_date: date
    notes: str | None = Field(default=None)

    # Audit
    created_at: datetime = Field(default_factory=get_current_utc_time)
    created_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    session: 'Session' = Relationship(back_populates='payments')
    creator: 'User' = Relationship(
        back_populates='created_payments',
    )


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
    changed_at: datetime = Field(default_factory=get_current_utc_time)
    changed_by: int = Field(foreign_key='studio.user.id')

    # Relationships
    session: 'Session' = Relationship(back_populates='status_history')
    changed_by_user: 'User' = Relationship(
        back_populates='status_changes',
    )
