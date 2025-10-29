"""
Photographer router for photographer-specific endpoints.

This module exposes REST endpoints for photographers to:
- View their assigned sessions
- Access session details relevant to their work
- Mark sessions as attended
- View client contact information
- See team assignments
- Get personal statistics

All endpoints enforce ownership validation - photographers can only
access sessions assigned to them.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.dependencies import SessionDep
from app.core.enums import SessionStatus
from app.core.permissions import require_permission
from app.photographers.schemas import (
    ClientBasicInfo,
    MarkAttendedRequest,
    PhotographerStats,
    SessionPhotographerListItem,
    SessionPhotographerView,
    SessionTeamInfo,
)
from app.photographers.service import PhotographerService
from app.users.models import User

# ==================== Photographers Router ====================

photographers_router = APIRouter(prefix='/photographers', tags=['photographers'])


@photographers_router.get(
    '/sessions',
    response_model=list[SessionPhotographerListItem],
    status_code=status.HTTP_200_OK,
    summary='List my assigned sessions',
    description='Get list of sessions assigned to the current photographer. Requires session.view.own permission.',
)
async def list_my_sessions(
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
) -> list[SessionPhotographerListItem]:
    """
    Get list of sessions assigned to the current photographer.

    **Query parameters:**
    - status: Filter by session status (e.g., ASSIGNED, ATTENDED)
    - start_date: Filter from this date (inclusive)
    - end_date: Filter until this date (inclusive)
    - limit: Maximum results (1-100, default: 50)
    - offset: Skip results for pagination (default: 0)

    **Response:**
    Returns compact session information including:
    - Session ID, date, time, location
    - Client name
    - Your role and attendance status
    - Session status

    **Permissions required:** session.view.own
    """
    service = PhotographerService(db)
    return await service.get_my_assignments(
        photographer_id=current_user.id,  # type: ignore
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@photographers_router.get(
    '/sessions/{session_id}',
    response_model=SessionPhotographerView,
    status_code=status.HTTP_200_OK,
    summary='Get session details',
    description='Get detailed information about an assigned session. Requires session.view.own permission.',
)
async def get_session_detail(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.own'))],
    session_id: Annotated[int, Path(description='Session ID', ge=1)],
) -> SessionPhotographerView:
    """
    Get detailed information about a session assigned to you.

    **Returns:**
    - Complete session information (date, time, location, type)
    - Limited client information (name, email, primary phone)
    - Session requirements and special requests
    - List of items/packages included (without prices)
    - Your assignment details (role, attended status, notes)
    - Delivery information for context

    **Access control:**
    You can only view sessions where you are assigned as a photographer.
    Attempting to access unassigned sessions will result in 403 Forbidden.

    **Permissions required:** session.view.own

    **Errors:**
    - 404: Session not found
    - 403: Not assigned to this session
    """
    service = PhotographerService(db)
    return await service.get_session_detail(
        session_id=session_id,
        photographer_id=current_user.id,  # type: ignore
    )


@photographers_router.get(
    '/sessions/{session_id}/client',
    response_model=ClientBasicInfo,
    status_code=status.HTTP_200_OK,
    summary='Get client contact information',
    description='Get basic client information for coordination. Requires session.view.own permission.',
)
async def get_client_info(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.own'))],
    session_id: Annotated[int, Path(description='Session ID', ge=1)],
) -> ClientBasicInfo:
    """
    Get basic client contact information for a session.

    **Returns:**
    Limited client data for coordination purposes:
    - Full name
    - Email
    - Primary phone

    **Privacy notice:**
    Per permissions policy, photographers do NOT have access to:
    - Secondary phone
    - Delivery address
    - Internal notes
    - Client type

    **Access control:**
    You can only view client info for sessions where you are assigned as a photographer.

    **Permissions required:** session.view.own

    **Errors:**
    - 404: Session not found
    - 403: Not assigned to this session
    """
    service = PhotographerService(db)
    return await service.get_client_info(
        session_id=session_id,
        photographer_id=current_user.id,  # type: ignore
    )


@photographers_router.patch(
    '/sessions/{session_id}/attend',
    response_model=SessionPhotographerView,
    status_code=status.HTTP_200_OK,
    summary='Mark session as attended',
    description='Mark a session as attended (or unattended). Requires session.mark-attended permission.',
)
async def mark_session_attended(
    db: SessionDep,
    current_user: Annotated[
        User, Depends(require_permission('session.mark-attended'))
    ],
    session_id: Annotated[int, Path(description='Session ID', ge=1)],
    data: MarkAttendedRequest,
) -> SessionPhotographerView:
    """
    Mark a session as attended (or unattended) by you.

    **Request body:**
    - attended: true to mark attended, false to unmark
    - notes: Optional observations or notes about the session

    **Business rules:**
    - Session must be in ASSIGNED status
    - Session date must have passed (for marking attended)
    - If all photographers mark attended, session automatically transitions to ATTENDED status

    **Use cases:**
    - Mark as attended: After completing the photography session
    - Unmark attended: If accidentally marked or session didn't happen
    - Add notes: Document any incidents, observations, or special circumstances

    **State transition:**
    When all photographers mark attended, the session automatically moves to ATTENDED status,
    making it visible to editors for the next phase of the workflow.

    **Access control:**
    You can only mark attendance for sessions where you are assigned as a photographer.

    **Permissions required:** session.mark-attended

    **Errors:**
    - 404: Session not found
    - 403: Not assigned to this session
    - 400: Session not in ASSIGNED status
    - 400: Cannot mark attended before session date
    """
    service = PhotographerService(db)
    return await service.mark_attended(
        session_id=session_id,
        photographer_id=current_user.id,  # type: ignore
        data=data,
    )


@photographers_router.get(
    '/sessions/{session_id}/team',
    response_model=SessionTeamInfo,
    status_code=status.HTTP_200_OK,
    summary='Get session team',
    description='Get list of photographers assigned to a session. Requires session.view.own permission.',
)
async def get_session_team(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.own'))],
    session_id: Annotated[int, Path(description='Session ID', ge=1)],
) -> SessionTeamInfo:
    """
    Get list of all photographers assigned to a session.

    Useful for multi-photographer sessions where team coordination is needed.

    **Returns:**
    - Session ID
    - List of photographer assignments with:
      - Photographer name
      - Role (Lead, Assistant, etc.)
      - Assignment date
      - Attendance status

    **Use cases:**
    - Coordinate with other photographers on the same session
    - See who else is assigned and their roles
    - Check if other photographers have already marked attended

    **Access control:**
    You can only view team info for sessions where you are assigned as a photographer.

    **Permissions required:** session.view.own

    **Errors:**
    - 404: Session not found
    - 403: Not assigned to this session
    """
    service = PhotographerService(db)
    return await service.get_session_team(
        session_id=session_id,
        photographer_id=current_user.id,  # type: ignore
    )


@photographers_router.get(
    '/stats',
    response_model=PhotographerStats,
    status_code=status.HTTP_200_OK,
    summary='Get my statistics',
    description='Get statistics and metrics for the current photographer. Requires session.view.own permission.',
)
async def get_my_stats(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('session.view.own'))],
) -> PhotographerStats:
    """
    Get statistics and metrics for your photography work.

    **Returns:**
    - total_assignments: Total number of sessions assigned to you (all time)
    - upcoming_sessions: Sessions with future dates
    - attended_sessions: Sessions you've marked as attended
    - pending_sessions: Sessions assigned but not yet attended (date passed)
    - next_session_date: Date of your next scheduled session
    - sessions_this_week: Sessions in the next 7 days
    - total_sessions_completed: Sessions attended and completed

    **Use cases:**
    - Dashboard overview
    - Track your workload
    - See upcoming commitments
    - Monitor completion rate

    **Permissions required:** session.view.own
    """
    service = PhotographerService(db)
    return await service.get_my_stats(photographer_id=current_user.id)  # type: ignore
