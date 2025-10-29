"""
Exception handlers for the Photography Studio API.

This module provides centralized exception handling with consistent error responses
following FastAPI best practices.
"""

import logging
from typing import Any, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .config import settings
from .exceptions import (
    BusinessValidationException,
    DeadlineExpiredException,
    DuplicateCodeException,
    DuplicateEmailException,
    DuplicateNameException,
    InactiveClientException,
    InactiveResourceException,
    InactiveUserException,
    InsufficientBalanceException,
    InsufficientPermissionsException,
    InvalidCredentialsException,
    InvalidPasswordFormatException,
    InvalidSessionTypeException,
    InvalidStatusTransitionException,
    InvalidTokenException,
    PackageItemsEmptyException,
    PaymentDeadlineExpiredException,
    PhotographerNotAvailableException,
    ResourceConflictException,
    ResourceNotFoundException,
    RoomNotAvailableException,
    SessionNotAccessibleToPhotographerException,
    SessionNotEditableException,
    StudioException,
    TokenExpiredException,
    UnauthorizedException,
)

# Configure logger for this module
logger = logging.getLogger(__name__)


def create_exception_handler(
    status_code: int, error_code: str, message: str
) -> Callable[[Request, Exception], Any]:
    """
    Factory function to create exception handlers with consistent response format.

    Args:
        status_code: HTTP status code to return
        error_code: Machine-readable error code for frontend
        message: Human-readable error message

    Returns:
        Async exception handler function
    """

    async def exception_handler(request: Request, exc: Exception):
        # Extract additional details from exception if available
        detail = {}
        if hasattr(exc, '__dict__'):
            detail = {
                k: v
                for k, v in exc.__dict__.items()
                if not k.startswith('_') and k not in ['args', 'with_traceback']
            }

        return JSONResponse(
            status_code=status_code,
            content={'message': message, 'error_code': error_code, 'detail': detail},
        )

    return exception_handler


