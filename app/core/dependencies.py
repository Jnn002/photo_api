"""
Common dependency injection type aliases for the Photography Studio API.

This module provides reusable type aliases using Annotated to simplify
dependency injection in FastAPI route handlers.
"""

from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_active_user, get_current_user
from app.users.models import User

# ==================== Database Dependencies ====================

SessionDep = Annotated[AsyncSession, Depends(get_session)]
"""
Dependency for injecting async database session.

Usage:
    @router.get('/items')
    async def list_items(db: SessionDep):
        ...
"""

# ==================== Authentication Dependencies ====================

CurrentUser = Annotated[User, Depends(get_current_user)]
"""
Dependency for injecting the current authenticated user.

Usage:
    @router.get('/me')
    async def get_me(current_user: CurrentUser):
        return current_user
"""

CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
"""
Dependency for injecting the current active user.
Raises exception if user is not active.

Usage:
    @router.post('/items')
    async def create_item(user: CurrentActiveUser):
        ...
"""

# Note: Permission-based type aliases are in app.core.permissions
# to avoid circular imports
