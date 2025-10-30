"""
Security Headers Middleware.

This middleware adds security headers to all HTTP responses to protect
against common web vulnerabilities.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Security headers added:
    - X-Frame-Options: Prevents clickjacking attacks
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-XSS-Protection: Enables XSS filter in older browsers
    - Strict-Transport-Security: Forces HTTPS connections (production only)
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Restricts browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # X-Frame-Options: Prevent clickjacking
        # DENY = Don't allow framing at all
        # SAMEORIGIN = Only allow framing from same origin
        response.headers['X-Frame-Options'] = 'DENY'

        # X-Content-Type-Options: Prevent MIME type sniffing
        # Forces browsers to respect declared content-type
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # X-XSS-Protection: Enable XSS filter in older browsers
        # Modern browsers use CSP instead, but this provides backwards compatibility
        # 1; mode=block = Enable filter and block page if XSS detected
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Strict-Transport-Security (HSTS): Force HTTPS
        # Only add in production (when using HTTPS)
        # max-age=31536000 = 1 year
        # includeSubDomains = Apply to all subdomains
        # Note: Only enable if using HTTPS, otherwise browsers will reject
        from app.core.config import settings

        if settings.SECURE_COOKIES:  # Indicates production/HTTPS environment
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )

        # Referrer-Policy: Control referrer information
        # strict-origin-when-cross-origin = Send full URL for same-origin,
        # only origin for cross-origin HTTPS, nothing for HTTP
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy: Restrict browser features
        # Disable potentially dangerous features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=()'
        )

        # Content-Security-Policy (CSP)
        # Note: This is a basic CSP. Adjust based on your frontend needs.
        # For API-only backends, a restrictive policy is recommended.
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        return response
