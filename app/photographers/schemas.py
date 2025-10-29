"""
Photographer-specific schemas for request/response DTOs.

This module defines Pydantic v2 schemas tailored for photographers:
- Limited client information (privacy-conscious)
- Session details relevant to photographers
- Team information for coordination
- Statistics and metrics

These schemas provide a restricted view compared to admin schemas,
following the principle of least privilege.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..core.enums import (
    DeliveryMethod,
    LineType,
    PhotographerRole,
    ReferenceType,
    SessionStatus,
    SessionType,
)


# ==================== Client Info Schemas ====================


class ClientBasicInfo(BaseModel):
    """
    Limited client information for photographers.

    Only includes fields necessary for coordination (per permissions_doc.md 5.3).
    Does NOT include: secondary_phone, delivery_address, notes, client_type.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    primary_phone: str


# ==================== Session Detail Schemas ====================


class SessionDetailBasicInfo(BaseModel):
    """
    Basic session line item information for photographers.

    Photographers can see what items/packages are included to prepare,
    but don't need to see all financial details.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    line_type: LineType
    reference_type: ReferenceType | None
    item_code: str
    item_name: str
    item_description: str | None
    quantity: int


# ==================== Photographer Assignment Schemas ====================


class PhotographerAssignmentInfo(BaseModel):
    """Information about a photographer assigned to a session."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    photographer_id: int
    photographer_name: str  # Will be populated from User
    role: PhotographerRole | None
    assigned_at: datetime
    attended: bool
    attended_at: datetime | None


class SessionTeamInfo(BaseModel):
    """Team of photographers assigned to a session."""

    session_id: int
    photographers: list[PhotographerAssignmentInfo]


# ==================== Session View Schemas ====================


class SessionPhotographerListItem(BaseModel):
    """
    Compact session info for list views (my assignments).

    Includes essential information for photographers to see their upcoming
    and past assignments at a glance.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str  # Denormalized for list view performance
    session_type: SessionType
    session_date: date
    session_time: str | None
    estimated_duration_hours: int | None
    location: str | None
    status: SessionStatus
    my_role: PhotographerRole | None
    my_attended: bool
    my_attended_at: datetime | None


class SessionPhotographerView(BaseModel):
    """
    Detailed session information for photographers.

    This is the primary schema photographers use to view session details.
    Includes all information needed to prepare and execute the session,
    but excludes sensitive financial data and internal notes.
    """

    model_config = ConfigDict(from_attributes=True)

    # Core session info
    id: int
    session_type: SessionType
    session_date: date
    session_time: str | None
    estimated_duration_hours: int | None
    location: str | None
    room_id: int | None
    status: SessionStatus

    # Client info (limited)
    client: ClientBasicInfo

    # Session requirements
    client_requirements: str | None

    # Delivery info (for context)
    delivery_method: DeliveryMethod | None
    delivery_deadline: date | None

    # Session items (what they're shooting)
    details: list[SessionDetailBasicInfo]

    # My assignment info
    my_assignment_id: int
    my_role: PhotographerRole | None
    my_assigned_at: datetime
    my_attended: bool
    my_attended_at: datetime | None
    my_notes: str | None

    # Timestamps
    created_at: datetime
    updated_at: datetime


# ==================== Action Schemas ====================


class MarkAttendedRequest(BaseModel):
    """Schema for photographer marking session as attended."""

    attended: bool = Field(
        default=True, description='Mark as attended (true) or unmark (false)'
    )
    notes: str | None = Field(
        default=None,
        description='Optional notes or observations about the session',
        max_length=1000,
    )


# ==================== Statistics Schemas ====================


class PhotographerStats(BaseModel):
    """Statistics and metrics for a photographer."""

    # Assignment counts
    total_assignments: int
    upcoming_sessions: int
    attended_sessions: int
    pending_sessions: int  # Assigned but not yet attended

    # Recent assignments (next 7 days)
    next_session_date: date | None
    sessions_this_week: int

    # All-time stats
    total_sessions_completed: int
