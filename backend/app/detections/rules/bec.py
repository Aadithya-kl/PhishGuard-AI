from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class BusinessEmailCompromiseRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        
        # 1. Urgency
        urgency_keywords = ["urgent", "immediate action required", "wire transfer", "payment instructions", "asap"]
        has_urgency = False
        for kw in urgency_keywords:
            if kw in subject or kw in body:
                has_urgency = True
                matched_patterns.append(kw)
                break
                
        # 2. Financial / Credential Request
        finance_keywords = ["wire transfer", "gift card", "invoice", "payment", "bank details", "routing number"]
        has_finance = False
        for kw in finance_keywords:
            if kw in subject or kw in body:
                has_finance = True
                matched_patterns.append(kw)
                break
                
        # 3. Sender Anomaly
        sender = scan.sender_address.lower() if scan.sender_address else ""
        
        # In a real environment, you check the domain against the company's internal domains
        # For this dataset, any free email provider sending an urgent financial request is an anomaly
        has_anomaly = False
        if "gmail" in sender or "yahoo" in sender or "hotmail" in sender:
            has_anomaly = True
            evidence.append(f"Sender uses free email provider '{sender}' for a financial request")
            matched_patterns.append("free_email_anomaly")
            
        # Bank detail update bypasses urgency requirement (Payroll fraud)
        is_payroll_fraud = "bank details" in body or "routing number" in body or "direct deposit" in body
        if is_payroll_fraud:
            has_urgency = True
            matched_patterns.append("bank_update_fraud")
        
        # All three must be present to trigger BEC to avoid false positives (like OOO with "urgent")
        if has_urgency and has_finance and has_anomaly:
            evidence.append("High urgency financial request with sender anomaly detected")
        elif "are you at your desk" in body and has_anomaly:
            evidence.append("CEO fraud conversational pattern with sender anomaly detected")
            matched_patterns.append("are you at your desk")
        else:
            return None
            
        return DetectionResult(
            detection_name="Business Email Compromise (BEC)",
            category="Business Email Compromise",
            severity=DetectionSeverity.critical,
            confidence=85,
            risk_contribution=40.0,
            matched_patterns=matched_patterns,
            mitre_mappings=[
                MitreMapping(technique_id="T1586", name="Compromise Accounts", tactic="Resource Development"),
                MitreMapping(technique_id="T1566.004", name="Spearphishing Voice", tactic="Initial Access")
            ],
            evidence=evidence,
            explanation="The email shows signs of BEC: it contains an urgent request for financial action combined with a suspicious sender address or display name mismatch."
        )