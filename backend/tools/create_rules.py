import os

RULES_DIR = r"c:\Users\loges\cybersecurity\backend\app\detections\rules"

rules = {
    "credential_harvesting.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class CredentialHarvestingRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        
        keywords = ["verify your account", "login to continue", "update your billing", "password expiry"]
        for kw in keywords:
            if kw in body:
                evidence.append(f"Found credential harvesting keyword: '{kw}'")
                
        # Also check for forms in HTML
        html = scan.body_html.lower() if scan.body_html else ""
        if "<form" in html and "password" in html:
            evidence.append("Found HTML form requesting password")
            
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Credential Harvesting Attempt",
            category="Credential Harvesting",
            severity=DetectionSeverity.high,
            confidence=85,
            risk_contribution=30.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1566.002", name="Spearphishing Link", tactic="Initial Access"),
                MitreMapping(technique_id="T1040", name="Network Sniffing", tactic="Credential Access") # example
            ],
            evidence=evidence,
            explanation="The email contains urgent requests for account verification along with links or forms designed to harvest credentials."
        )
""",
    "bec.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class BusinessEmailCompromiseRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        
        urgency = ["urgent", "immediate action required", "wire transfer", "payment instructions"]
        for kw in urgency:
            if kw in subject or kw in body:
                evidence.append(f"High urgency BEC keyword found: '{kw}'")
                
        # CEO fraud pattern
        if "are you at your desk" in body or "i need a favor" in body:
            evidence.append("Common CEO fraud conversational pattern detected")
            
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Business Email Compromise (BEC)",
            category="Business Email Compromise",
            severity=DetectionSeverity.critical,
            confidence=80,
            risk_contribution=40.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1586", name="Compromise Accounts", tactic="Resource Development"),
                MitreMapping(technique_id="T1566.004", name="Spearphishing Voice", tactic="Initial Access")
            ],
            evidence=evidence,
            explanation="This email matches patterns commonly used in Business Email Compromise, such as CEO fraud, urgent wire transfer requests, or sudden payment instruction changes."
        )
""",
    "invoice_fraud.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class InvoiceFraudRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        
        keywords = ["overdue invoice", "remittance advice", "payment attached", "unpaid invoice"]
        for kw in keywords:
            if kw in subject or kw in body:
                evidence.append(f"Invoice fraud keyword found: '{kw}'")
                
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Invoice Fraud Attempt",
            category="Invoice Fraud",
            severity=DetectionSeverity.medium,
            confidence=75,
            risk_contribution=25.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access")
            ],
            evidence=evidence,
            explanation="The email attempts to pressure the user into opening an 'overdue' invoice or processing a payment."
        )
""",
    "malware_delivery.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class MalwareDeliveryRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        
        # In a real app we check the attachment types
        # But we don't have attachments fully mocked here, we can check for suspicious extensions in body or subject
        body = scan.body_text.lower() if scan.body_text else ""
        
        suspicious_exts = [".exe", ".iso", ".vbs", ".js", ".scr", ".bat"]
        for ext in suspicious_exts:
            if ext in body:
                evidence.append(f"Suspicious file extension mentioned in body: '{ext}'")
                
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Malware Delivery",
            category="Malware Delivery",
            severity=DetectionSeverity.critical,
            confidence=90,
            risk_contribution=45.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1566.001", name="Spearphishing Attachment", tactic="Initial Access"),
                MitreMapping(technique_id="T1204.002", name="Malicious File", tactic="Execution")
            ],
            evidence=evidence,
            explanation="This email appears to distribute an executable payload commonly used for initial access and execution."
        )
""",
    "qr_phishing.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class QRPhishingRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        html = scan.body_html.lower() if scan.body_html else ""
        
        if "scan the qr code" in body or "qr code attached" in body:
            evidence.append("Explicit mention of QR code scanning")
            
        if "data:image/png;base64" in html and "scan" in body:
            evidence.append("Base64 inline image with scanning instructions (Quishing)")
            
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="QR Code Phishing (Quishing)",
            category="QR Phishing",
            severity=DetectionSeverity.high,
            confidence=85,
            risk_contribution=35.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access")
            ],
            evidence=evidence,
            explanation="The email attempts to bypass secure email gateways by burying a malicious link inside a QR code."
        )
