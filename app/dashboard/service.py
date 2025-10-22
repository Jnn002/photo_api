"""
Dashboard service layer for aggregated statistics.

This module orchestrates data from multiple modules (sessions, clients, catalog)
to provide aggregated metrics for the dashboard/home view.
"""

from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.sessions.repository import SessionPaymentRepository, SessionRepository


class DashboardService:
    """Service for dashboard statistics and aggregated metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepository(db)
        self.payment_repo = SessionPaymentRepository(db)

    async def get_stats(self, year: int | None = None, month: int | None = None) -> dict:
        """
        Get dashboard statistics for a specific month.

        Args:
            year: Year to filter (default: current year)
            month: Month to filter (default: current month)

        Returns:
            Dictionary with dashboard statistics:
            - active_sessions_count: Count of sessions not in COMPLETED or CANCELED
            - sessions_this_month: Count of sessions created in the specified month
            - total_revenue_this_month: Sum of payments (excluding refunds) in the specified month
            - pending_balance: Sum of pending balances across all active sessions
            - sessions_by_status: List of dictionaries with status and count
        """
        # Default to current year/month
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        # Get all statistics
        active_sessions = await self.session_repo.count_active_sessions()
        sessions_this_month = await self.session_repo.count_sessions_by_created_month(
            year, month
        )
        pending_balance = await self.session_repo.sum_pending_balance()
        total_revenue = await self.payment_repo.sum_revenue_by_month(year, month)
        sessions_by_status_raw = await self.session_repo.count_sessions_by_status()

        # Format sessions_by_status
        sessions_by_status = [
            {'status': status, 'count': count} for status, count in sessions_by_status_raw
        ]

        return {
            'active_sessions_count': active_sessions,
            'sessions_this_month': sessions_this_month,
            'total_revenue_this_month': total_revenue,
            'pending_balance': pending_balance,
            'sessions_by_status': sessions_by_status,
        }
