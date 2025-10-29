"""
Email tasks for asynchronous email sending via Celery.

This module defines Celery tasks for sending emails, including:
- Invitation emails for new team members
- Session notifications
- Payment reminders
"""

import logging
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader
from pydantic import SecretStr

from app.core.config import settings

from .celery_app import celery_app

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


# Email configuration from settings
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates',
)

# Jinja2 environment for template rendering
template_dir = Path(__file__).parent.parent / 'templates'
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))


@celery_app.task(name='send_invitation_email', bind=True, max_retries=3)
def send_invitation_email(
    self,
    recipient_email: str,
    invitation_url: str,
    custom_message: str | None = None,
) -> dict:
    """
    Send an invitation email to a new team member.

    Args:
        recipient_email: Email address of the invitee
        invitation_url: Full URL for accepting the invitation
        custom_message: Optional personalized message from the inviter

    Returns:
        Dictionary with status and message

    Raises:
        Exception: If email sending fails after retries
    """
    try:
        # Render HTML template
        html_template = jinja_env.get_template('invitation_email.html')
        html_body = html_template.render(
            invitation_url=invitation_url,
            custom_message=custom_message,
            app_name=settings.APP_NAME,
            expiry_days=settings.INVITATION_EXPIRY_DAYS,
        )

        # Render text template
        text_template = jinja_env.get_template('invitation_email.txt')
        text_body = text_template.render(
            invitation_url=invitation_url,
            custom_message=custom_message,
            app_name=settings.APP_NAME,
            expiry_days=settings.INVITATION_EXPIRY_DAYS,
        )

        # Create message
        message = MessageSchema(
            subject='Invitación al Sistema de Gestión Fotográfica',
            recipients=[recipient_email],
            body=text_body,
            html=html_body,
            subtype=MessageType.html,
        )

        # Send email
        fm = FastMail(mail_config)

        # Note: FastMail.send_message is async, but Celery tasks must be sync
        # We'll use asyncio.run to execute the async function
        import asyncio

        asyncio.run(fm.send_message(message))

        logger.info(f'Invitation email sent successfully to {recipient_email}')
        return {
            'status': 'success',
            'message': f'Invitation email sent to {recipient_email}',
        }

    except Exception as exc:
        logger.error(f'Failed to send invitation email to {recipient_email}: {exc}')

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(
                f'Max retries exceeded for invitation email to {recipient_email}'
            )
            return {
                'status': 'error',
                'message': f'Failed to send invitation email after {self.max_retries} retries',
            }
