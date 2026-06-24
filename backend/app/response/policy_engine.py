import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.response import OrganizationAutomationPolicy, AutomationLevel

class PolicyEngine:
    @staticmethod
    async def get_policy(db: AsyncSession, organization_id: uuid.UUID, action_type: str) -> OrganizationAutomationPolicy | None:
        result = await db.execute(
            select(OrganizationAutomationPolicy).where(
                OrganizationAutomationPolicy.organization_id == organization_id,
                OrganizationAutomationPolicy.action_type == action_type,
                OrganizationAutomationPolicy.enabled == True
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def evaluate_policy(policy: OrganizationAutomationPolicy | None, risk_score: float) -> str:
        if not policy:
            return "NO_POLICY_FOUND"
            
        if risk_score < policy.risk_threshold:
            return "BELOW_RISK_THRESHOLD"
            
        return policy.automation_level.value
