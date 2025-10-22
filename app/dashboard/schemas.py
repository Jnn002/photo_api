"""
Dashboard schemas for aggregated statistics and metrics.

This module defines Pydantic v2 schemas for dashboard/home view data.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import SessionStatus


class SessionsByStatus(BaseModel):
    """Schema for sessions count grouped by status."""

    status: SessionStatus
    count: int


class DashboardStats(BaseModel):
    """
    Schema for dashboard statistics.

    Provides aggregated metrics for the photography studio dashboard:
    - Active sessions (not completed or canceled)
    - Sessions created in the current month
    - Total revenue from payments in the current month
    - Pending balance across all active sessions
    - Session counts grouped by status
    """

    active_sessions_count: int = Field(
        ..., description='Count of sessions not in COMPLETED or CANCELED status'
    )
    sessions_this_month: int = Field(
        ..., description='Count of sessions created in the current month'
    )
    total_revenue_this_month: Decimal = Field(
        ..., description='Total payments (excluding refunds) received this month'
    )
    pending_balance: Decimal = Field(
        ..., description='Sum of pending balances across all active sessions'
    )
    sessions_by_status: list[SessionsByStatus] = Field(
        ..., description='Count of sessions grouped by status'
    )

    model_config = ConfigDict(from_attributes=True)
