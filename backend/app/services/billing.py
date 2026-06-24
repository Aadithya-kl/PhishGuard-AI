from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.models.usage import OrganizationUsage

class PlanLimits:
    FREE = {"max_scans_per_month": 100, "max_copilot_queries_per_month": 10}
    PRO = {"max_scans_per_month": 1000, "max_copilot_queries_per_month": 500}
    ENTERPRISE = {"max_scans_per_month": -1, "max_copilot_queries_per_month": -1}

class PlanEnforcementService:
    async def check_scan_limit(self, db: AsyncSession, organization_id: uuid.UUID) -> bool:
        """Check if the organization can perform another scan."""
        return await self._check_limit(db, organization_id, "scans_processed", "max_scans_per_month")

    async def check_copilot_limit(self, db: AsyncSession, organization_id: uuid.UUID) -> bool:
        """Check if the organization can perform another copilot query."""
        return await self._check_limit(db, organization_id, "copilot_queries", "max_copilot_queries_per_month")

    async def increment_scan_usage(self, db: AsyncSession, organization_id: uuid.UUID):
        """Increment scan usage count."""
        await self._increment_usage(db, organization_id, "scans_processed")

    async def increment_copilot_usage(self, db: AsyncSession, organization_id: uuid.UUID):
        """Increment copilot usage count."""
        await self._increment_usage(db, organization_id, "copilot_queries")

    async def _check_limit(self, db: AsyncSession, organization_id: uuid.UUID, usage_field: str, limit_field: str) -> bool:
        res = await db.execute(
            select(OrganizationUsage).where(
                OrganizationUsage.organization_id == organization_id
            )
        )
        usage = res.scalar_one_or_none()
        
        # If no usage record, they are definitely under limit
        if not usage:
            return True
            
        current_usage = getattr(usage, usage_field) or 0
        
        # Determine plan limits (assuming we have a helper to get plan limits based on org's plan)
        from app.models.organization import Organization
        org_res = await db.execute(select(Organization).where(Organization.id == organization_id))
        org = org_res.scalar_one_or_none()
        if not org:
            return False
            
        plan = org.plan
        limit = getattr(PlanLimits, plan.upper(), {}).get(limit_field, 0)
        
        # Return true if unlimited (-1) or current usage < limit
        return limit == -1 or current_usage < limit

    async def _increment_usage(self, db: AsyncSession, organization_id: uuid.UUID, usage_field: str):
        res = await db.execute(
            select(OrganizationUsage).where(
                OrganizationUsage.organization_id == organization_id
            )
        )
        usage = res.scalar_one_or_none()
        
        if not usage:
            usage = OrganizationUsage(
                organization_id=organization_id
            )
            db.add(usage)
            
        current_val = getattr(usage, usage_field) or 0
        setattr(usage, usage_field, current_val + 1)
        await db.commit()

billing_service = PlanEnforcementService()
