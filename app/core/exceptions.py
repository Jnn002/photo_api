"""
Custom exceptions for the Photography Studio API.

This module defines application-specific exceptions with error codes for
consistent error handling across the API.
"""


# ==================== Base Exception ====================


class StudioException(Exception):
    """
    Base exception for all Photography Studio exceptions.

    All custom exceptions inherit from this base class to allow
    centralized exception handling.
    """

    pass


# ==================== Authentication & Authorization Exceptions ====================


class InvalidPasswordFormatException(StudioException):
    """Password does not meet complexity requirements."""

    pass


class UnauthorizedException(StudioException):
    """User is not authenticated."""

    pass


class InvalidCredentialsException(StudioException):
    """Invalid email or password during login."""

    pass


class TokenExpiredException(StudioException):
    """JWT token has expired."""

    pass


class InvalidTokenException(StudioException):
    """JWT token is invalid or malformed."""

    pass


class InsufficientPermissionsException(StudioException):
    """User lacks required permissions for this operation."""

    pass


class InactiveUserException(StudioException):
    """User account is inactive or disabled."""

    pass


class InactiveClientException(StudioException):
    """Client account is inactive or disabled."""

    pass


class InactiveResourceException(StudioException):
    """Resource is inactive or disabled."""

    pass


# ==================== Resource Not Found Exceptions ====================


class ResourceNotFoundException(StudioException):
    """Base exception for resource not found errors."""

    def __init__(self, resource_type: str, identifier: str | int):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f'{resource_type} with identifier {identifier} not found')


class UserNotFoundException(ResourceNotFoundException):
    """User not found."""

    def __init__(self, identifier: str | int):
        super().__init__('User', identifier)


class ClientNotFoundException(ResourceNotFoundException):
    """Client not found."""

    def __init__(self, client_id: int):
        super().__init__('Client', client_id)


class SessionNotFoundException(ResourceNotFoundException):
    """Session not found."""

    def __init__(self, session_id: int):
        super().__init__('Session', session_id)


class ItemNotFoundException(ResourceNotFoundException):
    """Item not found."""

    def __init__(self, item_id: int):
        super().__init__('Item', item_id)


class PackageNotFoundException(ResourceNotFoundException):
    """Package not found."""

    def __init__(self, package_id: int):
        super().__init__('Package', package_id)


class RoomNotFoundException(ResourceNotFoundException):
    """Room not found."""

    def __init__(self, room_id: int):
        super().__init__('Room', room_id)


class RoleNotFoundException(ResourceNotFoundException):
    """Role not found."""

    def __init__(self, identifier: str | int):
        super().__init__('Role', identifier)


class PermissionNotFoundException(ResourceNotFoundException):
    """Permission not found."""

    def __init__(self, identifier: str | int):
        super().__init__('Permission', identifier)


class PackageItemNotFoundException(ResourceNotFoundException):
    """Package-Item relationship not found."""

    def __init__(self, package_id: int, item_id: int):
        super().__init__('PackageItem', f'package={package_id}, item={item_id}')


# ==================== Conflict/Duplicate Exceptions ====================


class ResourceConflictException(StudioException):
    """Base exception for resource conflicts."""

    def __init__(self, resource_type: str, field: str, value: str | int):
        self.resource_type = resource_type
        self.field = field
        self.value = value
        super().__init__(f'{resource_type} with {field} "{value}" already exists')


class DuplicateEmailException(ResourceConflictException):
    """Email already exists in the system."""

    def __init__(self, email: str, resource_type: str = 'User'):
        super().__init__(resource_type, 'email', email)


class DuplicateCodeException(ResourceConflictException):
    """Code already exists in the system."""

    def __init__(self, code: str, resource_type: str):
        super().__init__(resource_type, 'code', code)


class DuplicateNameException(ResourceConflictException):
    """Name already exists in the system."""

    def __init__(self, name: str, resource_type: str):
        super().__init__(resource_type, 'name', name)


# ==================== Business Logic Validation Exceptions ====================


class BusinessValidationException(StudioException):
    """Base exception for business logic validation failures."""

    pass


class SessionNotEditableException(BusinessValidationException):
    """Session cannot be edited (past changes deadline)."""

    def __init__(self, session_id: int, changes_deadline: str):
        self.session_id = session_id
        self.changes_deadline = changes_deadline
        super().__init__(
            f'Session {session_id} cannot be edited after changes deadline ({changes_deadline})'
        )


class InvalidStatusTransitionException(BusinessValidationException):
    """Invalid session status transition."""

    def __init__(
        self,
        from_status: str,
        to_status: str,
        allowed_statuses: list[str],
        reason: str | None = None,
    ):
        self.from_status = from_status
        self.to_status = to_status
        self.allowed_statuses = allowed_statuses
        self.reason = reason

        # Build message
        message = f'Cannot transition from {from_status} to {to_status}.'

        if reason:
            message += f' Reason: {reason}'
        elif allowed_statuses:
            message += f' Allowed: {", ".join(allowed_statuses)}'

        super().__init__(message)


class InsufficientBalanceException(BusinessValidationException):
    """Payment amount exceeds remaining balance."""

    def __init__(self, session_id: int, balance: float, attempted_amount: float):
        self.session_id = session_id
        self.balance = balance
        self.attempted_amount = attempted_amount
        super().__init__(
            f'Insufficient balance for session {session_id}. '
            f'Balance: {balance}, Attempted: {attempted_amount}'
        )


class PaymentDeadlineExpiredException(BusinessValidationException):
    """Payment deadline has passed."""

    def __init__(self, session_id: int, payment_deadline: str):
        self.session_id = session_id
        self.payment_deadline = payment_deadline
        super().__init__(f'Payment deadline expired for session {session_id}')


class DeadlineExpiredException(BusinessValidationException):
    """Generic deadline has expired."""

    def __init__(self, deadline_type: str, deadline_date: str):
        self.deadline_type = deadline_type
        self.deadline_date = deadline_date
        super().__init__(f'{deadline_type} deadline expired on {deadline_date}')


class RoomNotAvailableException(BusinessValidationException):
    """Room is already booked for the specified date/time."""

    def __init__(self, room_id: int, session_date: str, session_time: str):
        self.room_id = room_id
        self.session_date = session_date
        self.session_time = session_time
        super().__init__(
            f'Room {room_id} is not available on {session_date} at {session_time}'
        )


class PhotographerNotAvailableException(BusinessValidationException):
    """Photographer is already assigned to another session."""

    def __init__(self, photographer_id: int, session_date: str, session_time: str):
        self.photographer_id = photographer_id
        self.session_date = session_date
        self.session_time = session_time
        super().__init__(
            f'Photographer {photographer_id} is not available on {session_date} at {session_time}'
        )


class InvalidSessionTypeException(BusinessValidationException):
    """Invalid session type for the operation."""

    def __init__(self, message: str):
        super().__init__(message)


class PackageItemsEmptyException(BusinessValidationException):
    """Package has no items associated."""

    def __init__(self, package_id: int):
        self.package_id = package_id
        super().__init__(
            f'Package {package_id} has no items and cannot be added to session'
        )


class PhotographerNotAssignedException(BusinessValidationException):
    """Photographer is not assigned to the specified session."""

    def __init__(self, photographer_id: int, session_id: int):
        self.photographer_id = photographer_id
        self.session_id = session_id
        super().__init__(
            f'Photographer {photographer_id} is not assigned to session {session_id}'
        )


class InvalidSessionStateException(BusinessValidationException):
    """Session is not in a valid state for this operation."""

    def __init__(self, message: str):
        super().__init__(message)
