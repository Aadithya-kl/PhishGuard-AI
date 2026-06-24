import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.response import ExecutedAction
from app.response.providers.stubs import get_provider_for_action

class RollbackEngine:
    @staticmethod
    def verify_rollback_coverage(dry_run_result) -> bool:
        """
        No action may execute without rollback coverage.
        """
        return dry_run_result.rollback_available

    @staticmethod
    async def execute_rollback(db: AsyncSession, execution_id: uuid.UUID) -> bool:
        result = await db.execute(select(ExecutedAction).where(ExecutedAction.id == execution_id))
        action = result.scalar_one_or_none()
        
        if not action or not action.rollback_available or not action.rollback_id:
            return False
            
        provider = get_provider_for_action(action.action_type, action.organization_id)
        success = await provider.rollback(action.action_type, action.target_entity, action.rollback_id)
        
        if success:
            action.rolled_back = True
            await db.commit()
            
        return success
