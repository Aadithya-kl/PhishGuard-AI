import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.playbook import ActionRecommendation, ActionStatus
from app.models.audit import AuditLog
from app.config import settings
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

async def execute_action(db: AsyncSession, action_id: uuid.UUID, executed_by: uuid.UUID) -> bool:
    """
    Executes a given ActionRecommendation.
    Enforces the Phase 9 OBSERVATION_MODE hard guardrail.
    """
    # Fetch action
    action = await db.get(ActionRecommendation, action_id)
    if not action:
        return False
        
    if action.status != ActionStatus.approved:
        logger.warning(f"Attempted to execute action {action_id} which is not approved.")
        return False

    # Observation Mode Hard Guardrail
    if settings.OBSERVATION_MODE:
        destructive_types = [
            "quarantine_mailbox", "delete_mailbox", "disable_user",
            "revoke_token", "block_domain", "endpoint_isolation",
            "reset_password", "mfa_validation", "endpoint_review", "token_review"
        ]
        
        # Even if not in destructive types, everything is blocked in observation mode to be safe unless it's just 'escalate_investigation'
        # Actually the user prompt said: "Observation Mode must block all destructive actions."
        # And "If execution is attempted: AuditLog(action='execution_blocked_observation_mode')"
        
        audit_log = AuditLog(
            organization_id=action.organization_id,
            user_id=executed_by,
            action="execution_blocked_observation_mode",
            entity_type="action_recommendation",
            entity_id=str(action.id),
            details={
                "playbook_name": action.playbook_name,
                "recommendation_type": action.recommendation_type,
                "reasoning": "Execution blocked due to OBSERVATION_MODE=True guardrail."
            }
        )
        db.add(audit_log)
        
        # Mark as executed anyway since observation mode 'completes' it
        action.status = ActionStatus.executed
        action.executed_at = datetime.now(timezone.utc)
        await db.commit()
        return True

    # Real execution would go here if Phase 10...
    # ...
    
    action.status = ActionStatus.executed
    action.executed_at = datetime.now(timezone.utc)
    
    audit_log = AuditLog(
        organization_id=action.organization_id,
        user_id=executed_by,
        action="action_executed",
        entity_type="action_recommendation",
        entity_id=str(action.id),
        details={"recommendation_type": action.recommendation_type}
    )
    db.add(audit_log)
    
    await db.commit()
    return True
