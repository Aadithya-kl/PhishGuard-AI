"""Knowledge graph schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class GraphNodeResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    node_type: str
    node_value: str
    properties: Optional[dict[str, Any]] = None
    risk_score: Optional[float] = None


class GraphEdgeResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relationship: str
    properties: Optional[dict[str, Any]] = None


class GraphDataResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class AttackChainStep(BaseModel):
    step: int
    node: GraphNodeResponse
    action: str
    description: str


class AttackChainResponse(BaseModel):
    scan_id: uuid.UUID
    chain: list[AttackChainStep]
    summary: str
