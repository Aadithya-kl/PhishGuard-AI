import httpx
from typing import Dict, Any
from loguru import logger

from app.config import settings
from app.models.ioc import IocType
from app.services.threat_intel.base import ThreatIntelProvider

class AbuseIPDBProvider(ThreatIntelProvider):
    @property
    def name(self) -> str:
        return "AbuseIPDB"

    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        if ioc_type != IocType.ip:
            return {}

        api_key = settings.ABUSEIPDB_API_KEY
        if not api_key:
            logger.warning("ABUSEIPDB_API_KEY is not configured.")
            return {}

        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Accept": "application/json",
            "Key": api_key
        }
        params = {
            "ipAddress": value,
            "maxAgeInDays": "90"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    confidence = data.get("abuseConfidenceScore", 0)
                    
                    return {
                        "abuse_confidence_score": confidence,
                        "total_reports": data.get("totalReports", 0),
                        "is_malicious": confidence > 20,
                        "raw_data": data
                    }
                else:
                    logger.warning(f"AbuseIPDB returned status {response.status_code} for {value}")
        except Exception as e:
            logger.error(f"AbuseIPDB provider error: {str(e)}")
            
        return {}
