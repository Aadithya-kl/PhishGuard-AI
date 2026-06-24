from app.models.response import ResponseRiskTier

class ActionRegistry:
    # Mapping of action_type to its default Risk Tier
    ACTIONS = {
        # Investigation
        "auto_assign_investigation": ResponseRiskTier.LOW,
        "auto_create_case": ResponseRiskTier.LOW,
        "auto_escalate": ResponseRiskTier.LOW,
        
        # Email Security
        "quarantine_email": ResponseRiskTier.MEDIUM,
        "block_sender": ResponseRiskTier.MEDIUM,
        "delete_email": ResponseRiskTier.CRITICAL,
        "block_domain": ResponseRiskTier.CRITICAL,
        
        # Identity
        "disable_user": ResponseRiskTier.HIGH,
        "force_password_reset": ResponseRiskTier.HIGH,
        "revoke_session": ResponseRiskTier.HIGH,
        "revoke_oauth_consent": ResponseRiskTier.CRITICAL,
        
        # Infrastructure
        "block_ioc": ResponseRiskTier.HIGH,
        "block_ip": ResponseRiskTier.HIGH,
        "block_url": ResponseRiskTier.HIGH,
        "create_firewall_rule": ResponseRiskTier.CRITICAL,
    }

    @classmethod
    def get_risk_tier(cls, action_type: str) -> ResponseRiskTier:
        return cls.ACTIONS.get(action_type, ResponseRiskTier.CRITICAL) # Default to CRITICAL if unknown for safety

    @classmethod
    def is_valid_action(cls, action_type: str) -> bool:
        return action_type in cls.ACTIONS
