import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.response import (
    GlobalAutomationState, GlobalAutomationSettings, ResponseAuditRecord, ExecutedAction
)
from app.response.action_registry import ActionRegistry
from app.response.policy_engine import PolicyEngine
from app.response.approval_engine import ApprovalEngine
from app.response.response_guard import ResponseGuard
from app.response.rollback_engine import RollbackEngine
from app.response.providers.stubs import get_provider_for_action

class ResponseEngine:
    @staticmethod
    async def get_global_state(db: AsyncSession) -> GlobalAutomationState:
        result = await db.execute(select(GlobalAutomationSettings))
        settings = result.scalars().first()
        if not settings:
            settings = GlobalAutomationSettings()
            db.add(settings)
            await db.commit()
        return settings.state

    @staticmethod
    async def process_action(
        db: AsyncSession, 
        organization_id: uuid.UUID, 
        action_type: str, 
        target_entity: str, 
        request_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        context: dict = None
    ) -> dict:
        context = context or {}
        correlation_id = uuid.uuid4()
        
        # 1. Global Kill Switch Check
        global_state = await ResponseEngine.get_global_state(db)
        if global_state == GlobalAutomationState.DISABLED:
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "BLOCKED", "Global Automation is DISABLED", correlation_id=correlation_id)
            
        if not ActionRegistry.is_valid_action(action_type):
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "BLOCKED", "Invalid action type", correlation_id=correlation_id)
            
        risk_tier = ActionRegistry.get_risk_tier(action_type)
        
        # 2. Policy Engine
        policy = await PolicyEngine.get_policy(db, organization_id, action_type)
        risk_score = context.get("risk_score", 0.0)
        policy_result = PolicyEngine.evaluate_policy(policy, risk_score)
        
        if policy_result in ["NO_POLICY_FOUND", "BELOW_RISK_THRESHOLD"]:
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "BLOCKED", f"Policy check failed: {policy_result}", correlation_id=correlation_id)
                
        # 3. Approval Engine
        if not await ApprovalEngine.is_approved(db, request_id, risk_tier):
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "PENDING_APPROVAL", f"Missing approvals for tier {risk_tier}", correlation_id=correlation_id)
            
        # 4. Provider Selection
        provider = get_provider_for_action(action_type, organization_id)
        if provider.trust_level not in ["TESTED", "PRODUCTION"]:
            # LAB can only do dry run
            pass # We will enforce this at execution
            
        # 5. Dry Run
        dry_run = await provider.dry_run(action_type, target_entity, context)
        if not dry_run.success:
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "DRY_RUN_FAILED", f"Dry run failed: {dry_run.reason}", correlation_id=correlation_id)
            
        # 6. Blast Radius Simulation (ResponseGuard)
        if not ResponseGuard.check_blast_radius(dry_run.estimated_blast_radius):
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "BLOCKED", "blast_radius_violation", correlation_id=correlation_id)
            
        # 7. Rollback Certification
        if not RollbackEngine.verify_rollback_coverage(dry_run):
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "BLOCKED", "Rollback not available for action", correlation_id=correlation_id)
            
        # Stop here if Observation mode
        if global_state == GlobalAutomationState.OBSERVATION:
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "OBSERVATION_ONLY", "Dry run passed. Action not executed due to Observation mode.", correlation_id=correlation_id)
            
        # Enforce provider trust level
        if provider.trust_level not in ["TESTED", "PRODUCTION"]:
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "BLOCKED", f"Provider {provider.provider_name} is LAB trust level.", correlation_id=correlation_id)
            
        # 8. Execution
        exec_result = await provider.execute(action_type, target_entity, context)
        if not exec_result.success:
            return await ResponseEngine._log_audit(db, organization_id, user_id, action_type, "FAILED", f"Execution failed: {exec_result.reason}", correlation_id=correlation_id)
            
        # 9. Rollback Registration
        executed_action = ExecutedAction(
            organization_id=organization_id,
            action_type=action_type,
            target_entity=target_entity,
            provider_name=provider.provider_name,
            rollback_available=True,
            rollback_id=exec_result.rollback_id
        )
        db.add(executed_action)
        await db.commit()
        
        # 10. Audit Logging
        return await ResponseEngine._log_audit(
            db, organization_id, user_id, action_type, "EXECUTED", 
            f"Action executed via {provider.provider_name}", 
            correlation_id=correlation_id,
            rollback_id=exec_result.rollback_id,
            provider_name=provider.provider_name
        )

    @staticmethod
    async def _log_audit(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID | None, 
        action_type: str, status: str, details: str, correlation_id: uuid.UUID,
        rollback_id: str | None = None, provider_name: str = "Unknown"
    ) -> dict:
        risk_tier = ActionRegistry.get_risk_tier(action_type)
        audit = ResponseAuditRecord(
            organization_id=org_id,
            user_id=user_id,
            action_type=action_type,
            risk_tier=risk_tier,
            provider=provider_name,
            correlation_id=correlation_id,
            status=status,
            details=details,
            rollback_id=rollback_id
        )
        db.add(audit)
        await db.commit()
        return {"status": status, "correlation_id": str(correlation_id), "details": details, "rollback_id": rollback_id}
