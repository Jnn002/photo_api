"""
Invitation routers for invitation management endpoints.

This module exposes REST endpoints for:
- Creating invitations
- Validating invitation tokens
- Resending invitations
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import CurrentActiveUser, SessionDep
from app.core.permissions import require_permission
from app.invitations.schemas import (
    InvitationCreate,
    InvitationResend,
    InvitationResponse,
    InvitationValidateResponse,
)
from app.invitations.service import InvitationService
from app.users.models import User

router = APIRouter(prefix='/invitations', tags=['invitations'])


@router.post(
    '',
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create invitation',
    description='Create a new team member invitation. Requires user:create permission.',
)
async def create_invitation(
    data: InvitationCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.create'))],
) -> InvitationResponse:
    """
    Create a new invitation and send email to the invitee.

    This endpoint:
    1. Validates that the email is not already registered
    2. Generates a secure invitation token
    3. Saves the invitation to Redis with TTL
    4. Sends an invitation email via Celery (asynchronous)

    **Required fields:**
    - email: Email address of the person to invite

    **Optional fields:**
    - custom_message: Personalized message from the inviter (max 500 chars)

    **Returns:**
    - invitation_url: Full URL for the invitee to accept
    - email: Email address of the invitee
    - expires_at: When the invitation expires (UTC)
    - message: Success message

    **Permissions required:** user.create

    **Business rules:**
    - Email must not be already registered
    - Invitation expires in INVITATION_EXPIRY_DAYS (default: 7)
    - Email is sent asynchronously (doesn't block response)
    """
    service = InvitationService(db)
    return await service.create_invitation(data, invited_by=current_user.id)  # type: ignore


@router.get(
    '/validate/{token}',
    response_model=InvitationValidateResponse,
    status_code=status.HTTP_200_OK,
    summary='Validate invitation token',
    description='Validate an invitation token. Public endpoint (no authentication required).',
)
async def validate_invitation(
    token: Annotated[str, Path(description='Invitation token to validate')],
    db: SessionDep,
) -> InvitationValidateResponse:
    """
    Validate an invitation token.

    This endpoint is **public** (no authentication required) and is used by
    the frontend to verify if an invitation token is valid before showing
    the registration form.

    **Returns:**
    - is_valid: Whether the token is valid
    - email: Email address if valid (pre-filled in registration form)
    - message: Validation message

    **Validation rules:**
    - Token must exist in Redis (not expired)
    - Email must not be already registered
    - If email is registered after invitation, token is invalidated
    """
    service = InvitationService(db)
    return await service.validate_invitation(token)


@router.post(
    '/resend',
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Resend invitation',
    description='Resend an invitation with a new token. Requires user:create permission.',
)
async def resend_invitation(
    data: InvitationResend,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.create'))],
) -> InvitationResponse:
    """
    Resend an invitation to an email address.

    This generates a **new token** with a fresh expiration date. Old tokens
    will naturally expire via Redis TTL.

    **Use cases:**
    - Original invitation expired
    - User didn't receive the email
    - Admin wants to send updated custom message

    **Required fields:**
    - email: Email address to resend invitation to

    **Optional fields:**
    - custom_message: New personalized message (replaces previous)

    **Permissions required:** user.create

    **Business rules:**
    - Email must not be already registered
    - Generates new token (old tokens remain valid until TTL expires)
    - Sends new email asynchronously
    """
    service = InvitationService(db)
    return await service.resend_invitation(data, invited_by=current_user.id)  # type: ignore
