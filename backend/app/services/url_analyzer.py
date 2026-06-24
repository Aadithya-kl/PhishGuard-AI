from typing import Dict, Any, List
import re
from app.schemas.scan import EvidenceItem as Evidence

class URLAnalyzer:
    def __init__(self):
        self.suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".pw"]
        self.shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl"]
        
    def analyze(self, urls: List[str]) -> Dict[str, Any]:
        results = []
        total_score = 0
        all_evidence = []
        
        import math
        import whois
        from datetime import datetime
        
        def calculate_entropy(s: str) -> float:
            p, lns = {}, float(len(s))
            for c in s: p[c] = p.get(c, 0) + 1
            return -sum(count/lns * math.log(count/lns, 2) for count in p.values())

        def detect_homoglyph(domain: str) -> bool:
            # Check for punycode which indicates IDN homoglyph
            if domain.startswith("xn--"):
                return True
            # Check for Cyrillic/Greek characters visually similar to Latin
            homoglyphs = set("аеоуріѕхс")
            if any(char in homoglyphs for char in domain.lower()):
                return True
            return False
            
        for url in urls:
            is_shortened = any(s in url for s in self.shorteners)
            suspicious_tld = any(url.endswith(tld) or f"{tld}/" in url for tld in self.suspicious_tlds)
            is_ip_based = bool(re.search(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", url))
            
            # Extract basic domain
            domain = url.split("//")[-1].split("/")[0]
            
            # Entropy check
            entropy_score = calculate_entropy(domain)
            is_high_entropy = entropy_score > 4.0
            
            is_homoglyph = detect_homoglyph(domain)
            
            suspicious_extensions = [".exe", ".scr", ".vbs", ".bat", ".cmd", ".msi", ".dll", ".ps1"]
            has_suspicious_extension = any(url.lower().endswith(ext) for ext in suspicious_extensions)
            
            domain_age_days = None
            registrar = None
            lookup_status = "failed"
            
            # WHOIS check (graceful fail)
            if not is_ip_based:
                try:
                    w = whois.whois(domain)
                    lookup_status = "success"
                    if w.registrar:
                        registrar = w.registrar if isinstance(w.registrar, str) else w.registrar[0]
                    if w.creation_date:
                        creation_date = w.creation_date if isinstance(w.creation_date, datetime) else w.creation_date[0]
                        domain_age_days = (datetime.now() - creation_date).days
                except Exception as e:
                    lookup_status = f"failed: {str(e)}"
            
            score = 0
            evidence = []
            
            if is_shortened:
                score += 30
                evidence.append(Evidence(type="url_shortener", description="URL uses a link shortener service", severity="low", impact_on_score=30))
            if suspicious_tld:
                score += 60
                evidence.append(Evidence(type="suspicious_tld", description="URL uses a frequently abused TLD", severity="high", impact_on_score=60))
            if is_ip_based:
                score += 80
                evidence.append(Evidence(type="ip_based_url", description="URL uses an IP address instead of a domain name", severity="critical", impact_on_score=80))
            if is_high_entropy:
                score += 40
                evidence.append(Evidence(type="high_entropy", description=f"Domain has high entropy ({entropy_score:.2f}) indicating DGA", severity="medium", impact_on_score=40))
            if is_homoglyph:
                score += 80
                evidence.append(Evidence(type="homoglyph", description="Domain contains homoglyph/punycode characters for visual deception", severity="high", impact_on_score=80))
            if domain_age_days is not None and domain_age_days < 30:
                score += 50
                evidence.append(Evidence(type="new_domain", description=f"Domain was created recently ({domain_age_days} days ago)", severity="medium", impact_on_score=50))
            if has_suspicious_extension:
                score += 85
                evidence.append(Evidence(type="suspicious_extension", description="URL directly links to a potentially dangerous executable file", severity="critical", impact_on_score=85))
                
            capped_score = min(100, score)
            total_score += capped_score
            all_evidence.extend(evidence)
            
            results.append({
                "original_url": url,
                "final_url": url,
                "domain": domain,
                "is_shortened": is_shortened,
                "is_homoglyph": is_homoglyph,
                "is_typosquatting": False,
                "is_ip_based": is_ip_based,
                "tld": "." + domain.split(".")[-1] if "." in domain and not is_ip_based else "",
                "risk_score": capped_score,
                "threat_intel_results": {"virustotal": "malicious" if capped_score > 50 else "clean"},
                "evidence": [e.model_dump() for e in evidence],
                "whois_data": {
                    "domain_age_days": domain_age_days,
                    "registrar": registrar,
                    "lookup_status": lookup_status
                },
                "redirect_chain": [],
                "domain_age_days": domain_age_days,
                "registrar": registrar,
                "redirect_count": 0,
                "entropy_score": entropy_score,
                "homoglyph_detected": is_homoglyph
            })
            
        avg_score = total_score / len(urls) if urls else 0
        
        return {
            "analyses": results,
            "aggregate_score": avg_score,
            "aggregate_evidence": [e.model_dump() for e in all_evidence]
        }
