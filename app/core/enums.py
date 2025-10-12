# app/core/enums.py
"""
Core enums for the photography studio system.

These enums provide type-safe options for various fields across the application.
"""

from enum import Enum


class ItemType(str, Enum):
    """Types of catalog items."""

    DIGITAL_PHOTO = 'Digital Photo'
    PRINTED_PHOTO = 'Printed Photo'
    ALBUM = 'Album'
    VIDEO = 'Video'
    OTHER = 'Other'


class SessionType(str, Enum):
    """Types of photography sessions."""

    STUDIO = 'Studio'
    EXTERNAL = 'External'
    BOTH = 'Both'  # For Packages that work with both types


class Status(str, Enum):
    """General status for entities (User, Role, Permission, Client, Item, Package, Room)."""

    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    MAINTENANCE = 'Maintenance'  # Only used by Room


class SessionStatus(str, Enum):
    """Session state machine statuses.

    See files/business_rules_doc.md for complete state machine rules.
    """

    REQUEST = 'Request'
    NEGOTIATION = 'Negotiation'
    PRE_SCHEDULED = 'Pre-scheduled'
    CONFIRMED = 'Confirmed'
    ASSIGNED = 'Assigned'
    ATTENDED = 'Attended'
    IN_EDITING = 'In Editing'
    READY_FOR_DELIVERY = 'Ready for Delivery'
    COMPLETED = 'Completed'
    CANCELED = 'Canceled'


class LineType(str, Enum):
    """Types of session detail line items."""

    ITEM = 'Item'
    PACKAGE = 'Package'
    ADJUSTMENT = 'Adjustment'


class ReferenceType(str, Enum):
    """Reference types for session detail line items."""

    ITEM = 'Item'
    PACKAGE = 'Package'


class PaymentType(str, Enum):
    """Types of session payments."""

    DEPOSIT = 'Deposit'
    BALANCE = 'Balance'
    PARTIAL = 'Partial'
    REFUND = 'Refund'


class DeliveryMethod(str, Enum):
    """Methods of session delivery."""

    DIGITAL = 'Digital'
    PHYSICAL = 'Physical'
    BOTH = 'Both'


class PhotographerRole(str, Enum):
    """Roles for photographer assignments."""

    LEAD = 'Lead'
    ASSISTANT = 'Assistant'


class ClientType(str, Enum):
    """Types of clients."""

    INDIVIDUAL = 'Individual'
    INSTITUTIONAL = 'Institutional'


class CancellationInitiator(str, Enum):
    """Who initiated the session cancellation."""

    CLIENT = 'Client'
    STUDIO = 'Studio'
