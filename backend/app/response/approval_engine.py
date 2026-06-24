import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.response import ResponseApproval, ResponseRiskTier

class ApprovalEngine:
    @staticmethod
    async def get_required_approvals(risk_tier: ResponseRiskTier) -> list[str]:
        if risk_tier == ResponseRiskTier.LOW:
            return []
        if risk_tier == ResponseRiskTier.MEDIUM:
            return ["Analyst"]
        if risk_tier == ResponseRiskTier.HIGH:
            return ["Manager"]
        if risk_tier == ResponseRiskTier.CRITICAL:
            # Two-Person Rule
            return ["Manager", "OrgAdmin"]
            
        return ["OrgAdmin"] # Default fallback safe

    @staticmethod
    async def is_approved(db: AsyncSession, request_id: uuid.UUID, risk_tier: ResponseRiskTier) -> bool:
        required = await ApprovalEngine.get_required_approvals(risk_tier)
        if not required:
            return True
            
        result = await db.execute(
            select(ResponseApproval.approver_role).where(ResponseApproval.request_id == request_id)
        )
        approved_roles = set(result.scalars().all())
        
        for req_role in required:
            if req_role not in approved_roles:
                return False
                
        return True
