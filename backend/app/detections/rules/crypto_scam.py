from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class CryptoScamRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        body = scan.body_text.lower() if scan.body_text else ""
        
        crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "wallet address"]
        has_crypto = False
        for kw in crypto_keywords:
            if kw in body:
                has_crypto = True
                matched_patterns.append(kw)
                
        scam_intent = ["guaranteed return", "investment", "extortion", "compromised your", "send payment", "deposit"]
        has_intent = False
        for kw in scam_intent:
            if kw in body:
                has_intent = True
                matched_patterns.append(kw)
                
        # Regex for crypto wallet addresses (basic heuristic)
        wallet_pattern = re.compile(r'\b(?:1|3|bc1|0x)[a-zA-HJ-NP-Za-km-z0-9]{26,42}\b')
        original_body = scan.body_text if scan.body_text else ""
        wallets = wallet_pattern.findall(original_body)
        has_wallet = len(wallets) > 0
        if has_wallet:
            matched_patterns.append("crypto_wallet_regex")
            
        sender = scan.sender_address.lower() if scan.sender_address else ""
        is_internal = "company.com" in sender
            
        if has_crypto and (has_intent or has_wallet):
            if is_internal and not has_wallet and "investment" in body and "extortion" not in body:
                return None # Benign policy update
            evidence.append(f"Email mentions cryptocurrency alongside scam intent or explicit wallet addresses. Wallets found: {len(wallets)}")
            return DetectionResult(
                detection_name="Cryptocurrency Extortion / Scam",
                category="Crypto Scam",
                severity=DetectionSeverity.high,
                confidence=85,
                risk_contribution=30.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1498", name="Network Denial of Service", tactic="Impact"), # Extortion
                    MitreMapping(technique_id="T1566", name="Phishing", tactic="Initial Access")
                ],
                evidence=evidence,
                explanation="The email is attempting to extort cryptocurrency or promote a fraudulent investment scam."
            )
            
        return None