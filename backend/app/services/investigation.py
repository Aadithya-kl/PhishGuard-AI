from typing import Dict, Any, List

class InvestigationService:
    def __init__(self):
        pass

    def investigate(self, scan_id: str) -> Dict[str, Any]:
        return {
            "executive_summary": "Automated investigation complete.",
            "detailed_findings": [],
            "attack_chain": [],
            "mitigation_actions": ["Block sender", "Delete email"],
            "risk_assessment": {"level": "low"},
            "timeline": []
        }
