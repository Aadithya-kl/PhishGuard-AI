from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class MfaFatigueRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        
        mfa_keywords = ["verification code", "authentication code", "one-time password", "otp", "login attempt", "suspicious activities"]
        has_mfa = False
        for kw in mfa_keywords:
            if kw in body or kw in subject:
                has_mfa = True
                matched_patterns.append(kw)
                
        fatigue_keywords = ["approve", "deny", "did you request this", "call support"]
        has_fatigue = False
        for kw in fatigue_keywords:
            if kw in body:
                has_fatigue = True
                matched_patterns.append(kw)
                
        # To avoid false positives on legitimate single OTPs, require both context and multiple attempts or urgency
        urgency = "multiple" in body or "suspicious" in body or "immediately" in body
        
        if has_mfa and has_fatigue and urgency:
            evidence.append("Email simulates an MFA fatigue/push spam attack by showing multiple login attempt warnings and asking the user to approve or call support.")
            return DetectionResult(
                detection_name="MFA Fatigue / Push Spam",
                category="MFA Fatigue",
                severity=DetectionSeverity.high,
                confidence=80,
                risk_contribution=35.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1621", name="Multi-Factor Authentication Request Generation", tactic="Credential Access")
                ],
                evidence=evidence,
                explanation="The email alerts the user to suspicious login attempts and attempts to coerce them into approving a fraudulent MFA prompt or calling a fake support number."
            )
            
        return None