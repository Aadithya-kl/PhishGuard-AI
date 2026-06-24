import asyncio
from typing import Dict, Any, List

from app.models.ioc import IocType, EmailIoc
from app.services.threat_intel.otx import OTXProvider
from app.services.threat_intel.abuseipdb import AbuseIPDBProvider
from app.services.threat_intel.urlhaus import URLHausProvider
from app.services.threat_intel.phishtank import PhishTankProvider
from app.services.threat_intel.openphish import OpenPhishProvider
from app.services.threat_intel.confidence_engine import ThreatConfidenceEngine

class ThreatIntelManager:
    def __init__(self):
        self.providers = [
            OTXProvider(),
            AbuseIPDBProvider(),
            URLHausProvider(),
            PhishTankProvider(),
            OpenPhishProvider()
        ]

    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        """Check a single IOC against all configured providers concurrently."""
        tasks = [provider.check_ioc(ioc_type, value) for provider in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        reputation_data = {}
        is_malicious = False
        threat_score = 0.0
        
        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                reputation_data[provider.name] = {"error": str(result), "is_malicious": False}
            elif result:  # Not empty dictionary
                reputation_data[provider.name] = result
            else:
                reputation_data[provider.name] = {"status": "unsupported_ioc_type_or_no_data", "is_malicious": False}
                
        confidence_engine = ThreatConfidenceEngine()
        confidence_result = confidence_engine.evaluate(ioc_type.value, value, reputation_data)
        
        # Override naive boolean with confidence engine verdict
        is_malicious = confidence_result["verdict"] == "malicious"
        threat_score = confidence_result["confidence"]
        
        # Include the confidence assessment in the reputation data
        reputation_data["confidence_assessment"] = confidence_result
                    
        return {
            "reputation_data": reputation_data,
            "is_malicious": is_malicious,
            "threat_score": threat_score,
            "confidence_assessment": confidence_result
        }

    async def analyze_iocs(self, iocs: List[EmailIoc]) -> Dict[str, Any]:
        """
        Analyze a list of IOCs and return the unified enrichment result format required:
        {
            "domain_reputation": {},
            "ip_reputation": {},
            "phishing_matches": {},
            "risk_indicators": []
        }
        """
        domain_reputation = {}
        ip_reputation = {}
        phishing_matches = {}
        risk_indicators = []
        
        # Analyze concurrently
        tasks = [self.check_ioc(ioc.ioc_type, ioc.value) for ioc in iocs]
        results = await asyncio.gather(*tasks)
        
        for ioc, result in zip(iocs, results):
            # Update the IOC object directly
            ioc.threat_score = result.get("threat_score", 0.0)
            ioc.reputation_data = result.get("reputation_data", {})
            
            # Populate unified response
            if ioc.ioc_type in (IocType.domain, IocType.subdomain):
                domain_reputation[ioc.value] = ioc.reputation_data
            elif ioc.ioc_type == IocType.ip:
                ip_reputation[ioc.value] = ioc.reputation_data
            elif ioc.ioc_type == IocType.url:
                phishing_matches[ioc.value] = ioc.reputation_data
                
            if result.get("is_malicious"):
                risk_indicators.append({
                    "ioc_type": ioc.ioc_type.value,
                    "value": ioc.value,
                    "reason": "Flagged as malicious by threat intelligence providers."
                })
                
        # If any dicts are empty, provide a default explicit "clean" response so they are not fully empty 
        # as requested "Do not return empty dictionaries."
        if not domain_reputation:
            domain_reputation = {"status": "no_domains_found"}
        if not ip_reputation:
            ip_reputation = {"status": "no_ips_found"}
        if not phishing_matches:
            phishing_matches = {"status": "no_urls_found"}
            
        return {
            "domain_reputation": domain_reputation,
            "ip_reputation": ip_reputation,
            "phishing_matches": phishing_matches,
            "risk_indicators": risk_indicators
        }
