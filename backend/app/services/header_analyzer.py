from typing import Dict, Any, List
from app.schemas.scan import EvidenceItem as Evidence
import re

class HeaderAnalyzer:
    def __init__(self):
        pass

    def analyze(self, parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        evidence = []
        score = 100
        
        spf_pass = None
        dkim_pass = None
        dmarc_pass = None
        spf_result = "none"
        dkim_result = "none"
        dmarc_result = "none"
        sender_spoofed = False
        display_name_impersonation = False
        domain_mismatch = False
        
        headers = parsed_email.get("parsed_headers", {})
        sender = parsed_email.get("sender_address", "").lower()
        sender_name = parsed_email.get("sender_display_name", "").lower()
        reply_to = (parsed_email.get("reply_to") or "").lower()
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        reply_to_domain = reply_to.split("@")[-1] if "@" in reply_to else ""
        
        auth_results = ""
        # Handle cases where header might be a list or a string
        auth_header = headers.get("authentication-results", headers.get("Authentication-Results", ""))
        if isinstance(auth_header, list):
            auth_results = " ".join(auth_header).lower()
        else:
            auth_results = str(auth_header).lower()

        if "spf=pass" in auth_results:
            spf_pass = True
            spf_result = "pass"
        elif "spf=fail" in auth_results or "spf=softfail" in auth_results:
            spf_pass = False
            spf_result = "fail"
            score -= 20
            evidence.append({
                "finding": "SPF Failure",
                "severity": "medium",
                "confidence": 1.0,
                "evidence": ["SPF record check failed or softfail"]
            })

        if "dkim=pass" in auth_results:
            dkim_pass = True
            dkim_result = "pass"
        elif "dkim=fail" in auth_results:
            dkim_pass = False
            dkim_result = "fail"
            score -= 20
            evidence.append({
                "finding": "DKIM Failure",
                "severity": "medium",
                "confidence": 1.0,
                "evidence": ["DKIM signature invalid"]
            })
            
        if "dmarc=pass" in auth_results:
            dmarc_pass = True
            dmarc_result = "pass"
        elif "dmarc=fail" in auth_results:
            dmarc_pass = False
            dmarc_result = "fail"
            score -= 30
            evidence.append({
                "finding": "DMARC Failure",
                "severity": "high",
                "confidence": 1.0,
                "evidence": ["DMARC policy failed"]
            })

        # Check for Return-Path mismatch
        return_path = (parsed_email.get("return_path") or "").lower()
        return_path_domain = return_path.split("@")[-1].strip("<>") if "@" in return_path else ""
        
        if sender_domain and return_path_domain and sender_domain != return_path_domain:
            domain_mismatch = True
            score -= 40
            evidence.append({
                "finding": "Domain Alignment Failure",
                "severity": "high",
                "confidence": 0.9,
                "evidence": [f"From domain ({sender_domain}) does not match Return-Path domain ({return_path_domain})"]
            })
            
        if sender_domain and reply_to_domain and sender_domain != reply_to_domain:
            domain_mismatch = True
            score -= 30
            evidence.append({
                "finding": "Reply-To Mismatch",
                "severity": "high",
                "confidence": 0.85,
                "evidence": [f"From domain ({sender_domain}) does not match Reply-To domain ({reply_to_domain})"]
            })

        # Display Name Impersonation (e.g. "PayPal Security" <hacker@evil.com>)
        if sender_name and sender_domain:
            # If the display name contains a major brand but domain is different
            brands = ["paypal", "microsoft", "google", "apple", "amazon", "netflix", "facebook", "linkedin", "bank", "security", "admin", "support", "billing"]
            name_lower = sender_name.lower()
            if any(brand in name_lower for brand in brands):
                if not any(brand in sender_domain for brand in brands):
                    display_name_impersonation = True
                    score -= 50
                    evidence.append({
                        "finding": "Display Name Impersonation",
                        "severity": "critical",
                        "confidence": 0.9,
                        "evidence": [f"Display name '{sender_name}' claims high-profile identity but domain is '{sender_domain}'"]
                    })
            
        return {
            "spf_pass": spf_pass,
            "spf_result": spf_result,
            "dkim_pass": dkim_pass,
            "dkim_result": dkim_result,
            "dmarc_pass": dmarc_pass,
            "dmarc_result": dmarc_result,
            "sender_spoofed": sender_spoofed,
            "display_name_impersonation": display_name_impersonation,
            "domain_mismatch": domain_mismatch,
            "relay_chain": [],
            "forged_headers": [],
            "bec_indicators": [],
            "trust_score": max(0, score),
            "evidence": evidence
        }
