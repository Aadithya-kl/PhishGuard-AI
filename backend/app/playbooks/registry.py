from typing import Callable, Dict, List
from app.playbooks.models import ActionRecommendationCreate
from app.models.playbook import ConfidenceLevel

class PlaybookRegistry:
    def __init__(self):
        self._playbooks = {}

    def register(self, name: str):
        def decorator(func: Callable):
            self._playbooks[name] = func
            return func
        return decorator

    def get_playbook(self, name: str) -> Callable:
        return self._playbooks.get(name)
        
    def get_all(self) -> Dict[str, Callable]:
        return self._playbooks

registry = PlaybookRegistry()

@registry.register("Credential Harvesting")
def credential_harvesting_playbook(scan_data: dict) -> List[ActionRecommendationCreate]:
    actions = []
    # Evaluate scan_data
    if scan_data.get("risk_score", 0) > 80 and "Credential Harvesting Attempt" in scan_data.get("detections", []):
        confidence_score = 85.0
        actions.append(ActionRecommendationCreate(
            playbook_name="Credential Harvesting",
            recommendation_type="reset_password",
            reasoning="Detected high-confidence credential harvesting attempt against user.",
            confidence_score=confidence_score,
            confidence_level=ConfidenceLevel.HIGH if confidence_score >= 80 else ConfidenceLevel.MEDIUM,
            triggering_detections=scan_data.get("detections", []),
            triggering_mitre_ids=["T1566.002", "T1056"],
            triggering_iocs=scan_data.get("iocs", []),
            affected_users_count=1,
            scan_id=scan_data.get("scan_id")
        ))
        
        actions.append(ActionRecommendationCreate(
            playbook_name="Credential Harvesting",
            recommendation_type="mfa_validation",
            reasoning="Require immediate MFA validation due to credential exposure risk.",
            confidence_score=confidence_score,
            confidence_level=ConfidenceLevel.HIGH if confidence_score >= 80 else ConfidenceLevel.MEDIUM,
            triggering_detections=scan_data.get("detections", []),
            triggering_mitre_ids=["T1566.002", "T1056"],
            triggering_iocs=scan_data.get("iocs", []),
            affected_users_count=1,
            scan_id=scan_data.get("scan_id")
        ))
    return actions

@registry.register("Business Email Compromise")
def business_email_compromise_playbook(scan_data: dict) -> List[ActionRecommendationCreate]:
    actions = []
    if "BEC Intent Detected" in scan_data.get("detections", []):
        confidence_score = 90.0
        actions.append(ActionRecommendationCreate(
            playbook_name="Business Email Compromise",
            recommendation_type="escalate_investigation",
            reasoning="Financial fraud/BEC intent detected requiring immediate escalation.",
            confidence_score=confidence_score,
            confidence_level=ConfidenceLevel.HIGH,
            triggering_detections=scan_data.get("detections", []),
            triggering_mitre_ids=["T1566.001", "T1036"],
            triggering_iocs=scan_data.get("iocs", []),
            affected_users_count=1,
            scan_id=scan_data.get("scan_id")
        ))
    return actions

@registry.register("Malware Delivery")
def malware_delivery_playbook(scan_data: dict) -> List[ActionRecommendationCreate]:
    actions = []
    if "Malicious Attachment" in scan_data.get("detections", []):
        confidence_score = 95.0
        actions.append(ActionRecommendationCreate(
            playbook_name="Malware Delivery",
            recommendation_type="endpoint_review",
            reasoning="Malicious attachment delivered. Requires endpoint hash sweeping.",
            confidence_score=confidence_score,
            confidence_level=ConfidenceLevel.HIGH,
            triggering_detections=scan_data.get("detections", []),
            triggering_mitre_ids=["T1204.002", "T1059"],
            triggering_iocs=scan_data.get("iocs", []),
            affected_users_count=1,
            scan_id=scan_data.get("scan_id")
        ))
    return actions

@registry.register("OAuth Consent Phishing")
def oauth_consent_phishing_playbook(scan_data: dict) -> List[ActionRecommendationCreate]:
    actions = []
    if "OAuth Consent Phishing" in scan_data.get("detections", []):
        confidence_score = 88.0
        actions.append(ActionRecommendationCreate(
            playbook_name="OAuth Consent Phishing",
            recommendation_type="token_review",
            reasoning="Malicious OAuth consent URL found. Requires application token audit.",
            confidence_score=confidence_score,
            confidence_level=ConfidenceLevel.HIGH,
            triggering_detections=scan_data.get("detections", []),
            triggering_mitre_ids=["T1528"],
            triggering_iocs=scan_data.get("iocs", []),
            affected_users_count=1,
            scan_id=scan_data.get("scan_id")
        ))
    return actions
