"""
Redis Cache Service - Cache-aside pattern with ETags and invalidation.

Provides:
- Decorator-based caching for async functions
- ETag generation for conditional requests
- Cache invalidation by key pattern
- TTL management with jitter to prevent thundering herd
"""
import hashlib
import json
import random
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis
from fastapi import Request, Response

from app.config import get_settings

settings = get_settings()

# Redis connection pool (lazy initialization)
_redis_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis connection with connection pooling."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


def _generate_etag(data: Any) -> str:
    """Generate ETag from response data."""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(content.encode()).hexdigest()


def _add_jitter(ttl_seconds: int) -> int:
    """Add random jitter to TTL to prevent thundering herd."""
    jitter = random.randint(0, max(1, ttl_seconds // 10))
    return ttl_seconds + jitter


class CacheService:
    """
    Production-grade cache service with cache-aside pattern.

    Usage:
        cache = CacheService()

        # Simple get/set
        await cache.get("key")
        await cache.set("key", value, ttl=300)

        # Pattern invalidation
        await cache.invalidate_pattern("projects:*")

        # ETag support
        etag = cache.generate_etag(data)
    """

    def __init__(self):
        self._prefix = "portfolio:"

    def _key(self, key: str) -> str:
        """Prefix all keys to avoid collision."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value, returns None on miss."""
        r = await get_redis()
        value = await r.get(self._key(key))
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set cache value with TTL (seconds) + jitter."""
        r = await get_redis()
        serialized = json.dumps(value, default=str)
        await r.set(self._key(key), serialized, ex=_add_jitter(ttl))

    async def delete(self, key: str) -> None:
        """Delete a specific cache key."""
        r = await get_redis()
        await r.delete(self._key(key))

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        Returns count of deleted keys.

        WARNING: Uses SCAN (not KEYS) for production safety.
        """
        r = await get_redis()
        full_pattern = self._key(pattern)
        deleted = 0
        async for key in r.scan_iter(match=full_pattern, count=100):
            await r.delete(key)
            deleted += 1
        return deleted

    async def get_or_set(
        self, key: str, factory: Callable, ttl: int = 300
    ) -> Any:
        """
        Cache-aside pattern: get from cache, or compute and store.

        Args:
            key: Cache key
            factory: Async callable that produces the value on cache miss
            ttl: Time-to-live in seconds
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Cache miss — compute value
        value = await factory()
        await self.set(key, value, ttl)
        return value

    def generate_etag(self, data: Any) -> str:
        """Generate ETag for conditional request support."""
        return f'"{_generate_etag(data)}"'

    async def get_with_etag(self, key: str) -> tuple[Optional[Any], Optional[str]]:
        """Get cached value along with its ETag."""
        value = await self.get(key)
        if value is None:
            return None, None
        etag = self.generate_etag(value)
        return value, etag


def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator for caching async function results.

    Args:
        key_prefix: Prefix for the cache key (e.g., "projects:list")
        ttl: Time-to-live in seconds (default 5 minutes)
        key_builder: Optional function to build cache key from args/kwargs

    Example:
        @cached("projects:list", ttl=600)
        async def get_projects(page: int, status: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Auto-generate key from args
                key_parts = [str(a) for a in args if not hasattr(a, "__dict__")]
                key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())
                              if k not in ("db", "request", "response", "current_user")]
                suffix = ":".join(key_parts) if key_parts else "default"
                cache_key = f"{key_prefix}:{suffix}"

            cache = CacheService()
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        # Attach cache reference for manual invalidation
        wrapper.cache_key_prefix = key_prefix
        return wrapper

    return decorator


def conditional_response(request: Request, response: Response, data: Any, etag: str) -> Any:
    """
    Handle conditional requests (If-None-Match).
    Returns 304 Not Modified if ETag matches.
    """
    # Check If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        response.status_code = 304
        return None

    # Set ETag header
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=0, must-revalidate"
    return data


# Singleton instance
cache_service = CacheService()
