import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

settings = get_settings()

# In-memory rate limit store (use Redis in production for multi-instance)
# Format: { "ip:endpoint": [timestamp1, timestamp2, ...] }
_rate_limit_store: dict = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    
    Different limits for different endpoints:
    - /auth/login: 5 per minute
    - /auth/signup: 3 per hour (180 per 3600s)
    - /contact: 3 per hour
    - General: 60 per minute
    """

    # Endpoint-specific limits: (max_requests, window_seconds)
    ENDPOINT_LIMITS = {
        "/api/v1/auth/login": (5, 60),
        "/api/v1/auth/signup": (3, 3600),
        "/api/v1/contact": (3, 3600),
    }
    DEFAULT_LIMIT = (60, 60)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method

        # Only rate limit mutation endpoints and auth
        if method == "GET" and "/auth/" not in path:
            return await call_next(request)

        # Get limit for this endpoint
        max_requests, window = self._get_limit(path)

        # Check rate limit
        key = f"{client_ip}:{path}"
        now = time.time()

        if key not in _rate_limit_store:
            _rate_limit_store[key] = []

        # Remove expired timestamps
        _rate_limit_store[key] = [
            ts for ts in _rate_limit_store[key] if now - ts < window
        ]

        if len(_rate_limit_store[key]) >= max_requests:
            # Calculate retry time
            oldest = _rate_limit_store[key][0]
            retry_after = int(window - (now - oldest))

            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Try again in {retry_after} seconds."
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Record this request
        _rate_limit_store[key].append(now)

        # Process request and add rate limit headers
        response = await call_next(request)
        remaining = max_requests - len(_rate_limit_store[key])
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response

    def _get_limit(self, path: str) -> tuple:
        """Get rate limit for the given path."""
        for endpoint, limit in self.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint):
                return limit
        return self.DEFAULT_LIMIT

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP, considering proxies."""
        # Check X-Forwarded-For header (set by reverse proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
