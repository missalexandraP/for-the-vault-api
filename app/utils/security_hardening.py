"""Security utilities — rate limiting, input sanitization, and security helpers."""

import re
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class RateLimiter:
    """Simple in-memory rate limiter using sliding window.

    In production, replace with Redis-based implementation.
    """

    def __init__(self):
        self._windows: Dict[str, list] = defaultdict(list)

    def check(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> Tuple[bool, int]:
        """Check if a request is within rate limits.

        Returns: (is_allowed, requests_remaining)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old entries
        self._windows[key] = [
            ts for ts in self._windows[key]
            if ts > window_start
        ]

        current_count = len(self._windows[key])
        if current_count >= max_requests:
            return False, 0

        self._windows[key].append(now)
        return True, max_requests - current_count - 1

    def get_remaining(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> int:
        """Get remaining requests for a key without consuming."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        active = [ts for ts in self._windows.get(key, []) if ts > window_start]
        return max_requests - len(active)


# Global rate limiter instance
rate_limiter = RateLimiter()


# --- Input Validation Helpers ---

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

def validate_password_strength(password: str) -> Optional[str]:
    """Validate password strength. Returns error message or None."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    if len(password) > PASSWORD_MAX_LENGTH:
        return f"Password must be at most {PASSWORD_MAX_LENGTH} characters"

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"

    # Check for at least one digit
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number"

    # Check for at least one special character
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_+\-=\[\]\\;'/~`]", password):
        return "Password must contain at least one special character"

    return None


def sanitize_string(value: str, max_length: int = 2000) -> str:
    """Sanitize a string input: strip whitespace, limit length."""
    if not value:
        return value
    return value.strip()[:max_length]


def sanitize_html(value: str) -> str:
    """Remove basic HTML tags from a string to prevent injection."""
    if not value:
        return value
    # Remove script tags and content
    value = re.sub(r'<script[^>]*?>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
    # Remove other dangerous tags
    value = re.sub(r'<[^>]*?>', '', value)
    return value


# --- Rate limiting middleware for FastAPI ---

from fastapi import Request, HTTPException, status
from app.config import settings

RATE_LIMIT_PUBLIC = 30   # requests per minute for unauthenticated
RATE_LIMIT_AUTHED = 120  # requests per minute for authenticated


async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting as middleware."""
    if settings.DEBUG:
        # Skip rate limiting in dev mode
        return await call_next(request)

    # Determine client key
    client_ip = request.client.host if request.client else "unknown"
    auth_header = request.headers.get("Authorization", "")

    # Authenticated users get higher limits
    if auth_header.startswith("Bearer "):
        key = f"auth:{auth_header[:50]}"
        max_req = RATE_LIMIT_AUTHED
    else:
        key = f"public:{client_ip}"
        max_req = RATE_LIMIT_PUBLIC

    # Apply rate limit (bypass docs/health)
    path = request.url.path
    if path in ("/health", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    is_allowed, remaining = rate_limiter.check(key, max_req)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(max_req),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(max_req)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response