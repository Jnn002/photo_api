"""
Redis token blocklist management for logout functionality.

This module manages revoked JWT tokens using Redis with automatic expiration.
When a user logs out, both access and refresh tokens are added to the blocklist.
"""

import redis.asyncio as redis

from .config import settings

# Redis connection for token blocklist
token_blocklist = redis.from_url(settings.REDIS_URL)


async def add_jti_to_blocklist(jti: str, expiry_seconds: int) -> None:
    """
    Add a JWT token ID (jti) to the blocklist.

    Args:
        jti: JWT token ID to blocklist
        expiry_seconds: Time in seconds until the token would naturally expire

    The TTL ensures Redis automatically removes expired tokens from the blocklist.
    """
    await token_blocklist.set(name=jti, value='revoked', ex=expiry_seconds)


async def token_in_blocklist(jti: str) -> bool:
    """
    Check if a JWT token ID (jti) is in the blocklist.

    Args:
        jti: JWT token ID to check

    Returns:
        True if token is revoked (in blocklist), False otherwise
    """
    result = await token_blocklist.get(jti)
    return result is not None


async def revoke_token_pair(
    access_jti: str,
    refresh_jti: str,
    access_ttl: int,
    refresh_ttl: int,
) -> None:
    """
    Revoke both access and refresh tokens for a user session.

    Args:
        access_jti: Access token JTI
        refresh_jti: Refresh token JTI
        access_ttl: Remaining TTL for access token in seconds
        refresh_ttl: Remaining TTL for refresh token in seconds

    This is used during logout to invalidate the entire session.
    """
    await add_jti_to_blocklist(access_jti, access_ttl)
    await add_jti_to_blocklist(refresh_jti, refresh_ttl)


async def close_redis_connection() -> None:
    """Close the Redis connection pool. Should be called on app shutdown."""
    await token_blocklist.close()
