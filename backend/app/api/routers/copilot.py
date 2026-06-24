from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.user import User
from app.copilot.copilot_engine import CopilotEngine
from app.services.billing import billing_service

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class CopilotChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    analyst_mode: str = "soc_analyst"
    context: Dict[str, str] = {}  # e.g. {"current_scan_id": "...", "current_ioc": "..."}

class CopilotChatResponse(BaseModel):
    answer: str
    tools_used: List[str]
    sources: List[str]
    confidence: int

@router.post("/chat", response_model=CopilotChatResponse)
async def chat_with_copilot(
    request: CopilotChatRequest,
    tenant: TenantContext = Depends(requires_permission(Permission.USE_COPILOT)),
    db: AsyncSession = Depends(get_db)
):
    try:
        if not await billing_service.check_copilot_limit(db, tenant.organization.id):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Copilot query limit reached for this billing period. Please upgrade your plan."
            )

        engine = CopilotEngine()
        
        # Convert history
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        logger.info(f"Copilot chat requested by {tenant.user.email} in org {tenant.organization.id}")
        
        result = await engine.chat(
            user_message=request.message,
            conversation_history=history_dicts,
            analyst_mode=request.analyst_mode,
            context_ids=request.context,
            session=db,
            organization_id=tenant.organization.id
        )
        
        await billing_service.increment_copilot_usage(db, tenant.organization.id)
        
        return CopilotChatResponse(
            answer=result.get("answer", ""),
            tools_used=result.get("tools_used", []),
            sources=result.get("sources", []),
            confidence=result.get("confidence", 50)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Copilot chat failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error communicating with Copilot Engine")
