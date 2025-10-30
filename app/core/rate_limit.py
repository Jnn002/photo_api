"""
Rate limiting factory functions and dependencies for FastAPI.

This module provides a dependency injection pattern for rate limiting,
similar to the existing require_permission() pattern. It supports:
- Rate limiting by user ID (authenticated requests)
- Rate limiting by IP address (public endpoints)
- Rate limiting by endpoint (global limits)
- Flexible configuration per endpoint

Usage:
    from app.core.rate_limit import require_rate_limit

    # IP-based for public endpoints (e.g., login)
    @router.post('/login')
    async def login(
        data: LoginRequest,
        _: Annotated[None, Depends(require_rate_limit(5, 60, 'ip'))]
    ):
        ...

    # User-based for authenticated endpoints
    @router.get('/sessions')
    async def list_sessions(
        _: Annotated[None, Depends(require_rate_limit(100, 60, 'user'))],
        current_user: CurrentActiveUser,
    ):
        ...

    # Endpoint-based (global limit for that route)
    @router.post('/heavy-operation')
    async def process(
        _: Annotated[None, Depends(require_rate_limit(10, 60, 'endpoint'))]
    ):
        ...
"""

from typing import Literal

from fastapi import HTTPException, Request, status

from app.core.dependencies import CurrentActiveUser
from app.core.rate_limit_redis import get_rate_limit_redis

# Type for key generation strategies
KeyType = Literal['user', 'ip', 'endpoint']


def get_rate_limit_key(
    request: Request, current_user: CurrentActiveUser | None, key_type: KeyType
) -> str:
    """
    Generate a unique rate limit key based on the key type.

    Args:
        request: FastAPI request object
        current_user: Currently authenticated user (if any)
        key_type: Type of key to generate:
            - 'user': Rate limit per authenticated user
            - 'ip': Rate limit per IP address
            - 'endpoint': Rate limit per endpoint globally

    Returns:
        Unique key string for Redis

    Examples:
        get_rate_limit_key(request, user, 'user')
        # Returns: "user:123:POST:/api/v1/sessions"

        get_rate_limit_key(request, None, 'ip')
        # Returns: "ip:192.168.1.1:POST:/api/v1/auth/login"

        get_rate_limit_key(request, None, 'endpoint')
        # Returns: "endpoint:POST:/api/v1/items"
    """
    method = request.method
    path = request.url.path

    if key_type == 'user':
        if current_user is None:
            # Fallback to IP if user not authenticated
            # (shouldn't happen if dependency order is correct)
            return f'ip:{_get_client_ip(request)}:{method}:{path}'
        return f'user:{current_user.id}:{method}:{path}'

    elif key_type == 'ip':
        client_ip = _get_client_ip(request)
        return f'ip:{client_ip}:{method}:{path}'

    elif key_type == 'endpoint':
        return f'endpoint:{method}:{path}'

    else:
        raise ValueError(f'Invalid key_type: {key_type}')


def _get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Checks X-Forwarded-For and X-Real-IP headers first (for proxies),
    then falls back to direct connection IP.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    # Check proxy headers first
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first (client)
        return forwarded.split(',')[0].strip()

    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()

    # Fallback to direct connection
    if request.client:
        return request.client.host

    return 'unknown'


def require_rate_limit(
    limit: int,
    window_seconds: int,
    key_type: KeyType = 'user',
    include_headers: bool = True,
):
    """
    Factory function to create a rate limit dependency.

    This follows the same pattern as require_permission() for consistency.

    Args:
        limit: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        key_type: How to identify the rate limit:
            - 'user': Per authenticated user (requires CurrentActiveUser)
            - 'ip': Per IP address (works for public endpoints)
            - 'endpoint': Global limit for the endpoint
        include_headers: Whether to add rate limit headers to response

    Returns:
        Async dependency function for FastAPI

    Example:
        # Strict limit for login attempts
        @router.post('/login')
        async def login(
            _: Annotated[None, Depends(require_rate_limit(5, 60, 'ip'))]
        ):
            ...

        # Generous limit for authenticated reads
        @router.get('/items')
        async def list_items(
            current_user: CurrentActiveUser,
            _: Annotated[None, Depends(require_rate_limit(200, 60, 'user'))]
        ):
            ...
    """

    async def rate_limit_checker(
        request: Request,
        current_user: CurrentActiveUser | None = None,
    ) -> None:
        """
        Check rate limit for the current request.

        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        # Get Redis rate limiter
        limiter = get_rate_limit_redis()

        # Generate unique key
        rate_limit_key = get_rate_limit_key(request, current_user, key_type)

        # Check limit
        result = await limiter.check_limit(rate_limit_key, limit, window_seconds)

        # Add rate limit headers to response if requested
        if include_headers:
            request.state.rate_limit_limit = result['limit']
            request.state.rate_limit_remaining = max(
                0, result['limit'] - result['current_usage']
            )
            request.state.rate_limit_reset = (
                result['window_seconds'] if result['retry_after'] is None else result['retry_after']
            )

        # Raise exception if limit exceeded
        if not result['allowed']:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    'error': 'rate_limit_exceeded',
                    'message': f"Rate limit exceeded. Maximum {result['limit']} requests per {result['window_seconds']} seconds.",
                    'limit': result['limit'],
                    'window_seconds': result['window_seconds'],
                    'retry_after': result['retry_after'],
                },
                headers={'Retry-After': str(result['retry_after'])} if result['retry_after'] else {},
            )

    return rate_limit_checker


def require_rate_limit_with_config(config_key: str):
    """
    Factory function that reads rate limit config from settings.

    This allows centralized configuration in app/core/config.py.

    Args:
        config_key: Key to look up in settings (e.g., 'AUTH_RATE_LIMIT')

    Returns:
        Rate limit dependency function

    Example:
        # In config.py:
        AUTH_RATE_LIMIT = 5
        AUTH_RATE_WINDOW = 60

        # In router:
        @router.post('/login')
        async def login(
            _: Annotated[None, Depends(require_rate_limit_with_config('AUTH'))]
        ):
            ...
    """
    from app.core.config import settings

    async def rate_limit_checker(
        request: Request,
        current_user: CurrentActiveUser | None = None,
    ) -> None:
        # Get limit and window from settings
        limit = getattr(settings, f'{config_key}_RATE_LIMIT', settings.DEFAULT_RATE_LIMIT)
        window = getattr(
            settings,
            f'{config_key}_RATE_WINDOW_SECONDS',
            settings.DEFAULT_RATE_WINDOW_SECONDS,
        )

        # Determine key type (default to 'ip' for auth, 'user' for others)
        key_type: KeyType = 'ip' if config_key.startswith('AUTH') else 'user'

        # Use main rate limit checker
        checker = require_rate_limit(limit, window, key_type)
        return await checker(request, current_user)

    return rate_limit_checker
