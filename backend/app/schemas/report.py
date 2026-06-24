"""Report schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(default="technical", pattern=r"^(executive|technical|incident|compliance)$")
    format: str = Field(default="json", pattern=r"^(pdf|json|html)$")


class ReportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    scan_id: uuid.UUID
    report_type: str
    format: str
    file_path: str
    generated_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
