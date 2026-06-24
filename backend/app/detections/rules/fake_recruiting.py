from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class FakeRecruitingRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        
        recruit_keywords = ["job offer", "interview request", "remote work", "work from home", "hiring", "recruitment"]
        has_recruit = False
        for kw in recruit_keywords:
            if kw in body or kw in subject:
                has_recruit = True
                matched_patterns.append(kw)
                
        scam_intent = ["ssn", "social security", "bank details", "upfront payment", "deposit", "western union", "wire", "visa sponsorship fee"]
        has_intent = False
        for kw in scam_intent:
            if kw in body:
                has_intent = True
                matched_patterns.append(kw)
                
        # Fake recruiting usually comes from free email providers rather than corporate domains
        sender = scan.sender_address.lower() if scan.sender_address else ""
        is_free_email = "gmail.com" in sender or "yahoo.com" in sender or "hotmail.com" in sender
        
        if has_recruit and has_intent and is_free_email:
            evidence.append(f"Email contains recruitment lure combined with suspicious data/payment request from a free email provider ({sender})")
            return DetectionResult(
                detection_name="Fake Recruiting Campaign",
                category="Fake Recruiting",
                severity=DetectionSeverity.medium,
                confidence=85,
                risk_contribution=25.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1566.002", name="Spearphishing Link", tactic="Initial Access")
                ],
                evidence=evidence,
                explanation="The email is a fraudulent job offer attempting to collect sensitive personal information or upfront payment."
            )
            
        return None