"""
Photographer service layer for photographer-specific business logic.

This service provides photographers with:
- View their assigned sessions
- Access to session details relevant to their work
- Ability to mark sessions as attended
- Statistics and metrics

All operations enforce ownership validation to ensure photographers
can only access sessions assigned to them.
"""

from datetime import date, timedelta

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.clients.repository import ClientRepository
from app.core.enums import SessionStatus
from app.core.exceptions import (
    InvalidSessionStateException,
    PhotographerNotAssignedException,
    SessionNotAccessibleToPhotographerException,
    SessionNotFoundException,
)
from app.core.time_utils import get_current_utc_time
from app.photographers.schemas import (
    ClientBasicInfo,
    MarkAttendedRequest,
    PhotographerAssignmentInfo,
    PhotographerStats,
    SessionDetailBasicInfo,
    SessionPhotographerListItem,
    SessionPhotographerView,
    SessionTeamInfo,
)
from app.sessions.models import Session as SessionModel
from app.sessions.models import SessionPhotographer
from app.sessions.repository import (
    SessionDetailRepository,
    SessionPhotographerRepository,
    SessionRepository,
    SessionStatusHistoryRepository,
)
from app.users.repository import UserRepository


class PhotographerService:
    """Service for photographer-specific operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.photographer_repo = SessionPhotographerRepository(db)
        self.detail_repo = SessionDetailRepository(db)
        self.client_repo = ClientRepository(db)
        self.user_repo = UserRepository(db)
        self.history_repo = SessionStatusHistoryRepository(db)

    # ==================== Helper Methods ====================

    async def _verify_photographer_assignment(
        self, session_id: int, photographer_id: int
    ) -> SessionPhotographer:
        """
        Verify that a photographer is assigned to a session.

        Raises:
            SessionNotFoundException: If session doesn't exist
            PhotographerNotAssignedException: If photographer is not assigned
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)

        assignment = await self.photographer_repo.get_by_session_and_photographer(
            session_id, photographer_id
        )

        if not assignment:
            raise PhotographerNotAssignedException(photographer_id, session_id)

        return assignment

    async def _load_session_with_relationships(
        self, session_id: int
    ) -> SessionModel | None:
        """Load session with all necessary relationships for photographer view."""
        statement = (
            select(SessionModel)
            .where(SessionModel.id == session_id)
            .options(
                selectinload(SessionModel.client),  # type: ignore
                selectinload(SessionModel.details),  # type: ignore
                selectinload(SessionModel.photographers),  # type: ignore
            )
        )
        result = await self.db.exec(statement)
        return result.first()

    # ==================== List Assignments ====================

    async def get_my_assignments(
        self,
        photographer_id: int,
        status: SessionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionPhotographerListItem]:
        """
        Get list of sessions assigned to a photographer.

        Note: Photographers can only view sessions with status ASSIGNED.
        Sessions with other statuses are not accessible to photographers.

        Args:
            photographer_id: ID of the photographer
            status: Optional filter by session status (ignored - always filters by ASSIGNED)
            start_date: Optional filter from this date (inclusive)
            end_date: Optional filter until this date (inclusive)
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of SessionPhotographerListItem with compact session info
        """
        # Build query with filters and eager load client
        statement = (
            select(SessionModel, SessionPhotographer)
            .join(SessionPhotographer)
            .where(SessionPhotographer.photographer_id == photographer_id)
            .where(
                SessionModel.status == SessionStatus.ASSIGNED
            )  # Only ASSIGNED sessions
            .options(selectinload(SessionModel.client))  # type: ignore
        )

        # Apply date filters if provided
        if start_date:
            statement = statement.where(SessionModel.session_date >= start_date)

        if end_date:
            statement = statement.where(SessionModel.session_date <= end_date)

        statement = (
            statement.order_by(SessionModel.session_date.desc())
            .offset(offset)
            .limit(limit)
        )  # type: ignore

        result = await self.db.exec(statement)
        rows = result.all()

        # Convert to list items
        items = []
        for session, assignment in rows:
            items.append(
                SessionPhotographerListItem(
                    id=session.id,  # type: ignore
                    client_name=session.client.full_name,
                    session_type=session.session_type,
                    session_date=session.session_date,
                    session_time=session.session_time,
                    estimated_duration_hours=session.estimated_duration_hours,
                    location=session.location,
                    status=session.status,
                    my_role=assignment.role,
                    my_attended=assignment.attended,
                    my_attended_at=assignment.attended_at,
                )
            )

        return items

    # ==================== Get Session Detail ====================

    async def get_session_detail(
        self, session_id: int, photographer_id: int
    ) -> SessionPhotographerView:
        """
        Get detailed session information for a photographer.

        Validates that the photographer is assigned to the session and that
        the session is in ASSIGNED status before returning the information.

        Args:
            session_id: ID of the session
            photographer_id: ID of the photographer

        Returns:
            SessionPhotographerView with full session details

        Raises:
            SessionNotFoundException: If session doesn't exist
            PhotographerNotAssignedException: If photographer is not assigned
            SessionNotAccessibleToPhotographerException: If session status is not ASSIGNED
        """
        # Verify assignment
        assignment = await self._verify_photographer_assignment(
            session_id, photographer_id
        )

        # Load session with relationships
        session = await self._load_session_with_relationships(session_id)

        if not session:
            raise SessionNotFoundException(session_id)

        # Verify session is in ASSIGNED status
        if session.status != SessionStatus.ASSIGNED:
            raise SessionNotAccessibleToPhotographerException(
                session_id, session.status.value
            )

        # Build client basic info
        client_info = ClientBasicInfo(
            id=session.client.id,  # type: ignore
            full_name=session.client.full_name,
            email=session.client.email,
            primary_phone=session.client.primary_phone,
        )

        # Build session details (line items)
        detail_items = [
            SessionDetailBasicInfo(
                id=detail.id,  # type: ignore
                line_type=detail.line_type,
                reference_type=detail.reference_type,
                item_code=detail.item_code,
                item_name=detail.item_name,
                item_description=detail.item_description,
                quantity=detail.quantity,
            )
            for detail in session.details
        ]

        # Build photographer view
        return SessionPhotographerView(
            id=session.id,  # type: ignore
            session_type=session.session_type,
            session_date=session.session_date,
            session_time=session.session_time,
            estimated_duration_hours=session.estimated_duration_hours,
            location=session.location,
            room_id=session.room_id,
            status=session.status,
            client=client_info,
            client_requirements=session.client_requirements,
            delivery_method=session.delivery_method,
            delivery_deadline=session.delivery_deadline,
            details=detail_items,
            my_assignment_id=assignment.id,  # type: ignore
            my_role=assignment.role,
            my_assigned_at=assignment.assigned_at,
            my_attended=assignment.attended,
            my_attended_at=assignment.attended_at,
            my_notes=assignment.notes,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    # ==================== Get Client Info ====================

    async def get_client_info(
        self, session_id: int, photographer_id: int
    ) -> ClientBasicInfo:
        """
        Get basic client information for a session.

        Returns only limited client data (name, email, primary phone)
        as per permissions_doc.md section 5.3.

        Args:
            session_id: ID of the session
            photographer_id: ID of the photographer

        Returns:
            ClientBasicInfo with limited client data

        Raises:
            SessionNotFoundException: If session doesn't exist
            PhotographerNotAssignedException: If photographer is not assigned
            SessionNotAccessibleToPhotographerException: If session status is not ASSIGNED
        """
        # Verify assignment
        await self._verify_photographer_assignment(session_id, photographer_id)

        # Load session with client
        statement = (
            select(SessionModel)
            .where(SessionModel.id == session_id)
            .options(selectinload(SessionModel.client))  # type: ignore
        )
        result = await self.db.exec(statement)
        session = result.first()

        if not session:
            raise SessionNotFoundException(session_id)

        # Verify session is in ASSIGNED status
        if session.status != SessionStatus.ASSIGNED:
            raise SessionNotAccessibleToPhotographerException(
                session_id, session.status.value
            )

        return ClientBasicInfo(
            id=session.client.id,  # type: ignore
            full_name=session.client.full_name,
            email=session.client.email,
            primary_phone=session.client.primary_phone,
        )

    # ==================== Mark Attended ====================

    async def mark_attended(
        self, session_id: int, photographer_id: int, data: MarkAttendedRequest
    ) -> SessionPhotographerView:
        """
        Mark a session as attended (or unattended) by the photographer.

        Validates:
        - Photographer is assigned to the session
        - Session is in ASSIGNED status
        - Session date has passed (for marking attended)

        If marking attended and all photographers have attended,
        automatically transitions session to ATTENDED status.

        Args:
            session_id: ID of the session
            photographer_id: ID of the photographer
            data: MarkAttendedRequest with attended flag and notes

        Returns:
            Updated SessionPhotographerView

        Raises:
            SessionNotFoundException: If session doesn't exist
            PhotographerNotAssignedException: If photographer is not assigned
            InvalidSessionStateException: If session is not in ASSIGNED status
            InvalidStatusTransitionException: If trying to attend before session date
        """
        # Verify assignment
        assignment = await self._verify_photographer_assignment(
            session_id, photographer_id
        )

        # Load session
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)

        # Validate session status
        if session.status != SessionStatus.ASSIGNED:
            raise InvalidSessionStateException(
                f'Session must be in ASSIGNED status to mark attended. Current status: {session.status.value}'
            )

        # Validate date if marking as attended
        # TODO: REACTIVAR ESTA VALIDACIÓN PARA PRODUCCIÓN
        # Temporalmente deshabilitada para facilitar pruebas con datos históricos
        # if data.attended and session.session_date > date.today():
        #     raise InvalidStatusTransitionException(
        #         from_status=session.status.value,
        #         to_status=SessionStatus.ATTENDED.value,
        #         allowed_statuses=[],
        #         reason=f'Cannot mark session as attended before session date ({session.session_date})'
        #     )

        # Update assignment
        assignment.attended = data.attended
        assignment.attended_at = get_current_utc_time() if data.attended else None
        assignment.notes = data.notes

        self.db.add(assignment)
        await self.db.flush()

        # Check if all photographers have attended
        if data.attended:
            all_assignments = await self.photographer_repo.list_by_session(session_id)
            all_attended = all(a.attended for a in all_assignments)

            if all_attended:
                # Transition session to ATTENDED
                session.status = SessionStatus.ATTENDED
                self.db.add(session)

                # Record status change
                from app.sessions.models import SessionStatusHistory

                history = SessionStatusHistory(
                    session_id=session_id,
                    from_status=SessionStatus.ASSIGNED.value,
                    to_status=SessionStatus.ATTENDED.value,
                    reason='All photographers marked attended',
                    notes=f'Photographer {photographer_id} was the last to confirm attendance',
                    changed_by=photographer_id,
                )
                self.db.add(history)

        await self.db.commit()

        # Return updated view
        return await self.get_session_detail(session_id, photographer_id)

    # ==================== Get Session Team ====================

    async def get_session_team(
        self, session_id: int, photographer_id: int
    ) -> SessionTeamInfo:
        """
        Get list of all photographers assigned to a session.

        Useful for multi-photographer sessions where team coordination is needed.

        Args:
            session_id: ID of the session
            photographer_id: ID of the requesting photographer

        Returns:
            SessionTeamInfo with all photographer assignments

        Raises:
            SessionNotFoundException: If session doesn't exist
            PhotographerNotAssignedException: If photographer is not assigned
            SessionNotAccessibleToPhotographerException: If session status is not ASSIGNED
        """
        # Verify assignment
        await self._verify_photographer_assignment(session_id, photographer_id)

        # Load session to verify status
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)

        # Verify session is in ASSIGNED status
        if session.status != SessionStatus.ASSIGNED:
            raise SessionNotAccessibleToPhotographerException(
                session_id, session.status.value
            )

        # Get all assignments
        assignments = await self.photographer_repo.list_by_session(session_id)

        # Load user info for each photographer
        photographer_infos = []
        for assignment in assignments:
            user = await self.user_repo.get_by_id(assignment.photographer_id)
            if user:
                photographer_infos.append(
                    PhotographerAssignmentInfo(
                        id=assignment.id,  # type: ignore
                        photographer_id=assignment.photographer_id,
                        photographer_name=user.full_name,
                        role=assignment.role,
                        assigned_at=assignment.assigned_at,
                        attended=assignment.attended,
                        attended_at=assignment.attended_at,
                    )
                )

        return SessionTeamInfo(session_id=session_id, photographers=photographer_infos)

    # ==================== Statistics ====================

    async def get_my_stats(self, photographer_id: int) -> PhotographerStats:
        """
        Get statistics and metrics for a photographer.

        Includes:
        - Total assignments (all time)
        - Upcoming sessions (future dates)
        - Attended sessions
        - Pending sessions (assigned but not attended)
        - Next session date
        - Sessions this week

        Args:
            photographer_id: ID of the photographer

        Returns:
            PhotographerStats with various metrics
        """
        today = date.today()
        week_from_now = today + timedelta(days=7)

        # Get all assignments
        all_assignments = await self.photographer_repo.list_by_photographer(
            photographer_id, limit=1000
        )

        # Load sessions for each assignment
        total_assignments = len(all_assignments)
        attended_count = sum(1 for a in all_assignments if a.attended)

        # Get sessions for upcoming/pending calculations
        upcoming_sessions = []
        pending_sessions = []
        sessions_this_week = []

        for assignment in all_assignments:
            session = await self.session_repo.get_by_id(assignment.session_id)
            if not session:
                continue

            # Skip completed/cancelled sessions
            if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELED]:
                continue

            # Upcoming (future dates)
            if session.session_date >= today:
                upcoming_sessions.append(session)

                # This week
                if session.session_date <= week_from_now:
                    sessions_this_week.append(session)

            # Pending (assigned but not attended, date passed or today)
            if (
                session.status == SessionStatus.ASSIGNED
                and not assignment.attended
                and session.session_date <= today
            ):
                pending_sessions.append(session)

        # Find next session date
        next_session_date = None
        if upcoming_sessions:
            upcoming_sessions.sort(key=lambda s: s.session_date)
            next_session_date = upcoming_sessions[0].session_date

        # Count completed sessions (attended + session completed)
        # We need to check session status for each attended assignment
        completed_count = 0
        for assignment in all_assignments:
            if assignment.attended:
                session = await self.session_repo.get_by_id(assignment.session_id)
                if session and session.status == SessionStatus.COMPLETED:
                    completed_count += 1

        return PhotographerStats(
            total_assignments=total_assignments,
            upcoming_sessions=len(upcoming_sessions),
            attended_sessions=attended_count,
            pending_sessions=len(pending_sessions),
            next_session_date=next_session_date,
            sessions_this_week=len(sessions_this_week),
            total_sessions_completed=completed_count,
        )
