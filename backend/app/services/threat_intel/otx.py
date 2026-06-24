import httpx
from typing import Dict, Any
from loguru import logger

from app.config import settings
from app.models.ioc import IocType
from app.services.threat_intel.base import ThreatIntelProvider

class OTXProvider(ThreatIntelProvider):
    @property
    def name(self) -> str:
        return "AlienVault OTX"

    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        api_key = settings.OTX_API_KEY
        if not api_key:
            logger.warning("OTX_API_KEY is not configured.")
            return {}

        otx_type_map = {
            IocType.ip: "IPv4",
            IocType.domain: "domain",
            IocType.url: "url",
            IocType.md5: "file",
            IocType.sha1: "file",
            IocType.sha256: "file",
            IocType.email: "email"
        }

        otx_type = otx_type_map.get(ioc_type)
        if not otx_type:
            return {}

        url = f"https://otx.alienvault.com/api/v1/indicators/{otx_type}/{value}/general"
        headers = {"X-OTX-API-KEY": api_key}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    pulse_info = data.get("pulse_info", {})
                    count = pulse_info.get("count", 0)
                    
                    return {
                        "pulses": count,
                        "reputation": data.get("reputation", 0),
                        "is_malicious": count > 0,
                        "raw_data": data
                    }
                elif response.status_code == 404:
                    return {"is_malicious": False, "pulses": 0}
                else:
                    logger.warning(f"OTX API returned status {response.status_code} for {value}")
        except Exception as e:
            logger.error(f"OTX provider error: {str(e)}")
            
        return {}
