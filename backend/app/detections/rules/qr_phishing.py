from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class QrPhishingRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        body = scan.body_text.lower() if scan.body_text else ""
        html = scan.body_html.lower() if scan.body_html else ""
        
        combined_text = body + " " + html
        
        has_qr_mention = "qr code" in combined_text or "scan the code" in combined_text
        has_image = "<img" in combined_text or "cid:" in combined_text
        
        login_intent = "login" in combined_text or "verify" in combined_text or "authenticate" in combined_text or "2fa" in combined_text
        
        if has_qr_mention:
            matched_patterns.append("qr_mention")
        if has_image:
            matched_patterns.append("image_tag")
            
        sender = scan.sender_address.lower() if scan.sender_address else ""
        is_internal = "company.com" in sender
            
        if has_qr_mention and has_image:
            if is_internal and not login_intent:
                return None # Benign internal QR code for building access etc
            evidence.append("Mentions scanning a QR code and contains an embedded image")
            return DetectionResult(
                detection_name="QR Code Phishing (Quishing)",
                category="QR Phishing",
                severity=DetectionSeverity.high,
                confidence=85,
                risk_contribution=35.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access")
                ],
                evidence=evidence,
                explanation="Email uses a QR code as a potential payload to evade traditional URL filtering."
            )
            
        return None