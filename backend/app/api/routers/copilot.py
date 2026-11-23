from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Dict, Literal
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.copilot.copilot_engine import CopilotEngine
from app.services.billing import billing_service

router = APIRouter()

from app.core.rate_limit import user_limiter
import uuid as _uuid

_CONTEXT_KEYS = {"current_scan_id", "current_investigation_id", "current_ioc"}


class ChatMessage(BaseModel):
    # "system" is deliberately not allowed: clients must not be able to inject system prompts.
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=8000)


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)
    analyst_mode: Literal["soc_analyst", "threat_hunter", "executive", "incident_response"] = "soc_analyst"
    context: Dict[str, str] = Field(default_factory=dict)

    @field_validator("context")
    @classmethod
    def _check_context(cls, v: Dict[str, str]) -> Dict[str, str]:
        clean: Dict[str, str] = {}
        for key, value in v.items():
            if key not in _CONTEXT_KEYS:
                continue
            if key in {"current_scan_id", "current_investigation_id"}:
                try:
                    _uuid.UUID(value)
                except (ValueError, TypeError):
                    continue
            clean[key] = str(value)[:2048]
        return clean

class CopilotChatResponse(BaseModel):
    answer: str
    tools_used: List[str]
    sources: List[str]
    confidence: int

@router.post("/chat", response_model=CopilotChatResponse)
@user_limiter.limit("20/minute")
async def chat_with_copilot(
    request: Request,
    body: CopilotChatRequest,
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
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in body.history]
        
        logger.info(f"Copilot chat requested by {tenant.user.email} in org {tenant.organization.id}")
        
        result = await engine.chat(
            user_message=body.message,
            conversation_history=history_dicts,
            analyst_mode=body.analyst_mode,
            context_ids=body.context,
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
