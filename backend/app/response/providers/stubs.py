import uuid
from app.response.providers.base import BaseProvider, ProviderDryRunResult, ProviderExecutionResult
from app.models.response import ProviderTrustLevel

class StubProvider(BaseProvider):
    def __init__(self, organization_id: uuid.UUID, name: str, trust_level: ProviderTrustLevel = ProviderTrustLevel.LAB):
        super().__init__(organization_id)
        self._name = name
        self._trust_level = trust_level

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def trust_level(self) -> str:
        return self._trust_level.value

    async def dry_run(self, action_type: str, target_entity: str, context: dict) -> ProviderDryRunResult:
        # Mock blast radius mapping
        blast = {"affected_users": 1, "affected_mailboxes": 1, "affected_domains": 0, "affected_integrations": 0}
        
        # Specific mock for exceeding blast radius if domain block
        if action_type == "block_domain":
            blast["affected_users"] = 5000 # will trigger blast radius
            blast["affected_domains"] = 1
            
        return ProviderDryRunResult(
            success=True,
            target_entities=[target_entity],
            estimated_blast_radius=blast,
            expected_side_effects=[f"{action_type} will impact {target_entity}"],
            rollback_available=True
        )

    async def execute(self, action_type: str, target_entity: str, context: dict) -> ProviderExecutionResult:
        if self.is_lab:
            return ProviderExecutionResult(success=False, reason="LAB providers cannot execute actions.")
        return ProviderExecutionResult(success=True, rollback_id=uuid.uuid4().hex)

    async def rollback(self, action_type: str, target_entity: str, rollback_id: str) -> bool:
        return True


class M365Provider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "Microsoft 365", ProviderTrustLevel.TESTED)

class GoogleWorkspaceProvider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "Google Workspace", ProviderTrustLevel.TESTED)

class OktaProvider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "Okta", ProviderTrustLevel.TESTED)

class CloudflareProvider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "Cloudflare", ProviderTrustLevel.TESTED)

class CrowdStrikeProvider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "CrowdStrike", ProviderTrustLevel.PRODUCTION)

class DefenderProvider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "Microsoft Defender", ProviderTrustLevel.PRODUCTION)

class MockLabProvider(StubProvider):
    def __init__(self, organization_id: uuid.UUID):
        super().__init__(organization_id, "Mock Provider", ProviderTrustLevel.LAB)

def get_provider_for_action(action_type: str, org_id: uuid.UUID) -> BaseProvider:
    if action_type in ["quarantine_email", "delete_email"]:
        return M365Provider(org_id)
    if action_type in ["disable_user", "force_password_reset", "revoke_session", "revoke_oauth_consent"]:
        return OktaProvider(org_id)
    if action_type in ["block_domain", "block_url"]:
        return CloudflareProvider(org_id)
    if action_type in ["block_ioc", "block_ip"]:
        return CrowdStrikeProvider(org_id)
    if action_type == "create_firewall_rule":
        return DefenderProvider(org_id)
    # Default to Mock Lab
    return MockLabProvider(org_id)