def register_all_errors(app: FastAPI) -> None:
    """
    Register all custom exception handlers with the FastAPI application.

    This function should be called during application startup to ensure
    all custom exceptions are properly handled.

    Args:
        app: FastAPI application instance
    """

    # ==================== Authentication & Authorization ====================

    app.add_exception_handler(
        InvalidPasswordFormatException,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code='invalid_password_format',
            message='Password does not meet complexity requirements',
        ),
    )

    app.add_exception_handler(
        UnauthorizedException,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code='unauthorized',
            message='Authentication required',
        ),
    )

    app.add_exception_handler(
        InvalidCredentialsException,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code='invalid_credentials',
            message='Invalid email or password',
        ),
    )

    app.add_exception_handler(
        TokenExpiredException,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code='token_expired',
            message='Token has expired, please login again',
        ),
    )

    app.add_exception_handler(
        InvalidTokenException,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code='invalid_token',
            message='Invalid or malformed token',
        ),
    )

    app.add_exception_handler(
        InsufficientPermissionsException,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code='insufficient_permissions',
            message='You do not have permission to perform this action',
        ),
    )

    app.add_exception_handler(
        InactiveUserException,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code='inactive_user',
            message='User account is inactive',
        ),
    )

    app.add_exception_handler(
        InactiveClientException,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code='inactive_client',
            message='Client account is inactive',
        ),
    )

    app.add_exception_handler(
        InactiveResourceException,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code='inactive_resource',
            message='Resource is inactive or unavailable',
        ),
    )

    # ==================== Resource Not Found ====================

    @app.exception_handler(ResourceNotFoundException)
    async def resource_not_found_handler(
        request: Request, exc: ResourceNotFoundException
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'message': str(exc),
                'error_code': 'resource_not_found',
                'detail': {
                    'resource_type': exc.resource_type,
                    'identifier': exc.identifier,
                },
            },
        )

    # ==================== Conflicts/Duplicates ====================

    @app.exception_handler(DuplicateEmailException)
    async def duplicate_email_handler(request: Request, exc: DuplicateEmailException):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': str(exc),
                'error_code': 'duplicate_email',
                'detail': {
                    'resource_type': exc.resource_type,
                    'field': exc.field,
                    'value': exc.value,
                },
            },
        )

    @app.exception_handler(DuplicateCodeException)
    async def duplicate_code_handler(request: Request, exc: DuplicateCodeException):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': str(exc),
                'error_code': 'duplicate_code',
                'detail': {
                    'resource_type': exc.resource_type,
                    'field': exc.field,
                    'value': exc.value,
                },
            },
        )

    @app.exception_handler(DuplicateNameException)
    async def duplicate_name_handler(request: Request, exc: DuplicateNameException):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': str(exc),
                'error_code': 'duplicate_name',
                'detail': {
                    'resource_type': exc.resource_type,
                    'field': exc.field,
                    'value': exc.value,
                },
            },
        )

    @app.exception_handler(ResourceConflictException)
    async def resource_conflict_handler(
        request: Request, exc: ResourceConflictException
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': str(exc),
                'error_code': 'resource_conflict',
                'detail': {
                    'resource_type': exc.resource_type,
                    'field': exc.field,
                    'value': exc.value,
                },
            },
        )

    # ==================== Business Logic Validation ====================

    @app.exception_handler(SessionNotEditableException)
    async def session_not_editable_handler(
        request: Request, exc: SessionNotEditableException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'session_not_editable',
                'detail': {
                    'session_id': exc.session_id,
                    'changes_deadline': exc.changes_deadline,
                },
            },
        )

    @app.exception_handler(InvalidStatusTransitionException)
    async def invalid_status_transition_handler(
        request: Request, exc: InvalidStatusTransitionException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'invalid_status_transition',
                'detail': {
                    'from_status': exc.from_status,
                    'to_status': exc.to_status,
                    'allowed_statuses': exc.allowed_statuses,
                },
            },
        )

    @app.exception_handler(InsufficientBalanceException)
    async def insufficient_balance_handler(
        request: Request, exc: InsufficientBalanceException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'insufficient_balance',
                'detail': {
                    'session_id': exc.session_id,
                    'balance': exc.balance,
                    'attempted_amount': exc.attempted_amount,
                },
            },
        )

    @app.exception_handler(PaymentDeadlineExpiredException)
    async def payment_deadline_expired_handler(
        request: Request, exc: PaymentDeadlineExpiredException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'payment_deadline_expired',
                'detail': {
                    'session_id': exc.session_id,
                    'payment_deadline': exc.payment_deadline,
                },
            },
        )

    @app.exception_handler(DeadlineExpiredException)
    async def deadline_expired_handler(request: Request, exc: DeadlineExpiredException):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'deadline_expired',
                'detail': {
                    'deadline_type': exc.deadline_type,
                    'deadline_date': exc.deadline_date,
                },
            },
        )

    @app.exception_handler(RoomNotAvailableException)
    async def room_not_available_handler(
        request: Request, exc: RoomNotAvailableException
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': str(exc),
                'error_code': 'room_not_available',
                'detail': {
                    'room_id': exc.room_id,
                    'session_date': exc.session_date,
                    'session_time': exc.session_time,
                },
            },
        )

    @app.exception_handler(PhotographerNotAvailableException)
    async def photographer_not_available_handler(
        request: Request, exc: PhotographerNotAvailableException
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'message': str(exc),
                'error_code': 'photographer_not_available',
                'detail': {
                    'photographer_id': exc.photographer_id,
                    'session_date': exc.session_date,
                    'session_time': exc.session_time,
                },
            },
        )

    @app.exception_handler(InvalidSessionTypeException)
    async def invalid_session_type_handler(
        request: Request, exc: InvalidSessionTypeException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'invalid_session_type',
                'detail': {},
            },
        )

    @app.exception_handler(PackageItemsEmptyException)
    async def package_items_empty_handler(
        request: Request, exc: PackageItemsEmptyException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'package_items_empty',
                'detail': {'package_id': exc.package_id},
            },
        )

    @app.exception_handler(BusinessValidationException)
    async def business_validation_handler(
        request: Request, exc: BusinessValidationException
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': str(exc),
                'error_code': 'business_validation_error',
                'detail': {},
            },
        )

    @app.exception_handler(SessionNotAccessibleToPhotographerException)
    async def session_not_accessible_to_photographer_handler(
        request: Request, exc: SessionNotAccessibleToPhotographerException
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                'message': str(exc),
                'error_code': 'session_not_accessible',
                'detail': {
                    'session_id': exc.session_id,
                    'current_status': exc.current_status,
                },
            },
        )

    # ==================== Generic Studio Exception ====================

    @app.exception_handler(StudioException)
    async def studio_exception_handler(request: Request, exc: StudioException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'message': 'An unexpected error occurred',
                'error_code': 'internal_error',
                'detail': {'original_message': str(exc)},
            },
        )

    # ==================== Database Errors ====================

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError):
        # Use proper logging with levels
        logger.error(
            'Database error occurred',
            extra={
                'error': str(exc),
                'type': type(exc).__name__,
                'path': request.url.path,
                'method': request.method,
            },
            exc_info=settings.DEBUG,  # Stack trace only in debug mode
        )

        # Don't expose database details in production
        detail = {}
        if settings.DEBUG:
            detail = {'error_type': type(exc).__name__, 'error_message': str(exc)}

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'message': 'A database error occurred',
                'error_code': 'database_error',
                'detail': detail,
            },
        )

    # ==================== Validation Errors ====================

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        # Process errors to extract only JSON-serializable values
        errors = []
        for error in exc.errors():
            # Create a clean error dict without non-serializable objects
            clean_error = {
                'type': error.get('type'),
                'loc': error.get('loc'),
                'msg': error.get('msg'),
                'input': error.get('input'),
            }

            # Extract context if present, but convert non-serializable values
            if 'ctx' in error:
                ctx = error['ctx']
                clean_ctx = {}
                for key, value in ctx.items():
                    # Convert exception objects to their string representation
                    if isinstance(value, Exception):
                        clean_ctx[key] = str(value)
                    else:
                        clean_ctx[key] = value
                clean_error['ctx'] = clean_ctx

            errors.append(clean_error)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'message': 'Request validation failed',
                'error_code': 'validation_error',
                'detail': {'errors': errors},
            },
        )
