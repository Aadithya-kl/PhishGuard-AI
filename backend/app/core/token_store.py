"""Small Redis-backed key/value store for auth state.

Used for:
* refresh-token allow-list (rotation + revocation on logout)
* TOTP replay protection (a code can be used once)
* login-failure counters (account lockout)

Falls back to a process-local dictionary when Redis is unreachable so local
development still works. The fallback is NOT shared between workers, which is
why production deployments must run Redis.
"""

from __future__ import annotations

import time
from typing import Optional

from loguru import logger

from app.config import get_settings

settings = get_settings()


class _MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float]] = {}

    def _gc(self) -> None:
        now = time.time()
        for k in [k for k, (_, exp) in self._data.items() if exp and exp < now]:
            self._data.pop(k, None)

    async def set(self, key: str, value: str, ttl: int) -> None:
        self._gc()
        self._data[key] = (value, time.time() + ttl if ttl else 0)

    async def set_nx(self, key: str, value: str, ttl: int) -> bool:
        self._gc()
        if key in self._data:
            return False
        await self.set(key, value, ttl)
        return True

    async def get(self, key: str) -> Optional[str]:
        self._gc()
        item = self._data.get(key)
        return item[0] if item else None

    async def delete(self, key: str) -> int:
        return 1 if self._data.pop(key, None) is not None else 0

    async def incr(self, key: str, ttl: int) -> int:
        self._gc()
        current = int((self._data.get(key) or ("0", 0))[0]) + 1
        exp = self._data.get(key, ("", time.time() + ttl))[1]
        self._data[key] = (str(current), exp)
        return current


class TokenStore:
    def __init__(self) -> None:
        self._redis = None
        self._memory = _MemoryStore()
        self._warned = False

    async def _client(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)
            await client.ping()
            self._redis = client
            return client
        except Exception as exc:  # pragma: no cover - depends on infra
            if not self._warned:
                level = "error" if settings.is_production else "warning"
                getattr(logger, level)(f"Redis unavailable for auth token store, using in-memory fallback: {exc}")
                self._warned = True
            return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        r = await self._client()
        if r is None:
            return await self._memory.set(key, value, ttl)
        await r.set(key, value, ex=ttl)

    async def set_nx(self, key: str, value: str, ttl: int) -> bool:
        r = await self._client()
        if r is None:
            return await self._memory.set_nx(key, value, ttl)
        return bool(await r.set(key, value, ex=ttl, nx=True))

    async def get(self, key: str) -> Optional[str]:
        r = await self._client()
        if r is None:
            return await self._memory.get(key)
        return await r.get(key)

    async def pop(self, key: str) -> Optional[str]:
        """Atomically read-and-delete (used for single-use refresh tokens)."""
        r = await self._client()
        if r is None:
            value = await self._memory.get(key)
            await self._memory.delete(key)
            return value
        try:
            return await r.getdel(key)
        except Exception:  # Redis < 6.2
            pipe = r.pipeline()
            pipe.get(key)
            pipe.delete(key)
            value, _ = await pipe.execute()
            return value

    async def delete(self, key: str) -> None:
        r = await self._client()
        if r is None:
            await self._memory.delete(key)
            return
        await r.delete(key)

    async def incr(self, key: str, ttl: int) -> int:
        r = await self._client()
        if r is None:
            return await self._memory.incr(key, ttl)
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl, nx=True)
        count, _ = await pipe.execute()
        return int(count)

    async def ping(self) -> bool:
        return (await self._client()) is not None


token_store = TokenStore()
