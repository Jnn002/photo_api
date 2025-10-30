"""
Dashboard router for aggregated statistics endpoints.

This module exposes REST endpoints for dashboard/home view metrics.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import SessionDep
from app.core.permissions import require_permission
from app.dashboard.schemas import DashboardStats
from app.dashboard.service import DashboardService
from app.users.models import User

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


# session.view.all
@router.get(
    '/stats',
    response_model=DashboardStats,
    status_code=status.HTTP_200_OK,
    summary='Get dashboard statistics',
    description='Get aggregated statistics for the photography studio dashboard. Requires session.view.all permission.',
)
async def get_dashboard_stats(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('dashboard.view'))],
    year: Annotated[
        int | None, Query(description='Year to filter (default: current year)')
    ] = None,
    month: Annotated[
        int | None,
        Query(ge=1, le=12, description='Month to filter 1-12 (default: current month)'),
    ] = None,
) -> DashboardStats:
    """
    Get dashboard statistics for a specific month.

    **Query parameters:**
    - year: Year to filter (default: current year)
    - month: Month to filter, 1-12 (default: current month)

    **Response:**
    - active_sessions_count: Count of sessions not in COMPLETED or CANCELED status
    - sessions_this_month: Count of sessions created in the specified month
    - total_revenue_this_month: Sum of payments (excluding refunds) received in the specified month
    - pending_balance: Sum of pending balances across all active sessions
    - sessions_by_status: Count of sessions grouped by status

    **Use case:**
    - Frontend dashboard displays these metrics to provide an overview of the studio's operations
    - Coordinator/Admin can see financial health and session pipeline at a glance

    **Permissions required:** session.view.all

    **Future enhancements:**
    - Add client metrics (new clients, active clients)
    - Add catalog metrics (popular items, packages)
    - Add team metrics (photographer activity, editor workload)
    """
    service = DashboardService(db)
    stats = await service.get_stats(year=year, month=month)
    return DashboardStats(**stats)
