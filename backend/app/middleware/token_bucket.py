"""
Token Bucket Rate Limiter with Redis backing.

Replaces the basic sliding window algorithm with a production-grade token bucket
that supports:
- Per-endpoint configurable rates
- Burst allowance (bucket capacity > refill rate)
- Redis-backed for multi-instance deployments
- Graceful degradation (falls back to in-memory if Redis unavailable)
- Detailed rate limit headers (X-RateLimit-*)

Algorithm:
    Each client gets a "bucket" of tokens. Each request consumes one token.
    Tokens refill at a constant rate. If bucket is empty → 429.
    
    Bucket capacity allows bursts (e.g., capacity=20, refill=10/min means
    you can burst 20 requests instantly, then sustain 10/min).
"""
import time
import asyncio
from typing import Optional
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.observability import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitPolicy:
    """Configuration for a rate limit policy."""
    capacity: int  # Maximum tokens (burst size)
    refill_rate: float  # Tokens added per second
    
    @property
    def refill_interval(self) -> float:
        """Seconds between each token refill."""
        return 1.0 / self.refill_rate if self.refill_rate > 0 else float('inf')


# ─── Rate Limit Policies ────────────────────────────────────────────────────

# Endpoint-specific policies: path_prefix → policy
POLICIES: dict[str, RateLimitPolicy] = {
    # Auth endpoints — strict limits to prevent brute force
    "/api/v1/auth/login": RateLimitPolicy(capacity=5, refill_rate=5/60),  # 5 burst, 5/min sustained
    "/api/v1/auth/signup": RateLimitPolicy(capacity=3, refill_rate=3/3600),  # 3 burst, 3/hour
    "/api/v1/auth/refresh": RateLimitPolicy(capacity=10, refill_rate=10/60),  # 10/min
    
    # Contact — prevent spam
    "/api/v1/contact": RateLimitPolicy(capacity=3, refill_rate=3/3600),  # 3/hour
    
    # Search — moderate limits
    "/api/v1/search": RateLimitPolicy(capacity=30, refill_rate=30/60),  # 30/min with burst
    
    # Admin endpoints — more generous
    "/api/v1/projects": RateLimitPolicy(capacity=30, refill_rate=20/60),  # 30 burst, 20/min
    "/api/v1/blog": RateLimitPolicy(capacity=30, refill_rate=20/60),
    
    # WebSocket — initial connection rate
    "/ws/": RateLimitPolicy(capacity=5, refill_rate=5/60),
}

# Default policy for unmatched endpoints
DEFAULT_POLICY = RateLimitPolicy(capacity=60, refill_rate=60/60)  # 60/min with 60 burst


class TokenBucket:
    """
    In-memory token bucket implementation.
    Used as fallback when Redis is unavailable.
    """
    
    def __init__(self, policy: RateLimitPolicy):
        self.policy = policy
        self.tokens: float = policy.capacity
        self.last_refill: float = time.time()
    
    def consume(self) -> tuple[bool, float, int]:
        """
        Try to consume a token.
        Returns: (allowed, tokens_remaining, retry_after_seconds)
        """
        now = time.time()
        
        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        refill_amount = elapsed * self.policy.refill_rate
        self.tokens = min(self.policy.capacity, self.tokens + refill_amount)
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True, self.tokens, 0
        else:
            # Calculate time until next token
            deficit = 1 - self.tokens
            retry_after = deficit / self.policy.refill_rate if self.policy.refill_rate > 0 else 60
            return False, 0, int(retry_after) + 1


