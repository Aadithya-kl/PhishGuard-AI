from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class InvoiceFraudRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        html = scan.body_html.lower() if scan.body_html else ""
        combined_text = body + " " + html
        
        keywords = ["invoice attached", "unpaid invoice", "remittance advice", "payment overdue", "billing statement"]
        has_invoice_intent = False
        for kw in keywords:
            if kw in combined_text or kw in subject:
                has_invoice_intent = True
                matched_patterns.append(kw)
                break
                
        # Require attachment or external link
        has_payload = False
        if "attachment" in combined_text or "attached" in combined_text:
            has_payload = True
            matched_patterns.append("attachment_reference")
        if "<a href" in combined_text or "http" in combined_text:
            has_payload = True
            matched_patterns.append("link_present")
            
        if has_invoice_intent and has_payload:
            evidence.append("Email references an invoice and contains a payload (attachment/link)")
            
            return DetectionResult(
                detection_name="Invoice Fraud Attempt",
                category="Invoice Fraud",
                severity=DetectionSeverity.high,
                confidence=80,
                risk_contribution=35.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access")
                ],
                evidence=evidence,
                explanation="Email uses invoice or billing lures along with a link or attachment, a common technique for malware delivery or credential theft."
            )
            
        return None