import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.graph import Relationship

async def build_global_graph(db: AsyncSession, user_id: uuid.UUID) -> nx.Graph:
    """
    Builds an in-memory NetworkX graph from the persisted relationships table.
    """
    rels_res = await db.execute(select(Relationship).where(Relationship.user_id == user_id))
    relationships = rels_res.scalars().all()
    
    G = nx.Graph()
    
    # Confidence weighting map
    weight_map = {
        "High": 1.0,
        "Medium": 0.5,
        "Low": 0.2
    }
    
    for r in relationships:
        # Add nodes with their type as attribute
        if not G.has_node(r.source_value):
            G.add_node(r.source_value, type=r.source_type.value)
        if not G.has_node(r.target_value):
            G.add_node(r.target_value, type=r.target_type.value)
            
        # Add edge
        weight = weight_map.get(r.confidence.value, 0.5)
        G.add_edge(
            r.source_value, 
            r.target_value, 
            relationship=r.relationship_type,
            confidence=r.confidence.value,
            weight=weight
        )
        
    return G

async def build_ego_graph(db: AsyncSession, user_id: uuid.UUID, root_value: str, depth: int = 3) -> nx.Graph:
    """
    Builds a bounded traversal graph (ego graph) from a specific root node.
    """
    G = await build_global_graph(db, user_id)
    if not G.has_node(root_value):
        return nx.Graph()
        
    # Extract ego graph
    ego = nx.ego_graph(G, root_value, radius=depth, center=True, undirected=True)
    return ego
