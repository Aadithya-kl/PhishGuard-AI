from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.database import get_db
from app.models.user import User
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.services.graph.graph_builder import build_global_graph, build_ego_graph
from app.services.graph.entity_resolution import resolve_entities
from app.services.graph.graph_scoring import get_node_scoring
from app.services.graph.criticality_engine import rank_critical_nodes
from app.services.graph.graph_traversal import traverse_graph
from app.services.graph.infrastructure_detection import detect_infrastructure_clusters
from app.services.graph.actor_clustering import cluster_threat_actors

router = APIRouter()

@router.get("/stats", response_model=Dict[str, Any])
async def get_graph_stats(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))):
    """Get global graph node and edge count."""
    G = await build_global_graph(db, tenant.organization.id)
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges()
    }

@router.get("/node/{id}", response_model=Dict[str, Any])
async def get_graph_node(id: str, db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))):
    """Get node scoring and centrality metrics."""
    G = await build_global_graph(db, tenant.organization.id)
    if not G.has_node(id):
        raise HTTPException(status_code=404, detail="Node not found in graph")
        
    score_profile = get_node_scoring(G, id)
    return score_profile

from app.core.rate_limit import user_limiter
from fastapi import Request

@router.get("/traverse", response_model=Dict[str, Any])
@user_limiter.limit("60/minute")
async def get_graph_traversal(
    request: Request,
    ioc: str = Query(..., description="Root IOC to traverse from"),
    depth: int = Query(1, description="Traversal depth (max 3)"),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))
):
    if depth > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MAX_TRAVERSAL_DEPTH exceeded. Maximum allowed depth is 3."
        )
        
    G = await build_global_graph(db, tenant.organization.id)
    result = traverse_graph(G, ioc, depth=depth)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result

@router.get("/clusters", response_model=List[Dict[str, Any]])
async def get_graph_clusters(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))):
    G = await build_global_graph(db, tenant.organization.id)
    clusters = detect_infrastructure_clusters(G)
    return [c for c in clusters if c["confidence"] in ("Medium", "High")]

@router.get("/actors", response_model=List[Dict[str, Any]])
async def get_graph_actors(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))):
    G = await build_global_graph(db, tenant.organization.id)
    actors = cluster_threat_actors(G)
    return actors

@router.get("/infrastructure", response_model=List[Dict[str, Any]])
async def get_graph_infrastructure(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))):
    G = await build_global_graph(db, tenant.organization.id)
    return detect_infrastructure_clusters(G)

@router.get("/critical-assets", response_model=List[Dict[str, Any]])
async def get_critical_assets(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_GRAPH))):
    G = await build_global_graph(db, tenant.organization.id)
    ranked = rank_critical_nodes(G, top_n=20)
    return ranked
