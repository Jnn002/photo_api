"""
Sessions repositories for database operations.

This module provides data access methods for Session-related entities
using SQLModel's native async methods.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import PaymentType, SessionStatus
from app.core.time_utils import get_current_utc_time
from app.sessions.models import (
    Session as SessionModel,
)
from app.sessions.models import (
    SessionDetail,
    SessionPayment,
    SessionPhotographer,
    SessionStatusHistory,
)

# ==================== Session Repository ====================


class SessionRepository:
    """Repository for Session database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, session_id: int) -> SessionModel | None:
        """Get session by ID."""
        return await self.db.get(SessionModel, session_id)

    async def get_with_details(self, session_id: int) -> SessionModel | None:
        """
        Get session by ID with details eagerly loaded.

        Uses selectinload for optimized query performance.
        """
        statement = (
            select(SessionModel)
            .where(SessionModel.id == session_id)
            .options(
                selectinload(SessionModel.details)  # type: ignore
            )
        )
        result = await self.db.exec(statement)
        return result.first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[SessionModel]:
        """List all sessions with pagination."""
        statement = (
            select(SessionModel)
            .order_by(col(SessionModel.session_date).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_status(
        self, status: SessionStatus, limit: int = 100, offset: int = 0
    ) -> list[SessionModel]:
        """List sessions by status."""
        statement = (
            select(SessionModel)
            .where(SessionModel.status == status)
            .order_by(col(SessionModel.session_date).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_client(
        self, client_id: int, limit: int = 100, offset: int = 0
    ) -> list[SessionModel]:
        """List sessions by client."""
        statement = (
            select(SessionModel)
            .where(SessionModel.client_id == client_id)
            .order_by(col(SessionModel.session_date).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionModel]:
        """List sessions within a date range."""
        statement = (
            select(SessionModel)
            .where(SessionModel.session_date >= start_date)
            .where(SessionModel.session_date <= end_date)
            .order_by(col(SessionModel.session_date))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_photographer(
        self, photographer_id: int, limit: int = 100, offset: int = 0
    ) -> list[SessionModel]:
        """List sessions assigned to a photographer."""
        statement = (
            select(SessionModel)
            .join(SessionPhotographer)
            .where(SessionPhotographer.photographer_id == photographer_id)
            .order_by(col(SessionModel.session_date).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_editor(
        self, editor_id: int, limit: int = 100, offset: int = 0
    ) -> list[SessionModel]:
        """List sessions assigned to an editor."""
        statement = (
            select(SessionModel)
            .where(SessionModel.editing_assigned_to == editor_id)
            .order_by(col(SessionModel.session_date).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def check_room_availability(
        self, room_id: int, session_date: date, session_time: str
    ) -> bool:
        """
        Check if a room is available for a given date and time.

        Returns True if available, False if already booked.
        """
        statement = select(SessionModel).where(
            SessionModel.room_id == room_id,
            SessionModel.session_date == session_date,
            SessionModel.session_time == session_time,
            col(SessionModel.status).not_in(
                [SessionStatus.CANCELED, SessionStatus.COMPLETED]
            ),
        )
        result = await self.db.exec(statement)
        existing = result.first()
        return existing is None

    async def create(self, session: SessionModel) -> SessionModel:
        """Create a new session."""
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def update(self, session: SessionModel, data: dict) -> SessionModel:
        """Update an existing session."""
        session.sqlmodel_update(data)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def count_sessions(
        self,
        client_id: int | None = None,
        status: SessionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        photographer_id: int | None = None,
        editor_id: int | None = None,
    ) -> int:
        """
        Count sessions matching filters.

        Args:
            client_id: Filter by client
            status: Filter by session status
            start_date: Filter from this date (inclusive)
            end_date: Filter until this date (inclusive)
            photographer_id: Filter by assigned photographer
            editor_id: Filter by assigned editor

        Returns:
            Total count of sessions matching filters
        """
        statement = select(func.count(SessionModel.id))

        if client_id:
            statement = statement.where(SessionModel.client_id == client_id)

        if status:
            statement = statement.where(SessionModel.status == status)

        if start_date:
            statement = statement.where(SessionModel.session_date >= start_date)

        if end_date:
            statement = statement.where(SessionModel.session_date <= end_date)

        if photographer_id:
            statement = statement.join(SessionPhotographer).where(
                SessionPhotographer.photographer_id == photographer_id
            )

        if editor_id:
            statement = statement.where(SessionModel.editing_assigned_to == editor_id)

        result = await self.db.exec(statement)
        return result.one()

    # ==================== Dashboard Statistics ====================

    async def count_active_sessions(self) -> int:
        """
        Count sessions that are active (not COMPLETED or CANCELED).

        Returns:
            Count of active sessions
        """
        statement = select(func.count(SessionModel.id)).where(
            col(SessionModel.status).not_in([SessionStatus.COMPLETED, SessionStatus.CANCELED])
        )
        result = await self.db.exec(statement)
        return result.one()

    async def count_sessions_by_created_month(self, year: int, month: int) -> int:
        """
        Count sessions created in a specific month.

        Args:
            year: Year to filter
            month: Month to filter (1-12)

        Returns:
            Count of sessions created in the specified month
        """
        from datetime import datetime
        from sqlalchemy import extract

        statement = select(func.count(SessionModel.id)).where(
            extract('year', SessionModel.created_at) == year,
            extract('month', SessionModel.created_at) == month
        )
        result = await self.db.exec(statement)
        return result.one()

    async def sum_pending_balance(self) -> Decimal:
        """
        Sum of pending balances across all active sessions.

        Returns:
            Total pending balance (balance_amount) for active sessions
        """
        statement = select(func.coalesce(func.sum(SessionModel.balance_amount), 0)).where(
            col(SessionModel.status).not_in([SessionStatus.COMPLETED, SessionStatus.CANCELED])
        )
        result = await self.db.exec(statement)
        return Decimal(str(result.one()))

    async def count_sessions_by_status(self) -> list[tuple[SessionStatus, int]]:
        """
        Count sessions grouped by status.

        Returns:
            List of tuples (status, count) for all session statuses
        """
        statement = (
            select(SessionModel.status, func.count(SessionModel.id))
            .group_by(SessionModel.status)
        )
        result = await self.db.exec(statement)
        return list(result.all())


# ==================== Session Detail Repository ====================


class SessionDetailRepository:
    """Repository for SessionDetail database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, detail_id: int) -> SessionDetail | None:
        """Get session detail by ID."""
        return await self.db.get(SessionDetail, detail_id)

    async def list_by_session(self, session_id: int) -> list[SessionDetail]:
        """List all details for a session."""
        statement = (
            select(SessionDetail)
            .where(SessionDetail.session_id == session_id)
            .order_by(col(SessionDetail.created_at))
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, detail: SessionDetail) -> SessionDetail:
        """Create a new session detail."""
        self.db.add(detail)
        await self.db.flush()
        await self.db.refresh(detail)
        return detail

    async def create_many(self, details: list[SessionDetail]) -> list[SessionDetail]:
        """Create multiple session details."""
        for detail in details:
            self.db.add(detail)

        await self.db.flush()

        for detail in details:
            await self.db.refresh(detail)

        return details

    async def mark_delivered(self, detail: SessionDetail) -> SessionDetail:
        """Mark a session detail as delivered."""
        detail.is_delivered = True
        detail.delivered_at = get_current_utc_time()
        self.db.add(detail)
        await self.db.flush()
        await self.db.refresh(detail)
        return detail


# ==================== Session Payment Repository ====================


class SessionPaymentRepository:
    """Repository for SessionPayment database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, payment_id: int) -> SessionPayment | None:
        """Get session payment by ID."""
        return await self.db.get(SessionPayment, payment_id)

    async def list_by_session(self, session_id: int) -> list[SessionPayment]:
        """List all payments for a session."""
        statement = (
            select(SessionPayment)
            .where(SessionPayment.session_id == session_id)
            .order_by(col(SessionPayment.payment_date).desc())
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def get_total_paid(self, session_id: int) -> Decimal:
        """
        Get total amount paid for a session.

        Sums all payments excluding refunds.
        """
        statement = (
            select(func.sum(SessionPayment.amount))
            .where(SessionPayment.session_id == session_id)
            .where(SessionPayment.payment_type != PaymentType.REFUND)
        )
        result = await self.db.exec(statement)
        total = result.first()
        return total or Decimal('0.00')

    async def get_total_refunded(self, session_id: int) -> Decimal:
        """Get total amount refunded for a session."""
        statement = (
            select(func.sum(SessionPayment.amount))
            .where(SessionPayment.session_id == session_id)
            .where(SessionPayment.payment_type == PaymentType.REFUND)
        )
        result = await self.db.exec(statement)
        total = result.first()
        return total or Decimal('0.00')

    async def create(self, payment: SessionPayment) -> SessionPayment:
        """Create a new session payment."""
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def sum_revenue_by_month(self, year: int, month: int) -> Decimal:
        """
        Sum total revenue (payments excluding refunds) for a specific month.

        Args:
            year: Year to filter
            month: Month to filter (1-12)

        Returns:
            Total revenue for the specified month
        """
        from sqlalchemy import extract

        statement = (
            select(func.coalesce(func.sum(SessionPayment.amount), 0))
            .where(SessionPayment.payment_type != PaymentType.REFUND)
            .where(
                extract('year', SessionPayment.payment_date) == year,
                extract('month', SessionPayment.payment_date) == month
            )
        )
        result = await self.db.exec(statement)
        return Decimal(str(result.one()))


# ==================== Session Photographer Repository ====================


class SessionPhotographerRepository:
    """Repository for SessionPhotographer database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, assignment_id: int) -> SessionPhotographer | None:
        """Get photographer assignment by ID."""
        return await self.db.get(SessionPhotographer, assignment_id)

    async def get_by_session_and_photographer(
        self, session_id: int, photographer_id: int
    ) -> SessionPhotographer | None:
        """Get photographer assignment by session and photographer IDs."""
        statement = select(SessionPhotographer).where(
            SessionPhotographer.session_id == session_id,
            SessionPhotographer.photographer_id == photographer_id,
        )
        result = await self.db.exec(statement)
        return result.first()

    async def list_by_session(self, session_id: int) -> list[SessionPhotographer]:
        """List all photographer assignments for a session."""
        statement = (
            select(SessionPhotographer)
            .where(SessionPhotographer.session_id == session_id)
            .order_by(col(SessionPhotographer.assigned_at))
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def list_by_photographer(
        self, photographer_id: int, limit: int = 100, offset: int = 0
    ) -> list[SessionPhotographer]:
        """List all assignments for a photographer."""
        statement = (
            select(SessionPhotographer)
            .where(SessionPhotographer.photographer_id == photographer_id)
            .order_by(col(SessionPhotographer.assigned_at).desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def check_photographer_availability(
        self, photographer_id: int, session_date: date, session_time: str
    ) -> bool:
        """
        Check if a photographer is available for a given date and time.

        Returns True if available, False if already assigned.
        """
        statement = (
            select(SessionPhotographer)
            .join(SessionModel)
            .where(
                SessionPhotographer.photographer_id == photographer_id,
                SessionModel.session_date == session_date,
                SessionModel.session_time == session_time,
                col(SessionModel.status).not_in(
                    [SessionStatus.CANCELED, SessionStatus.COMPLETED]
                ),
            )
        )
        result = await self.db.exec(statement)
        existing = result.first()
        return existing is None

    async def create(self, assignment: SessionPhotographer) -> SessionPhotographer:
        """Create a new photographer assignment."""
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def mark_attended(
        self, assignment: SessionPhotographer
    ) -> SessionPhotographer:
        """Mark photographer as attended."""
        assignment.attended = True
        assignment.attended_at = get_current_utc_time()
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def remove_assignment(self, assignment_id: int) -> None:
        """Remove a photographer assignment."""
        assignment = await self.get_by_id(assignment_id)

        if assignment:
            await self.db.delete(assignment)
            await self.db.flush()


# ==================== Session Status History Repository ====================


class SessionStatusHistoryRepository:
    """Repository for SessionStatusHistory database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with async database session."""
        self.db = db

    async def get_by_id(self, history_id: int) -> SessionStatusHistory | None:
        """Get status history record by ID."""
        return await self.db.get(SessionStatusHistory, history_id)

    async def list_by_session(self, session_id: int) -> list[SessionStatusHistory]:
        """List all status history for a session."""
        statement = (
            select(SessionStatusHistory)
            .where(SessionStatusHistory.session_id == session_id)
            .order_by(col(SessionStatusHistory.changed_at))
        )
        result = await self.db.exec(statement)
        return list(result.all())

    async def create(self, history: SessionStatusHistory) -> SessionStatusHistory:
        """Create a new status history record."""
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        return history
