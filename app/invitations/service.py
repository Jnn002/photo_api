"""
Invitation service layer for business logic.

This module provides business logic for invitation management operations
including creating invitations, validating tokens, and sending emails.
"""

import logging
import secrets
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.exceptions import (
    DuplicateEmailException,
    InvalidTokenException,
)
from app.core.invitation_redis import (
    delete_invitation,
    get_invitation,
    save_invitation,
)
from app.invitations.schemas import (
    InvitationCreate,
    InvitationResend,
    InvitationResponse,
    InvitationValidateResponse,
)
from app.tasks.email_tasks import send_invitation_email
from app.users.repository import UserRepository

logger = logging.getLogger(__name__)


class InvitationService:
    """Business logic for invitation management."""

    def __init__(self, db):
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)

    async def create_invitation(
        self, data: InvitationCreate, invited_by: int
    ) -> InvitationResponse:
        """
        Create a new invitation and send email.

        Args:
            data: Invitation creation data
            invited_by: User ID of the person creating the invitation

        Returns:
            InvitationResponse with invitation URL and details

        Raises:
            DuplicateEmailException: If email is already registered
        """
        # Check if email is already registered
        existing_user = await self.user_repo.find_by_email(data.email)
        if existing_user:
            raise DuplicateEmailException(
                f'Email {data.email} is already registered in the system'
            )

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expiry_days = settings.INVITATION_EXPIRY_DAYS
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        # Save invitation to Redis
        await save_invitation(
            token=token,
            email=data.email,
            custom_message=data.custom_message,
            invited_by=invited_by,
            ttl_days=expiry_days,
        )

        # Build invitation URL
        invitation_url = f'{settings.FRONTEND_URL}/register?invitation={token}'

        # Send email asynchronously via Celery
        send_invitation_email.delay(
            recipient_email=data.email,
            invitation_url=invitation_url,
            custom_message=data.custom_message,
        )

        logger.info(
            f'Invitation created for {data.email} by user {invited_by}, token: {token[:8]}...'
        )

        return InvitationResponse(
            invitation_url=invitation_url,
            email=data.email,
            expires_at=expires_at,
            message=f'Invitation sent successfully to {data.email}',
        )

    async def validate_invitation(self, token: str) -> InvitationValidateResponse:
        """
        Validate an invitation token.

        Args:
            token: Invitation token to validate

        Returns:
            InvitationValidateResponse with validation result
        """
        # Retrieve invitation from Redis
        invitation_data = await get_invitation(token)

        if not invitation_data:
            return InvitationValidateResponse(
                is_valid=False,
                email=None,
                message='Invalid or expired invitation token',
            )

        # Check if email is already registered (might have registered after invitation)
        existing_user = await self.user_repo.find_by_email(invitation_data['email'])
        if existing_user:
            # Invalidate the invitation since user already exists
            await delete_invitation(token)
            return InvitationValidateResponse(
                is_valid=False,
                email=None,
                message='This email is already registered',
            )

        return InvitationValidateResponse(
            is_valid=True,
            email=invitation_data['email'],
            message='Invitation is valid',
        )

    async def invalidate_invitation(self, token: str) -> bool:
        """
        Invalidate an invitation token (used after successful registration).

        Args:
            token: Invitation token to invalidate

        Returns:
            True if token was invalidated, False if it didn't exist
        """
        result = await delete_invitation(token)
        if result:
            logger.info(f'Invitation token invalidated: {token[:8]}...')
        return result

    async def resend_invitation(
        self, data: InvitationResend, invited_by: int
    ) -> InvitationResponse:
        """
        Resend an invitation (generates new token).

        Args:
            data: Invitation resend data
            invited_by: User ID of the person resending the invitation

        Returns:
            InvitationResponse with new invitation URL

        Raises:
            DuplicateEmailException: If email is already registered
        """
        # Check if email is already registered
        existing_user = await self.user_repo.find_by_email(data.email)
        if existing_user:
            raise DuplicateEmailException(
                f'Email {data.email} is already registered in the system'
            )

        # Generate new token (old tokens will expire naturally via Redis TTL)
        token = secrets.token_urlsafe(32)

        # Calculate expiration
        expiry_days = settings.INVITATION_EXPIRY_DAYS
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        # Save new invitation to Redis
        await save_invitation(
            token=token,
            email=data.email,
            custom_message=data.custom_message,
            invited_by=invited_by,
            ttl_days=expiry_days,
        )

        # Build invitation URL
        invitation_url = f'{settings.FRONTEND_URL}/register?invitation={token}'

        # Send email asynchronously via Celery
        send_invitation_email.delay(
            recipient_email=data.email,
            invitation_url=invitation_url,
            custom_message=data.custom_message,
        )

        logger.info(
            f'Invitation resent to {data.email} by user {invited_by}, token: {token[:8]}...'
        )

        return InvitationResponse(
            invitation_url=invitation_url,
            email=data.email,
            expires_at=expires_at,
            message=f'Invitation resent successfully to {data.email}',
        )

    async def get_invitation_email(self, token: str) -> str:
        """
        Get the email associated with an invitation token.

        Args:
            token: Invitation token

        Returns:
            Email address

        Raises:
            InvalidTokenException: If token is invalid or expired
        """
        invitation_data = await get_invitation(token)

        if not invitation_data:
            raise InvalidTokenException('Invalid or expired invitation token')

        return invitation_data['email']
