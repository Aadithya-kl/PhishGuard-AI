import httpx
import time
from typing import Dict, Any, Set
from loguru import logger

from app.config import settings
from app.models.ioc import IocType
from app.services.threat_intel.base import ThreatIntelProvider

class OpenPhishProvider(ThreatIntelProvider):
    def __init__(self):
        self._cache: Set[str] = set()
        self._last_fetch: float = 0.0
        self._cache_ttl: float = 3600.0  # 1 hour

    @property
    def name(self) -> str:
        return "OpenPhish"

    async def _update_cache(self):
        now = time.time()
        if now - self._last_fetch < self._cache_ttl and self._cache:
            return

        url = settings.OPENPHISH_FEED_URL
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    lines = response.text.splitlines()
                    self._cache = {line.strip() for line in lines if line.strip()}
                    self._last_fetch = now
        except Exception as e:
            logger.error(f"OpenPhish provider error updating feed: {str(e)}")

    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        if ioc_type != IocType.url:
            return {}

        await self._update_cache()

        is_malicious = value in self._cache
        return {
            "is_malicious": is_malicious,
            "in_feed": is_malicious
        }
