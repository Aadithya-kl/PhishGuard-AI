from typing import Dict, Any, List
from datetime import datetime
import json

class ThreatConfidenceEngine:
    def evaluate(self, ioc_type: str, value: str, provider_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates threat intel results across multiple providers to determine a true confidence score.
        """
        confidence = 0.0
        sources = []
        evidence = []
        malicious_hits = 0
        total_providers_checked = 0
        
        pulse_count = 0
        recent_pulses = 0
        
        for provider_name, data in provider_results.items():
            if "status" in data and "unsupported" in data["status"]:
                continue
            if "error" in data:
                continue
                
            total_providers_checked += 1
            
            if data.get("is_malicious", False):
                malicious_hits += 1
                sources.append(provider_name)
                
                # Specialized logic for AlienVault OTX
                if provider_name == "AlienVault OTX":
                    pulses = data.get("pulses", 0)
                    pulse_count = pulses
                    raw_data = data.get("raw_data", {})
                    pulse_info = raw_data.get("pulse_info", {})
                    pulse_list = pulse_info.get("pulses", [])
                    
                    for p in pulse_list:
                        created_str = p.get("created", "")
                        if created_str:
                            try:
                                # OTX dates are ISO 8601 like "2023-01-15T23:03:27.378000"
                                dt = datetime.fromisoformat(created_str.split(".")[0])
                                days_old = (datetime.utcnow() - dt).days
                                if days_old < 90:
                                    recent_pulses += 1
                            except Exception:
                                pass
                                
                    if pulses > 0:
                        evidence.append(f"AlienVault OTX reported {pulses} pulses ({recent_pulses} recent within 90 days).")
                else:
                    evidence.append(f"{provider_name} reported this IOC as malicious.")
        
        # Calculate confidence based on new calibrated bands
        if malicious_hits > 0:
            if malicious_hits == 1:
                # Single provider
                if pulse_count > 0:
                    # OTX Only
                    if pulse_count == 1:
                        confidence = 25.0
                        evidence.append("Single threat intelligence pulse found. Weak evidence.")
                    elif recent_pulses > 1:
                        confidence = 70.0
                        evidence.append("Multiple recent pulses found. High confidence of active threat.")
                    elif pulse_count > 1:
                        confidence = 50.0
                        evidence.append(f"Multiple pulses ({pulse_count}) found across history. Suspicious.")
                else:
                    # Non-OTX single provider
                    confidence = 45.0
            else:
                # Cross-provider agreement (2 or more)
                confidence = 65.0
                if malicious_hits > 2:
                    confidence = 90.0
                evidence.append(f"High confidence: {malicious_hits} different providers agree on malicious status.")
                
            # Domain age and historical rep can be passed in later or retrieved if needed.
            
        confidence = min(100.0, confidence)
        
        verdict = "safe"
        if confidence >= 70:
            verdict = "malicious"
        elif confidence >= 40:
            verdict = "suspicious"
            
        if total_providers_checked == 0:
            verdict = "unknown"
            evidence.append("No threat intelligence providers returned data for this IOC.")
            
        return {
            "confidence": confidence,
            "sources": sources,
            "provider_count": total_providers_checked,
            "verdict": verdict,
            "evidence": evidence
        }
