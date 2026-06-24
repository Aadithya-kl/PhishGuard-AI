import httpx
from typing import Dict, Any
from loguru import logger

from app.config import settings
from app.models.ioc import IocType
from app.services.threat_intel.base import ThreatIntelProvider

class PhishTankProvider(ThreatIntelProvider):
    @property
    def name(self) -> str:
        return "PhishTank"

    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        if ioc_type != IocType.url:
            return {}

        try:
            url = "https://checkurl.phishtank.com/checkurl/"
            data = {"url": value, "format": "json"}
            
            # If we have an API key, we should provide it, but it might work without one
            if settings.PHISHTANK_API_KEY:
                data["app_key"] = settings.PHISHTANK_API_KEY
                
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=data)
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if "results" in result:
                            # It's a valid JSON response from phishtank
                            in_database = result["results"].get("in_database", False)
                            valid = result["results"].get("valid", False)
                            
                            return {
                                "is_malicious": in_database and valid,
                                "in_database": in_database,
                                "raw_data": result
                            }
                    except Exception:
                        # Sometimes PhishTank returns non-JSON or HTML on rate limits
                        pass
        except Exception as e:
            logger.error(f"PhishTank provider error: {str(e)}")
            
        return {}
