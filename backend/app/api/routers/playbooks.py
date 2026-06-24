from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.playbook import ActionRecommendation, ActionStatus
from app.schemas.playbook import ActionRecommendationResponse, ActionFeedback
from app.models.audit import AuditLog
from app.playbooks.executor import execute_action
from app.models.recommendation_feedback import RecommendationOutcome, OutcomeType
from app.services.trust_engine import AutomationTrustEngine

router = APIRouter()

@router.get("", response_model=List[ActionRecommendationResponse])
async def list_recommendations(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))
):
    query = select(ActionRecommendation).where(ActionRecommendation.organization_id == tenant.organization.id)
    if status:
        query = query.where(ActionRecommendation.status == status)
    
    query = query.order_by(desc(ActionRecommendation.created_at))
    result = await db.execute(query)
    
    return [ActionRecommendationResponse.model_validate(r) for r in result.scalars()]

@router.post("/{id}/approve", response_model=dict)
async def approve_recommendation(
    id: uuid.UUID,
    feedback: ActionFeedback,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    rec = await db.get(ActionRecommendation, id)
    if not rec or rec.organization_id != tenant.organization.id:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    if rec.status != ActionStatus.pending:
        raise HTTPException(status_code=400, detail="Recommendation is not pending")
        
    rec.status = ActionStatus.approved
    rec.approved_by = tenant.user.id
    rec.approved_at = datetime.now(timezone.utc)
    rec.analyst_feedback = feedback.analyst_feedback
    rec.analyst_notes = feedback.analyst_notes
    
    # Audit log
    audit_log = AuditLog(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        action="recommendation_approved",
        entity_type="action_recommendation",
        entity_id=str(rec.id)
    )
    db.add(audit_log)
    
    # Recommendation Outcome
    outcome = RecommendationOutcome(
        organization_id=tenant.organization.id,
        recommendation_id=rec.id,
        analyst_id=tenant.user.id,
        outcome_type=OutcomeType.approved,
        feedback_category=feedback.feedback_category,
        feedback_reason=feedback.analyst_feedback,
        feedback_notes=feedback.analyst_notes
    )
    db.add(outcome)
    await db.commit()
    
    # Trust Engine Update
    await AutomationTrustEngine.process_outcome(db, outcome)
    
    # Trigger execution
    await execute_action(db, rec.id, tenant.user.id)
    
    return {"message": "Action approved and execution requested", "status": rec.status.value}

@router.post("/{id}/reject", response_model=dict)
async def reject_recommendation(
    id: uuid.UUID,
    feedback: ActionFeedback,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    rec = await db.get(ActionRecommendation, id)
    if not rec or rec.organization_id != tenant.organization.id:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    if rec.status != ActionStatus.pending:
        raise HTTPException(status_code=400, detail="Recommendation is not pending")
        
    rec.status = ActionStatus.rejected
    rec.analyst_feedback = feedback.analyst_feedback
    rec.analyst_notes = feedback.analyst_notes
    
    # Audit log
    audit_log = AuditLog(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        action="recommendation_rejected",
        entity_type="action_recommendation",
        entity_id=str(rec.id)
    )
    db.add(audit_log)
    
    # Recommendation Outcome
    outcome = RecommendationOutcome(
        organization_id=tenant.organization.id,
        recommendation_id=rec.id,
        analyst_id=tenant.user.id,
        outcome_type=OutcomeType.rejected,
        feedback_category=feedback.feedback_category,
        feedback_reason=feedback.analyst_feedback,
        feedback_notes=feedback.analyst_notes
    )
    db.add(outcome)
    await db.commit()
    
    # Trust Engine Update
    await AutomationTrustEngine.process_outcome(db, outcome)
    
    return {"message": "Action rejected", "status": rec.status.value}
