import httpx
from typing import Dict, Any
from loguru import logger

from app.models.ioc import IocType
from app.services.threat_intel.base import ThreatIntelProvider

class URLHausProvider(ThreatIntelProvider):
    @property
    def name(self) -> str:
        return "URLhaus"

    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        if ioc_type not in (IocType.url, IocType.domain, IocType.ip):
            return {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if ioc_type == IocType.url:
                    response = await client.post("https://urlhaus-api.abuse.ch/v1/url/", data={"url": value})
                else:
                    response = await client.post("https://urlhaus-api.abuse.ch/v1/host/", data={"host": value})
                    
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("query_status", "no_results")
                    
                    if status == "ok":
                        return {
                            "is_malicious": True,
                            "threat_type": data.get("threat", "unknown"),
                            "status": data.get("url_status", "unknown"),
                            "raw_data": data
                        }
                    else:
                        return {"is_malicious": False}
        except Exception as e:
            logger.error(f"URLhaus provider error: {str(e)}")
            
        return {}
