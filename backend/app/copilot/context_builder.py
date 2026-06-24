from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.scan import EmailScan
from app.models.investigation import Investigation

class ContextBuilder:
    async def build_context(self, context_ids: Dict[str, str], session: AsyncSession, organization_id: str) -> Dict[str, Any]:
        """
        Pre-loads evidence based on the current UI context.
        E.g. if the user is looking at an investigation, we fetch it immediately.
        """
        evidence = {}
        
        if "current_scan_id" in context_ids:
            from sqlalchemy.orm import selectinload
            stmt = select(EmailScan).where(
                EmailScan.id == context_ids["current_scan_id"],
                EmailScan.organization_id == organization_id
            ).options(
                selectinload(EmailScan.iocs),
                selectinload(EmailScan.ai_analysis)
            )
            res = await session.execute(stmt)
            scan = res.scalar_one_or_none()
            if scan:
                evidence["current_scan"] = {
                    "id": str(scan.id),
                    "subject": scan.subject,
                    "sender": scan.sender_address,
                    "risk_level": scan.risk_level,
                    "ai_analysis": scan.ai_analysis,
                    "iocs": scan.iocs
                }
                
        if "current_investigation_id" in context_ids:
            stmt = select(Investigation).where(
                Investigation.id == context_ids["current_investigation_id"],
                Investigation.organization_id == organization_id
            )
            res = await session.execute(stmt)
            inv = res.scalar_one_or_none()
            if inv:
                evidence["current_investigation"] = {
                    "id": str(inv.id),
                    "title": inv.title,
                    "status": inv.status,
                    "severity": inv.severity,
                    "findings": inv.findings
                }
                
        if "current_ioc" in context_ids:
            evidence["current_ioc"] = context_ids["current_ioc"]
            
        return evidence
