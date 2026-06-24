from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class BrandImpersonationRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        sender = scan.sender_address.lower() if scan.sender_address else ""
        display_name = scan.sender_display_name.lower() if scan.sender_display_name else ""
        
        brands = {"microsoft": "microsoft.com", "paypal": "paypal.com", "apple": "apple.com", "amazon": "amazon.com"}
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        
        for brand, real_domain in brands.items():
            # 1. Brand Mention
            has_brand_mention = brand in body or brand in subject or brand in display_name
            
            if has_brand_mention:
                # 2. Mismatch checks
                is_display_name_mismatch = (brand in display_name) and (sender_domain != real_domain)
                is_domain_mismatch = (brand in sender_domain) and (sender_domain != real_domain)
                
                # Simple homoglyph check: substituting o with 0
                homoglyph_brand = brand.replace('o', '0')
                is_homoglyph = (homoglyph_brand in sender_domain) and (homoglyph_brand != brand)
                
                if is_display_name_mismatch or is_domain_mismatch or is_homoglyph:
                    matched_patterns.append(brand)
                    
                    if is_display_name_mismatch:
                        evidence.append(f"Display name implies {brand} affiliation but domain is {sender_domain}")
                        matched_patterns.append("display_name_mismatch")
                    if is_domain_mismatch:
                        evidence.append(f"Domain {sender_domain} contains {brand} but is not the official {real_domain}")
                        matched_patterns.append("domain_mismatch")
                    if is_homoglyph:
                        evidence.append(f"Homoglyph domain detected: {sender_domain}")
                        matched_patterns.append("homoglyph_domain")
                        
                    return DetectionResult(
                        detection_name="Brand Impersonation",
                        category="Brand Impersonation",
                        severity=DetectionSeverity.high,
                        confidence=90,
                        risk_contribution=35.0,
                        matched_patterns=matched_patterns,
                        mitre_mappings=[
                            MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access"),
                            MitreMapping(technique_id="T1036", name="Masquerading", tactic="Defense Evasion")
                        ],
                        evidence=evidence,
                        explanation=f"The email attempts to impersonate {brand} by mentioning the brand while using an unofficial or deceptive sender domain."
                    )
        
        return None