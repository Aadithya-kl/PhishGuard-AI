"""AI Security Copilot schemas."""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    scan_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[dict[str, str]] = Field(default_factory=list)


class CopilotResponse(BaseModel):
    response: str
    suggested_questions: list[str] = Field(default_factory=list)
    context_used: list[str] = Field(default_factory=list)


class CopilotSuggestionsResponse(BaseModel):
    scan_id: uuid.UUID
    suggestions: list[str]