""",
    "oauth_consent.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class OAuthConsentRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        
        keywords = ["grant access", "needs permission to access", "authorize app", "connect to your account"]
        for kw in keywords:
            if kw in body:
                evidence.append(f"OAuth consent grant keyword found: '{kw}'")
                
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="OAuth Consent Phishing",
            category="OAuth Consent",
            severity=DetectionSeverity.high,
            confidence=80,
            risk_contribution=35.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1528", name="Steal Application Access Token", tactic="Credential Access")
            ],
            evidence=evidence,
            explanation="This email is soliciting an OAuth authorization grant, which could give an attacker persistent access to the user's account."
        )
""",
    "mfa_fatigue.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class MFAFatigueRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        subject = scan.subject.lower() if scan.subject else ""
        
        if "approve sign-in" in body or "approve the request on your microsoft authenticator app" in body:
            evidence.append("MFA approval request found in body")
            
        if "unusual sign-in activity" in subject and "approve" in body:
            evidence.append("Unusual sign-in paired with approval request")
            
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="MFA Fatigue / Push Spam",
            category="MFA Fatigue",
            severity=DetectionSeverity.high,
            confidence=95,
            risk_contribution=30.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1621", name="Multi-Factor Authentication Request Generation", tactic="Credential Access")
            ],
            evidence=evidence,
            explanation="The email is attempting to trick the user into approving a fraudulent MFA push notification."
        )
""",
    "crypto_scam.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class CryptoScamRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        
        keywords = ["bitcoin", "ethereum", "crypto wallet", "seed phrase", "giveaway"]
        for kw in keywords:
            if kw in body:
                evidence.append(f"Cryptocurrency scam keyword found: '{kw}'")
                
        # Basic regex for a bitcoin address pattern in text
        if re.search(r'\\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\\b', body):
            evidence.append("Potential Bitcoin wallet address found in body")
            
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Cryptocurrency Extortion / Scam",
            category="Cryptocurrency Scam",
            severity=DetectionSeverity.medium,
            confidence=85,
            risk_contribution=20.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1498", name="Network Denial of Service", tactic="Impact"), # Extortion
                MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access")
            ],
            evidence=evidence,
            explanation="The email contains requests for cryptocurrency payments or attempts to steal crypto wallet credentials."
        )
""",
    "fake_recruiting.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping

class FakeRecruitingRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        body = scan.body_text.lower() if scan.body_text else ""
        
        keywords = ["job offer", "remote position", "work from home", "salary"]
        matches = [kw for kw in keywords if kw in body]
        
        if len(matches) >= 2 and ("kindly" in body or "whatsapp" in body or "telegram" in body):
            evidence.append(f"Fake recruiting pattern found with keywords: {matches}")
            
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Fake Recruiting Campaign",
            category="Fake Recruiting",
            severity=DetectionSeverity.low,
            confidence=70,
            risk_contribution=15.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1566.002", name="Spearphishing Link", tactic="Initial Access")
            ],
            evidence=evidence,
            explanation="The email exhibits patterns of fake job offers designed to steal PII or solicit advance fee fraud."
        )
""",
    "brand_impersonation.py": """
from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class BrandImpersonationRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        sender = scan.sender_address.lower() if scan.sender_address else ""
        
        # Simple domain checks, in reality we'd use a large list or fuzzy matching
        brands = {"microsoft": "microsoft.com", "paypal": "paypal.com", "apple": "apple.com", "amazon": "amazon.com"}
        
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        
        for brand, real_domain in brands.items():
            if brand in sender and sender_domain != real_domain:
                evidence.append(f"Sender {sender} impersonates '{brand}' but uses domain '{sender_domain}'")
                
        if not evidence:
            return None
            
        return DetectionResult(
            detection_name="Brand Impersonation",
            category="Brand Impersonation",
            severity=DetectionSeverity.high,
            confidence=95,
            risk_contribution=15.0,
            mitre_mappings=[
                MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access"),
                MitreMapping(technique_id="T1036", name="Masquerading", tactic="Defense Evasion")
            ],
            evidence=evidence,
            explanation="The sender address or display name attempts to mimic a well-known brand but originates from an unaffiliated domain."
        )
"""
}

for filename, content in rules.items():
    path = os.path.join(RULES_DIR, filename)
    with open(path, "w") as f:
        f.write(content.strip())
    print(f"Created {filename}")
