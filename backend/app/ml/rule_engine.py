import re
import json
from typing import Dict, Any, List
from app.schemas.scan import EvidenceItem as Evidence

class RuleMatch:
    def __init__(self, rule_id: str, category: str, description: str, matched_text: str, confidence: float):
        self.rule_id = rule_id
        self.category = category
        self.description = description
        self.matched_text = matched_text
        self.confidence = confidence

class RuleEngine:
    def __init__(self):
        self.rules = {
            "URGENCY": [
                (r"(?i)\b(immediate action required)\b", 0.9),
                (r"(?i)\b(account suspended)\b", 0.8),
                (r"(?i)\b(verify within 24 hours)\b", 0.85),
                (r"(?i)\b(action needed)\b", 0.6),
                (r"(?i)\b(final notice)\b", 0.75),
                (r"(?i)\b(your account will be closed)\b", 0.9)
            ],
            "FEAR": [
                (r"(?i)\b(unauthorized access)\b", 0.8),
                (r"(?i)\b(security breach)\b", 0.85),
                (r"(?i)\b(suspicious activity)\b", 0.7),
                (r"(?i)\b(has been compromised)\b", 0.85)
            ],
            "CREDENTIAL_HARVESTING": [
                (r"(?i)\b(update your password)\b", 0.7),
                (r"(?i)\b(confirm your identity)\b", 0.75),
                (r"(?i)\b(verify your account)\b", 0.8),
                (r"(?i)\b(log in to continue)\b", 0.6)
            ],
            "FINANCIAL": [
                (r"(?i)\b(wire transfer)\b", 0.65),
                (r"(?i)\b(invoice attached)\b", 0.6),
                (r"(?i)\b(payment required)\b", 0.7),
                (r"(?i)\b(overdue payment)\b", 0.65)
            ],
            "IMPERSONATION": [
                (r"(?i)\b(CEO)\b", 0.5),
                (r"(?i)\b(IT department)\b", 0.6),
                (r"(?i)\b(help desk)\b", 0.55),
                (r"(?i)\b(support team)\b", 0.4)
            ]
        }

    def analyze(self, text: str) -> List[RuleMatch]:
        matches = []
        if not text:
            return matches
            
        for category, patterns in self.rules.items():
            for i, (pattern, confidence) in enumerate(patterns):
                for match in re.finditer(pattern, text):
                    rule_match = RuleMatch(
                        rule_id=f"RULE_{category}_{i}",
                        category=category,
                        description=f"Detected {category.lower()} pattern",
                        matched_text=match.group(0),
                        confidence=confidence
                    )
                    matches.append(rule_match)
        return matches
        
    def generate_evidence(self, matches: List[RuleMatch]) -> List[Evidence]:
        evidence_list = []
        for match in matches:
            severity = "medium"
            if match.confidence > 0.8:
                severity = "high"
                
            evidence_list.append(Evidence(
                type="social_engineering_rule",
                description=f"{match.description}: '{match.matched_text}'",
                severity=severity,
                impact_on_score=int(match.confidence * 20)
            ))
        return evidence_list
