"""
Session routers for session management endpoints.

This module exposes REST endpoints for:
- Sessions: Main session CRUD and state machine transitions
- SessionDetails: Line items (adding items/packages)
- SessionPhotographers: Photographer assignments
- SessionPayments: Payment tracking
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field

from app.core.dependencies import SessionDep
from app.core.enums import SessionStatus
from app.core.permissions import require_permission
from app.core.schemas import PaginatedResponse
from app.sessions.models import (
    Session as SessionModel,
)
from app.sessions.models import (
    SessionDetail,
    SessionPayment,
    SessionPhotographer,
    SessionStatusHistory,
)
from app.sessions.schemas import (
    SessionCancellation,
    SessionCreate,
    SessionDetailPublic,
    SessionEditorAssignment,
    SessionMarkReady,
    SessionPaymentCreate,
    SessionPaymentPublic,
    SessionPhotographerAssign,
    SessionPhotographerPublic,
    SessionPhotographerUpdate,
    SessionPublic,
    SessionStatusHistoryPublic,
    SessionStatusTransition,
    SessionUpdate,
)
from app.sessions.schemas import (
    SessionDetail as SessionDetailSchema,
)
from app.sessions.service import (
    SessionDetailService,
    SessionPaymentService,
    SessionPhotographerService,
    SessionService,
)
from app.users.models import User

# ==================== Sessions Router ====================

sessions_router = APIRouter(prefix='/sessions', tags=['sessions'])


@sessions_router.post(
    '',
    response_model=SessionPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create session',
    description='Create a new session in REQUEST status. Requires session.create permission.',
)
async def create_session(
    data: SessionCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.create'))],
) -> SessionModel:
    """
    Create a new photography session.

    **Required fields:**
    - client_id: Client ID (must exist and be active)
    - session_type: Type (Studio/External)
    - session_date: Date of session (must be in future)

    **Optional fields:**
    - session_time: Time in HH:MM format
    - estimated_duration_hours: Duration (1-24 hours)
    - location: Required for External sessions
    - room_id: Required for Studio sessions
    - client_requirements: Special client requests

    **Business rules:**
    - Session is created in REQUEST status
    - Room availability is validated for Studio sessions
    - Session date must be in the future

    **Permissions required:** session.create
    """
    service = SessionService(db)
    return await service.create_session(data, created_by=current_user.id)  # type: ignore


@sessions_router.get(
    '',
    response_model=PaginatedResponse[SessionPublic],
    status_code=status.HTTP_200_OK,
    summary='List sessions',
    description='Get paginated list of sessions with optional filters. Requires session.view.all permission.',
)
async def list_sessions(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.all'))],
    client_id: Annotated[int | None, Query(description='Filter by client ID')] = None,
    status_filter: Annotated[
        SessionStatus | None,
        Query(description='Filter by session status', alias='status'),
    ] = None,
    start_date: Annotated[
        date | None, Query(description='Filter by start date (inclusive)')
    ] = None,
    end_date: Annotated[
        date | None, Query(description='Filter by end date (inclusive)')
    ] = None,
    photographer_id: Annotated[
        int | None, Query(description='Filter by assigned photographer')
    ] = None,
    editor_id: Annotated[
        int | None, Query(description='Filter by assigned editor')
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[SessionPublic]:
    """
    List sessions with pagination and optional filters.

    **Query parameters:**
    - client_id: Filter by client
    - status: Filter by session status
    - start_date: Filter from this date (inclusive)
    - end_date: Filter until this date (inclusive)
    - photographer_id: Filter by assigned photographer
    - editor_id: Filter by assigned editor
    - limit: Maximum results (1-100, default: 50)
    - offset: Skip results for pagination (default: 0)

    **Response:**
    - items: List of sessions for the current page
    - total: Total number of sessions matching filters
    - limit: Maximum items per page
    - offset: Number of items skipped
    - has_more: Whether there are more sessions beyond this page

    **Permissions required:** session.view.all
    """
    service = SessionService(db)
    sessions = await service.list_sessions(
        client_id=client_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        photographer_id=photographer_id,
        editor_id=editor_id,
        limit=limit,
        offset=offset,
    )
    total = await service.count_sessions(
        client_id=client_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        photographer_id=photographer_id,
        editor_id=editor_id,
    )

    return PaginatedResponse(
        items=sessions,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(sessions)) < total,
    )


@sessions_router.get(
    '/my-assignments',
    response_model=PaginatedResponse[SessionPublic],
    status_code=status.HTTP_200_OK,
    summary='List my assigned sessions (Photographer)',
    description='Get sessions assigned to current photographer. Requires session.view.own permission.',
)
async def list_my_assignments(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.own'))],
    status_filter: Annotated[
        SessionStatus | None,
        Query(description='Filter by session status', alias='status'),
    ] = None,
    start_date: Annotated[
        date | None, Query(description='Filter by start date (inclusive)')
    ] = None,
    end_date: Annotated[
        date | None, Query(description='Filter by end date (inclusive)')
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[SessionPublic]:
    """
    List sessions assigned to the current photographer.

    **Query parameters:**
    - status: Filter by session status (optional)
    - start_date: Filter from this date (inclusive, optional)
    - end_date: Filter until this date (inclusive, optional)
    - limit: Maximum results (1-100, default: 50)
    - offset: Skip results for pagination (default: 0)

    **Response:**
    - items: List of sessions for the current page
    - total: Total number of sessions matching filters
    - limit: Maximum items per page
    - offset: Number of items skipped
    - has_more: Whether there are more sessions beyond this page

    **Permissions required:** session.view.own
    """
    service = SessionService(db)
    sessions = await service.list_my_photographer_assignments(
        photographer_id=current_user.id,  # type: ignore
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    total = await service.count_sessions(
        photographer_id=current_user.id,  # type: ignore
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
    )

    return PaginatedResponse(
        items=sessions,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(sessions)) < total,
    )


@sessions_router.get(
    '/my-editing',
    response_model=PaginatedResponse[SessionPublic],
    status_code=status.HTTP_200_OK,
    summary='List my editing assignments (Editor)',
    description='Get sessions assigned to current editor. Requires session.view.own permission.',
)
async def list_my_editing(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.own'))],
    status_filter: Annotated[
        SessionStatus | None,
        Query(description='Filter by session status', alias='status'),
    ] = None,
    start_date: Annotated[
        date | None, Query(description='Filter by start date (inclusive)')
    ] = None,
    end_date: Annotated[
        date | None, Query(description='Filter by end date (inclusive)')
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[SessionPublic]:
    """
    List sessions assigned to the current editor.

    **Query parameters:**
    - status: Filter by session status (optional, default: IN_EDITING)
    - start_date: Filter from this date (inclusive, optional)
    - end_date: Filter until this date (inclusive, optional)
    - limit: Maximum results (1-100, default: 50)
    - offset: Skip results for pagination (default: 0)

    **Response:**
    - items: List of sessions for the current page
    - total: Total number of sessions matching filters
    - limit: Maximum items per page
    - offset: Number of items skipped
    - has_more: Whether there are more sessions beyond this page

    **Permissions required:** session.view.own
    """
    service = SessionService(db)
    sessions = await service.list_my_editor_assignments(
        editor_id=current_user.id,  # type: ignore
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    total = await service.count_sessions(
        editor_id=current_user.id,  # type: ignore
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
    )

    return PaginatedResponse(
        items=sessions,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(sessions)) < total,
    )


@sessions_router.get(
    '/{session_id}',
    response_model=SessionDetailSchema,
    status_code=status.HTTP_200_OK,
    summary='Get session by ID',
    description='Get detailed session information by ID. Requires session.view.all permission.',
)
async def get_session(
    session_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.all'))],
) -> SessionModel:
    """
    Get session by ID with detailed information.

    **Path parameters:**
    - session_id: Session ID to retrieve

    **Permissions required:** session.view
    """
    service = SessionService(db)
    return await service.get_session(session_id)


@sessions_router.patch(
    '/{session_id}',
    response_model=SessionPublic,
    status_code=status.HTTP_200_OK,
    summary='Update session',
    description='Update session information. Requires session.edit.pre-assigned permission.',
)
async def update_session(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionUpdate,
    db: SessionDep,
    current_user: Annotated[
        User, Depends(require_permission('session.edit.pre-assigned'))
    ],
) -> SessionModel:
    """
    Update session information.

    **Path parameters:**
    - session_id: Session ID to update

    **Optional fields (all):**
    - session_date: Updated date (must be in future)
    - session_time: Updated time (HH:MM format)
    - estimated_duration_hours: Updated duration
    - location: Updated location
    - room_id: Updated room
    - client_requirements: Updated requirements
    - internal_notes: Staff notes
    - delivery_method: Delivery method
    - delivery_address: Delivery address

    **Business rules:**
    - Cannot edit after changes deadline (7 days before session)
    - Room availability is validated if changing room/datetime

    **Permissions required:** session.edit.pre-assigned
    """
    service = SessionService(db)
    return await service.update_session(session_id, data, updated_by=current_user.id)  # type: ignore


# ==================== State Machine Transitions ====================


@sessions_router.post(
    '/{session_id}/transition',
    response_model=SessionPublic,
    status_code=status.HTTP_200_OK,
    summary='Transition session status',
    description='Transition session to a new status. Requires session.transition permission.',
)
async def transition_status(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionStatusTransition,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.edit.all'))],
) -> SessionModel:
    """
    Transition session to a new status.

    **Path parameters:**
    - session_id: Session ID

    **Request body:**
    - to_status: Target status (must be valid transition)
    - reason: Reason for transition (optional)
    - notes: Additional notes (optional)

    **Valid transitions (see business_rules_doc.md):**
    - REQUEST → NEGOTIATION, PRE_SCHEDULED, CANCELED
    - NEGOTIATION → PRE_SCHEDULED, CANCELED
    - PRE_SCHEDULED → CONFIRMED, CANCELED
    - CONFIRMED → ASSIGNED, CANCELED
    - ASSIGNED → ATTENDED, CANCELED
    - ATTENDED → IN_EDITING, CANCELED
    - IN_EDITING → READY_FOR_DELIVERY, CANCELED
    - READY_FOR_DELIVERY → COMPLETED, CANCELED

    **Business rules applied automatically:**
    - PRE_SCHEDULED: Calculates payment deadline (5 days) and changes deadline (7 days before session)
    - CONFIRMED: Validates deposit payment
    - IN_EDITING: Records editing start time, calculates delivery deadline
    - READY_FOR_DELIVERY: Records editing completion time
    - COMPLETED: Validates full payment, records delivery time

    **Permissions required:** session.transition
    """
    service = SessionService(db)
    return await service.transition_status(
        session_id,
        SessionStatus(data.to_status),
        changed_by=current_user.id,  # type: ignore
        reason=data.reason,
        notes=data.notes,
    )


@sessions_router.post(
    '/{session_id}/cancel',
    response_model=SessionDetailSchema,
    status_code=status.HTTP_200_OK,
    summary='Cancel session',
    description='Cancel session with refund calculation. Requires session.cancel permission.',
)
async def cancel_session(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionCancellation,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.cancel'))],
) -> SessionModel:
    """
    Cancel a session with automatic refund calculation.

    **Path parameters:**
    - session_id: Session ID to cancel

    **Request body:**
    - cancellation_reason: Reason for cancellation (required)
    - initiated_by: Who initiated (Client/Studio) - affects refund
    - notes: Additional notes (optional)

    **Refund matrix (see business_rules_doc.md):**
    - Before Pre-scheduled: 100% refund
    - Pre-scheduled/Confirmed: 50% if Client initiated, 100% if Studio initiated
    - After Confirmed: No refund if Client initiated, 100% if Studio initiated

    **Permissions required:** session.cancel
    """
    service = SessionService(db)
    return await service.cancel_session(
        session_id,
        data,
        cancelled_by=current_user.id,  # type: ignore
    )


@sessions_router.post(
    '/{session_id}/mark-ready',
    response_model=SessionPublic,
    status_code=status.HTTP_200_OK,
    summary='Mark session ready for delivery (Editor)',
    description='Mark session as ready for delivery (editor completed editing). Requires session.mark-ready permission.',
)
async def mark_session_ready(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionMarkReady,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.mark-ready'))],
) -> SessionModel:
    """
    Mark a session as ready for delivery (editor completed editing).

    **Important:** This automatically transitions the session from IN_EDITING to READY_FOR_DELIVERY status.

    **Path parameters:**
    - session_id: Session ID to mark as ready

    **Request body:**
    - notes: Additional notes (optional)

    **Business logic:**
    - Session must be in IN_EDITING status
    - Automatically transitions to READY_FOR_DELIVERY
    - Records editing_completed_at timestamp
    - Records status change in history

    **Permissions required:** session.mark-ready

    **Use case:**
    - Editor finishes editing photos/videos for a session
    - Marks session as ready so coordinator can deliver to client
    """
    service = SessionService(db)
    return await service.mark_ready_for_delivery(
        session_id=session_id,
        marked_by=current_user.id,  # type: ignore
        notes=data.notes,
    )


@sessions_router.post(
    '/{session_id}/assign-editor',
    response_model=SessionPublic,
    status_code=status.HTTP_200_OK,
    summary='Assign editor to session',
    description='Assign an editor to a session for editing phase. Requires session.assign-resources permission.',
)
async def assign_editor_to_session(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionEditorAssignment,
    db: SessionDep,
    current_user: Annotated[
        User, Depends(require_permission('session.assign-resources'))
    ],
) -> SessionModel:
    """
    Assign an editor to a session for the editing phase.

    **Path parameters:**
    - session_id: Session ID to assign editor to

    **Request body:**
    - editor_id: User ID of the editor to assign

    **Business logic:**
    - Typically done when session is in ATTENDED status
    - Editor will be responsible for editing photos/videos
    - Session should be transitioned to IN_EDITING after assignment

    **Permissions required:** session.assign-resources

    **Use case:**
    1. Session has been attended by photographer
    2. Coordinator assigns an editor for post-processing
    3. Editor can now see session in their /sessions/my-editing list
    4. Coordinator transitions session to IN_EDITING status

    **Workflow:**
    - POST /sessions/{id}/assign-editor (this endpoint)
    - POST /sessions/{id}/transition with to_status=IN_EDITING
    - Editor works on editing
    - POST /sessions/{id}/mark-ready when complete
    """
    service = SessionService(db)
    return await service.assign_editor(
        session_id=session_id,
        editor_id=data.editor_id,
        assigned_by=current_user.id,  # type: ignore
    )


# ==================== Session Details (Line Items) Router ====================


@sessions_router.post(
    '/{session_id}/details/items/{item_id}',
    response_model=SessionDetailPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Add item to session',
    description='Add an individual item to session. Requires session.edit permission.',
)
async def add_item_to_session(
    session_id: Annotated[int, Field(gt=0)],
    item_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.edit.all'))],
    quantity: Annotated[int, Query(ge=1, description='Quantity of item')] = 1,
) -> SessionDetail:
    """
    Add an individual catalog item to a session.

    **Path parameters:**
    - session_id: Session ID
    - item_id: Item ID to add

    **Query parameters:**
    - quantity: Quantity of item (default: 1)

    **Business rules:**
    - Session must be editable (before changes deadline)
    - Item must be active
    - Item price is denormalized (captured at time of addition)

    **Permissions required:** session.edit
    """
    service = SessionDetailService(db)
    detail = await service.add_item_to_session(
        session_id,
        item_id,
        quantity,
        created_by=current_user.id,  # type: ignore
    )

    # Recalculate session totals
    session_service = SessionService(db)
    await session_service.recalculate_totals(session_id)

    return detail


@sessions_router.post(
    '/{session_id}/details/packages/{package_id}',
    response_model=list[SessionDetailPublic],
    status_code=status.HTTP_201_CREATED,
    summary='Add package to session',
    description='Add a package to session (package explosion). Requires session.edit.all permission.',
)
async def add_package_to_session(
    session_id: Annotated[int, Field(gt=0)],
    package_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.edit.all'))],
) -> list[SessionDetail]:
    """
    Add a package to a session (PACKAGE EXPLOSION pattern).

    **Path parameters:**
    - session_id: Session ID
    - package_id: Package ID to add

    **Business rules:**
    - Session must be editable (before changes deadline)
    - Package must be active and have items
    - Package session_type must match session type
    - Each item in package is denormalized into a separate SessionDetail record
    - This ensures historical immutability (changing package doesn't affect past sessions)

    **Permissions required:** session.edit.all
    """
    service = SessionDetailService(db)
    details = await service.add_package_to_session(
        session_id,
        package_id,
        created_by=current_user.id,  # type: ignore
    )

    # Recalculate session totals
    session_service = SessionService(db)
    await session_service.recalculate_totals(session_id)

    return details


@sessions_router.get(
    '/{session_id}/details',
    response_model=list[SessionDetailPublic],
    status_code=status.HTTP_200_OK,
    summary='List session details',
    description='Get all line items for a session. Requires session.view permission.',
)
async def list_session_details(
    session_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.all'))],
) -> list[SessionDetail]:
    """
    List all line items (details) for a session.

    **Path parameters:**
    - session_id: Session ID

    **Permissions required:** session.view
    """
    service = SessionDetailService(db)
    return await service.list_session_details(session_id)


@sessions_router.delete(
    '/{session_id}/details/{detail_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remove session detail',
    description='Remove a line item from session. Requires session.edit permission.',
)
async def remove_session_detail(
    session_id: Annotated[int, Field(gt=0)],
    detail_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.edit'))],
) -> None:
    """
    Remove a line item from a session.

    **Path parameters:**
    - session_id: Session ID
    - detail_id: Detail ID to remove

    **Business rules:**
    - Session must be editable (before changes deadline)

    **Permissions required:** session.edit
    """
    service = SessionDetailService(db)
    await service.remove_detail(detail_id, removed_by=current_user.id)  # type: ignore

    # Recalculate session totals
    session_service = SessionService(db)
    await session_service.recalculate_totals(session_id)


@sessions_router.post(
    '/{session_id}/recalculate',
    response_model=SessionPublic,
    status_code=status.HTTP_200_OK,
    summary='Recalculate session totals',
    description='Recalculate all financial totals from details. Requires session.edit permission.',
)
async def recalculate_session_totals(
    session_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.edit.all'))],
) -> SessionModel:
    """
    Recalculate all financial totals for a session.

    **Path parameters:**
    - session_id: Session ID

    **Recalculates:**
    - total_amount: Sum of all detail line_subtotals
    - deposit_amount: total * deposit_percentage (default 50%) - informational only
    - balance_amount: total - paid_amount (remaining balance to be paid)
    - paid_amount: Sum of all payments minus refunds

    **Note:** balance_amount always represents the remaining amount the client owes,
    regardless of whether they've paid the deposit or not.

    **Permissions required:** session.edit.all
    """
    service = SessionService(db)
    return await service.recalculate_totals(session_id)


# ==================== Session Payments Router ====================


@sessions_router.post(
    '/{session_id}/payments',
    response_model=SessionPaymentPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Record payment',
    description='Record a payment for a session. Requires session.payment permission.',
)
async def record_payment(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionPaymentCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.payment'))],
) -> SessionPayment:
    """
    Record a payment for a session.

    **Path parameters:**
    - session_id: Session ID

    **Request body:**
    - payment_type: Type (Deposit/Balance/Partial/Refund)
    - payment_method: Method (Cash/Card/Transfer/etc.)
    - amount: Payment amount (must be positive)
    - transaction_reference: Transaction reference (optional)
    - payment_date: Date of payment (cannot be in future)
    - notes: Additional notes (optional)

    **Business rules:**
    - Payment amount cannot exceed remaining balance (total_amount - paid_amount)
    - Session paid_amount is updated automatically
    - Session balance_amount is recalculated as: total_amount - paid_amount

    **Auto-updates:**
    - paid_amount: Increases by payment amount
    - balance_amount: Recalculated to reflect remaining balance

    **Permissions required:** session.payment
    """
    service = SessionPaymentService(db)
    return await service.record_payment(data, created_by=current_user.id)  # type: ignore


# TODO: Check permission later, session.view**
@sessions_router.get(
    '/{session_id}/payments',
    response_model=list[SessionPaymentPublic],
    status_code=status.HTTP_200_OK,
    summary='List session payments',
    description='Get all payments for a session. Requires session.view.all permission.',
)
async def list_session_payments(
    session_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.all'))],
) -> list[SessionPayment]:
    """
    List all payments for a session.

    **Path parameters:**
    - session_id: Session ID

    **Permissions required:** session.view.all
    """
    service = SessionPaymentService(db)
    return await service.list_session_payments(session_id)


# ==================== Session Photographers Router ====================


@sessions_router.post(
    '/{session_id}/photographers',
    response_model=SessionPhotographerPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Assign photographer',
    description='Assign a photographer to a session. Requires session.assign-resources permission.',
)
async def assign_photographer(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionPhotographerAssign,
    db: SessionDep,
    current_user: Annotated[
        User, Depends(require_permission('session.assign-resources'))
    ],
) -> SessionPhotographer:
    """
    Assign a photographer to a session.

    **Important:** This automatically transitions the session from CONFIRMED to ASSIGNED status.

    **Path parameters:**
    - session_id: Session ID

    **Request body:**
    - photographer_id: User ID of photographer
    - role: Role (Lead/Assistant) - optional

    **Business logic:**
    - Creates photographer assignment
    - If session is in CONFIRMED status, automatically transitions to ASSIGNED
    - Records status change in history

    **Business rules:**
    - Photographer availability is validated (not double-booked)

    **Permissions required:** session.assign-resources
    """
    service = SessionPhotographerService(db)
    return await service.assign_photographer(data, assigned_by=current_user.id)  # type: ignore


@sessions_router.get(
    '/{session_id}/photographers',
    response_model=list[SessionPhotographerPublic],
    status_code=status.HTTP_200_OK,
    summary='List session photographers',
    description='Get all photographer assignments for a session. Requires session.view permission.',
)
async def list_session_photographers(
    session_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.all'))],
) -> list[SessionPhotographer]:
    """
    List all photographer assignments for a session.

    **Path parameters:**
    - session_id: Session ID

    **Permissions required:** session.view.all
    """
    service = SessionPhotographerService(db)
    return await service.list_session_photographers(session_id)


@sessions_router.patch(
    '/{session_id}/photographers/{assignment_id}/attended',
    response_model=SessionPhotographerPublic,
    status_code=status.HTTP_200_OK,
    summary='Mark photographer attended',
    description='Mark photographer as attended and auto-transition session to ATTENDED. Requires session.mark-attended permission.',
)
async def mark_photographer_attended(
    session_id: Annotated[int, Field(gt=0)],
    assignment_id: Annotated[int, Field(gt=0)],
    data: SessionPhotographerUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.mark-attended'))],
) -> SessionPhotographer:
    """
    Mark a photographer assignment as attended.

    **Important:** This automatically transitions the session from ASSIGNED to ATTENDED status.

    **Path parameters:**
    - session_id: Session ID
    - assignment_id: Assignment ID

    **Request body:**
    - attended: True to mark as attended
    - notes: Session notes (optional)

    **Business logic:**
    - Marks the photographer as attended
    - If session is in ASSIGNED status, automatically transitions to ATTENDED
    - Records status change in history

    **Permissions required:** session.mark-attended
    """
    service = SessionPhotographerService(db)
    return await service.mark_attended(
        assignment_id,
        marked_by=current_user.id,  # type: ignore
        notes=data.notes,  # type: ignore
    )


@sessions_router.patch(
    '/{session_id}/my-attendance',
    response_model=SessionPhotographerPublic,
    status_code=status.HTTP_200_OK,
    summary='Mark my attendance (Photographer - Simplified)',
    description='Mark attendance for current photographer without needing assignment_id. Requires session.mark-attended permission.',
)
async def mark_my_attendance(
    session_id: Annotated[int, Field(gt=0)],
    data: SessionPhotographerUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.mark-attended'))],
) -> SessionPhotographer:
    """
    Mark attendance for the current photographer (simplified endpoint).

    **Simplified endpoint for photographers** - only requires session_id.
    The backend automatically finds the photographer's assignment using the authenticated user.

    **Important:** This automatically transitions the session from ASSIGNED to ATTENDED status.

    **Path parameters:**
    - session_id: Session ID

    **Request body:**
    - attended: True to mark as attended
    - notes: Session notes (optional)

    **Business logic:**
    - Finds photographer assignment for current user
    - Marks the photographer as attended
    - If session is in ASSIGNED status, automatically transitions to ATTENDED
    - Records status change in history

    **Permissions required:** session.mark-attended

    **Use case:**
    - Photographer completes a photography session
    - Frontend only needs session_id (from /sessions/my-assignments list)
    - Photographer marks attendance with a single call

    **Error cases:**
    - 404: Photographer is not assigned to this session
    - 404: Session not found
    """
    service = SessionPhotographerService(db)
    return await service.mark_my_attendance(
        session_id=session_id,
        photographer_id=current_user.id,  # type: ignore
        marked_by=current_user.id,  # type: ignore
        notes=data.notes,
    )


@sessions_router.delete(
    '/{session_id}/photographers/{assignment_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remove photographer assignment',
    description='Remove a photographer from a session. Requires session.assign-resources permission.',
)
async def remove_photographer_assignment(
    session_id: Annotated[int, Field(gt=0)],
    assignment_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[
        User, Depends(require_permission('session.assign-resources'))
    ],
) -> None:
    """
    Remove a photographer assignment from a session.

    **Path parameters:**
    - session_id: Session ID
    - assignment_id: Assignment ID to remove

    **Permissions required:** session.assign-resources
    """
    service = SessionPhotographerService(db)
    await service.remove_assignment(assignment_id)


# ==================== Session Status History Router ====================


@sessions_router.get(
    '/{session_id}/history',
    response_model=list[SessionStatusHistoryPublic],
    status_code=status.HTTP_200_OK,
    summary='Get session status history',
    description='Get status change history for a session. Requires session.view.all permission.',
)
async def get_session_status_history(
    session_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.all'))],
) -> list[SessionStatusHistory]:
    """
    Get status change history for a session.

    **Path parameters:**
    - session_id: Session ID

    **Returns:**
    - Ordered list of all status changes with timestamps and reasons

    **Permissions required:** session.view.all
    """
    service = SessionService(db)
    await service.get_session(session_id)  # Validate session exists

    from app.sessions.repository import SessionStatusHistoryRepository

    history_repo = SessionStatusHistoryRepository(db)
    return await history_repo.list_by_session(session_id)


# ==================== Main Router for Export ====================

router = APIRouter()
router.include_router(sessions_router)
