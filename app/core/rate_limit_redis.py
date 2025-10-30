"""
Redis client for rate limiting using sliding window algorithm.

This module provides a Redis-backed rate limiter that uses sorted sets
to implement a precise sliding window algorithm. This approach is more
accurate than fixed window and prevents burst traffic at window boundaries.

Algorithm:
- Uses Redis ZSET (sorted set) where:
  - Members: timestamp strings (microsecond precision)
  - Scores: timestamp floats (for range queries)
- For each request:
  1. Remove entries older than the window
  2. Count remaining entries
  3. If under limit, add current timestamp
  4. Return whether request is allowed

Example:
    limiter = RateLimitRedis(redis_url="redis://localhost:6379/0")
    allowed = await limiter.check_limit("user:123:login", limit=5, window_seconds=60)
"""

import time
from typing import TypedDict

import redis.asyncio as redis


class RateLimitResult(TypedDict):
    """Result of a rate limit check."""

    allowed: bool
    current_usage: int
    limit: int
    window_seconds: int
    retry_after: int | None  # Seconds to wait before next attempt


class RateLimitRedis:
    """
    Redis-backed rate limiter using sliding window algorithm.

    Attributes:
        redis_client: Async Redis connection
        key_prefix: Prefix for all rate limit keys (default: "rate_limit:")
    """

    def __init__(self, redis_url: str, key_prefix: str = 'rate_limit:'):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            key_prefix: Prefix for Redis keys to namespace rate limit data
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix

    async def close(self):
        """Close Redis connection. Should be called on application shutdown."""
        await self.redis_client.aclose()

    def _make_key(self, identifier: str) -> str:
        """
        Create namespaced Redis key.

        Args:
            identifier: Unique identifier (e.g., "user:123:endpoint")

        Returns:
            Namespaced key (e.g., "rate_limit:user:123:endpoint")
        """
        return f'{self.key_prefix}{identifier}'

    async def check_limit(
        self, identifier: str, limit: int, window_seconds: int
    ) -> RateLimitResult:
        """
        Check if request is within rate limit using sliding window.

        This method implements the sliding window algorithm:
        1. Calculate window boundaries (now - window_seconds to now)
        2. Remove old entries outside the window
        3. Count current entries in window
        4. If under limit, add current timestamp and allow
        5. If over limit, calculate retry_after and deny

        Args:
            identifier: Unique key for this rate limit (user, IP, endpoint, etc.)
            limit: Maximum number of requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult with:
                - allowed: True if request is allowed, False if rate limited
                - current_usage: Current number of requests in window
                - limit: The limit that was checked against
                - window_seconds: The window size in seconds
                - retry_after: Seconds until next request allowed (if denied)

        Example:
            result = await limiter.check_limit("user:123:login", 5, 60)
            if result["allowed"]:
                # Process request
                pass
            else:
                # Return 429 with retry_after
                raise RateLimitExceeded(retry_after=result["retry_after"])
        """
        key = self._make_key(identifier)
        now = time.time()
        window_start = now - window_seconds

        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()

        # 1. Remove entries older than the window
        pipe.zremrangebyscore(key, '-inf', window_start)

        # 2. Count current entries in window
        pipe.zcard(key)

        # 3. Get oldest entry to calculate retry_after if needed
        pipe.zrange(key, 0, 0, withscores=True)

        # Execute pipeline
        _, current_count, oldest_entries = await pipe.execute()

        # Check if under limit
        if current_count < limit:
            # Add current timestamp and allow request
            # Use microsecond precision to avoid duplicate scores
            timestamp_key = f'{now:.6f}'
            await self.redis_client.zadd(key, {timestamp_key: now})

            # Set TTL to window_seconds + buffer to auto-cleanup
            await self.redis_client.expire(key, window_seconds + 10)

            return RateLimitResult(
                allowed=True,
                current_usage=current_count + 1,
                limit=limit,
                window_seconds=window_seconds,
                retry_after=None,
            )
        else:
            # Rate limit exceeded
            # Calculate retry_after based on oldest entry in window
            if oldest_entries:
                oldest_timestamp = oldest_entries[0][1]  # Score from (member, score)
                retry_after = int(oldest_timestamp + window_seconds - now) + 1
            else:
                retry_after = window_seconds

            return RateLimitResult(
                allowed=False,
                current_usage=current_count,
                limit=limit,
                window_seconds=window_seconds,
                retry_after=retry_after,
            )

    async def reset_limit(self, identifier: str) -> bool:
        """
        Reset rate limit for a specific identifier.

        Useful for:
        - Testing
        - Manual admin overrides
        - Clearing limits after security incidents

        Args:
            identifier: The rate limit key to reset

        Returns:
            True if key was deleted, False if it didn't exist
        """
        key = self._make_key(identifier)
        result = await self.redis_client.delete(key)
        return result > 0

    async def get_current_usage(self, identifier: str) -> int:
        """
        Get current usage count without modifying limits.

        Args:
            identifier: The rate limit key to check

        Returns:
            Number of requests in the current window
        """
        key = self._make_key(identifier)
        return await self.redis_client.zcard(key)


# Singleton instance (initialized in app lifespan)
_rate_limit_redis: RateLimitRedis | None = None


def get_rate_limit_redis() -> RateLimitRedis:
    """
    Get the global RateLimitRedis instance.

    This should be initialized in the FastAPI lifespan context manager.

    Raises:
        RuntimeError: If rate limiter hasn't been initialized

    Returns:
        The global RateLimitRedis instance
    """
    if _rate_limit_redis is None:
        raise RuntimeError(
            'Rate limit Redis not initialized. '
            'Call init_rate_limit_redis() in app lifespan.'
        )
    return _rate_limit_redis


def init_rate_limit_redis(redis_url: str) -> RateLimitRedis:
    """
    Initialize the global RateLimitRedis instance.

    Should be called once in the FastAPI lifespan startup.

    Args:
        redis_url: Redis connection URL

    Returns:
        The initialized RateLimitRedis instance
    """
    global _rate_limit_redis
    _rate_limit_redis = RateLimitRedis(redis_url)
    return _rate_limit_redis


async def close_rate_limit_redis():
    """
    Close the global RateLimitRedis instance.

    Should be called in the FastAPI lifespan shutdown.
    """
    global _rate_limit_redis
    if _rate_limit_redis is not None:
        await _rate_limit_redis.close()
        _rate_limit_redis = None