class TokenBucketRateLimiter(BaseHTTPMiddleware):
    """
    Production-grade token bucket rate limiter.
    
    Features:
    - Redis-backed with Lua script for atomic token operations
    - Falls back to in-memory buckets if Redis unavailable
    - Per-IP, per-endpoint rate limiting
    - Configurable policies per endpoint
    - Standard rate limit headers
    - Skip list for internal/health endpoints
    """
    
    # Lua script for atomic token bucket operation in Redis
    # This runs atomically — no race conditions between check and consume
    LUA_TOKEN_BUCKET = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    
    -- Get current bucket state
    local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
    local tokens = tonumber(bucket[1])
    local last_refill = tonumber(bucket[2])
    
    -- Initialize if bucket doesn't exist
    if tokens == nil then
        tokens = capacity
        last_refill = now
    end
    
    -- Refill tokens based on elapsed time
    local elapsed = now - last_refill
    local refill_amount = elapsed * refill_rate
    tokens = math.min(capacity, tokens + refill_amount)
    
    -- Try to consume a token
    local allowed = 0
    if tokens >= 1 then
        tokens = tokens - 1
        allowed = 1
    end
    
    -- Save state
    redis.call('HMSET', key, 'tokens', tostring(tokens), 'last_refill', tostring(now))
    -- Set TTL to auto-cleanup idle buckets (2x the time to refill from empty)
    local ttl = math.ceil(capacity / refill_rate) * 2
    if ttl < 60 then ttl = 60 end
    redis.call('EXPIRE', key, ttl)
    
    -- Return: allowed (0/1), remaining tokens, retry_after (seconds until next token)
    local retry_after = 0
    if allowed == 0 then
        local deficit = 1 - tokens
        retry_after = math.ceil(deficit / refill_rate)
    end
    
    return {allowed, math.floor(tokens), retry_after}
    """
    
    SKIP_PATHS = {"/health", "/", "/docs", "/redoc", "/api/openapi.json"}
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._local_buckets: dict[str, TokenBucket] = {}
        self._lua_sha: Optional[str] = None
        self._cleanup_counter = 0
    
    async def dispatch(self, request: Request, call_next):
        # Skip non-rate-limited paths
        path = request.url.path
        if path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Only rate limit mutations + auth (let GETs through mostly)
        method = request.method
        if method == "GET" and not any(p in path for p in ["/auth/", "/search", "/ws/"]):
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Get policy for this endpoint
        policy = self._get_policy(path)
        
        # Build rate limit key
        bucket_key = f"ratelimit:{client_ip}:{self._normalize_path(path)}"
        
        # Try Redis first, fall back to local
        allowed, remaining, retry_after = await self._check_rate_limit(
            bucket_key, policy
        )
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                path=path,
                policy_capacity=policy.capacity,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limit": policy.capacity,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(policy.capacity),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(policy.capacity)
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(remaining)))
        
        return response
    
    async def _check_rate_limit(
        self, key: str, policy: RateLimitPolicy
    ) -> tuple[bool, float, int]:
        """Check rate limit via Redis (primary) or local fallback."""
        try:
            from app.services.cache import cache_service
            
            if cache_service._redis is None:
                raise RuntimeError("Redis not connected")
            
            redis = cache_service._redis
            
            # Load Lua script if not cached
            if self._lua_sha is None:
                self._lua_sha = await redis.script_load(self.LUA_TOKEN_BUCKET)
            
            # Execute atomic token bucket check
            result = await redis.evalsha(
                self._lua_sha,
                1,  # number of keys
                key,  # KEYS[1]
                str(policy.capacity),  # ARGV[1]
                str(policy.refill_rate),  # ARGV[2]
                str(time.time()),  # ARGV[3]
            )
            
            allowed = bool(result[0])
            remaining = float(result[1])
            retry_after = int(result[2])
            
            return allowed, remaining, retry_after
            
        except Exception:
            # Redis unavailable — fall back to local token bucket
            return self._check_local(key, policy)
    
    def _check_local(self, key: str, policy: RateLimitPolicy) -> tuple[bool, float, int]:
        """In-memory token bucket fallback."""
        # Periodic cleanup of stale buckets
        self._cleanup_counter += 1
        if self._cleanup_counter >= 1000:
            self._cleanup_local_buckets()
            self._cleanup_counter = 0
        
        if key not in self._local_buckets:
            self._local_buckets[key] = TokenBucket(policy)
        
        bucket = self._local_buckets[key]
        return bucket.consume()
    
    def _cleanup_local_buckets(self):
        """Remove stale buckets to prevent memory leaks."""
        now = time.time()
        stale_keys = [
            k for k, v in self._local_buckets.items()
            if now - v.last_refill > 3600  # Idle for 1 hour
        ]
        for key in stale_keys:
            del self._local_buckets[key]
    
    def _get_policy(self, path: str) -> RateLimitPolicy:
        """Match path to rate limit policy."""
        for prefix, policy in POLICIES.items():
            if path.startswith(prefix):
                return policy
        return DEFAULT_POLICY
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for rate limit key (group dynamic segments)."""
        # Group all paths under their API prefix
        parts = path.split("/")
        # Keep first 4 segments: /api/v1/resource/action
        return "/".join(parts[:5])
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"
