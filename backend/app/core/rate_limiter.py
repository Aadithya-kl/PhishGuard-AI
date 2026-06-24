"""Redis-backed sliding-window rate limiter."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from loguru import logger

from app.config import get_settings

settings = get_settings()


class RateLimiter:
    """Sliding-window rate limiter using Redis sorted sets.

    Falls back to a permissive in-memory counter when Redis is unavailable.
    """

    def __init__(self, requests_per_minute: int = 0):
        self.limit = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._memory_store: dict[str, list[float]] = {}

    async def _get_redis(self):
        """Try to get a Redis connection; return None if unavailable."""
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.ping()
            return r
        except Exception:
            return None

    async def _check_redis(self, key: str) -> bool:
        """Sliding-window check via Redis sorted set."""
        r = await self._get_redis()
        if r is None:
            return self._check_memory(key)
        try:
            now = time.time()
            window_start = now - 60.0
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, 120)
            results = await pipe.execute()
            count = results[1]
            await r.aclose()
            return count < self.limit
        except Exception:
            return True

    def _check_memory(self, key: str) -> bool:
        """In-memory fallback when Redis is unavailable."""
        now = time.time()
        window_start = now - 60.0
        timestamps = self._memory_store.get(key, [])
        timestamps = [t for t in timestamps if t > window_start]
        timestamps.append(now)
        self._memory_store[key] = timestamps
        return len(timestamps) <= self.limit

    async def __call__(self, request: Request) -> None:
        """FastAPI dependency – raises 429 when limit exceeded."""
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        allowed = await self._check_redis(key)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )


# Pre-built instances for common limits
default_limiter = RateLimiter()
scan_limiter = RateLimiter(requests_per_minute=30)
auth_limiter = RateLimiter(requests_per_minute=10)
