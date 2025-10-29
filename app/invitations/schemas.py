"""
Invitation schemas for request/response DTOs.

This module defines Pydantic models for invitation-related API operations.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class InvitationCreate(BaseModel):
    """Schema for creating a new invitation."""

    email: EmailStr = Field(..., description='Email address of the invitee')
    custom_message: str | None = Field(
        None,
        max_length=500,
        description='Optional personalized message from the inviter',
    )


class InvitationResponse(BaseModel):
    """Schema for invitation creation response."""

    invitation_url: str = Field(..., description='Full URL to accept the invitation')
    email: str = Field(..., description='Email address of the invitee')
    expires_at: datetime = Field(..., description='Expiration date and time (UTC)')
    message: str = Field(..., description='Success message')


class InvitationValidateResponse(BaseModel):
    """Schema for invitation validation response."""

    is_valid: bool = Field(..., description='Whether the invitation token is valid')
    email: str | None = Field(
        None, description='Email address if invitation is valid'
    )
    message: str = Field(..., description='Validation message')


class InvitationResend(BaseModel):
    """Schema for resending an invitation."""

    email: EmailStr = Field(..., description='Email address to resend invitation to')
    custom_message: str | None = Field(
        None,
        max_length=500,
        description='Optional personalized message from the inviter',
    )
