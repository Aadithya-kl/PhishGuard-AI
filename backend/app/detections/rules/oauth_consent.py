from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class OAuthConsentRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        body = scan.body_text.lower() if scan.body_text else ""
        html = scan.body_html.lower() if scan.body_html else ""
        combined_text = body + " " + html
        
        oauth_endpoints = ["login.microsoftonline.com/common/oauth2", "accounts.google.com/o/oauth2"]
        has_oauth = False
        for endpoint in oauth_endpoints:
            if endpoint in combined_text:
                has_oauth = True
                matched_patterns.append(endpoint)
                evidence.append(f"Contains link to known OAuth authorization endpoint: {endpoint}")
                
        # Require a suspicious prompt or missing context
        suspicious_contexts = ["client_id=", "response_type=code", "prompt=consent"]
        has_context = False
        for ctx in suspicious_contexts:
            if ctx in combined_text:
                has_context = True
                matched_patterns.append(ctx)
                
        if has_oauth and has_context:
            return DetectionResult(
                detection_name="OAuth Consent Phishing",
                category="OAuth Consent",
                severity=DetectionSeverity.high,
                confidence=85,
                risk_contribution=40.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1528", name="Steal Application Access Token", tactic="Credential Access")
                ],
                evidence=evidence,
                explanation="Email contains a link to an OAuth authorization endpoint requesting consent, commonly used to bypass MFA by granting token access to a malicious app."
            )
            
        return None