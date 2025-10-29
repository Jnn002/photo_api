"""
Redis utilities for invitation token management.

This module handles storage and retrieval of invitation tokens in Redis
with automatic expiration (TTL). Invitations are stored as JSON objects
with email, custom message, and metadata.
"""

import json
from datetime import datetime

import redis.asyncio as redis

from .config import settings

# Redis connection for invitations
invitation_redis = redis.from_url(settings.REDIS_URL)


def _get_invitation_key(token: str) -> str:
    """Generate Redis key for an invitation token."""
    return f'invitation:{token}'


async def save_invitation(
    token: str,
    email: str,
    custom_message: str | None,
    invited_by: int,
    ttl_days: int,
) -> None:
    """
    Save an invitation token to Redis with TTL.

    Args:
        token: Unique invitation token
        email: Email address of the invitee
        custom_message: Optional custom message from the inviter
        invited_by: User ID of the person who created the invitation
        ttl_days: Time to live in days

    The invitation data is stored as JSON with automatic expiration.
    """
    key = _get_invitation_key(token)
    data = {
        'email': email,
        'custom_message': custom_message,
        'invited_by': invited_by,
        'created_at': datetime.utcnow().isoformat(),
    }

    ttl_seconds = ttl_days * 24 * 60 * 60  # Convert days to seconds
    await invitation_redis.set(
        name=key,
        value=json.dumps(data),
        ex=ttl_seconds,
    )


async def get_invitation(token: str) -> dict | None:
    """
    Retrieve invitation data from Redis.

    Args:
        token: Invitation token to look up

    Returns:
        Dictionary with invitation data if found and not expired, None otherwise
    """
    key = _get_invitation_key(token)
    data = await invitation_redis.get(key)

    if data is None:
        return None

    return json.loads(data)


async def delete_invitation(token: str) -> bool:
    """
    Delete an invitation token from Redis.

    Args:
        token: Invitation token to delete

    Returns:
        True if the token was deleted, False if it didn't exist
    """
    key = _get_invitation_key(token)
    result = await invitation_redis.delete(key)
    return result > 0


async def close_invitation_redis_connection() -> None:
    """Close the Redis connection pool. Should be called on app shutdown."""
    await invitation_redis.close()
