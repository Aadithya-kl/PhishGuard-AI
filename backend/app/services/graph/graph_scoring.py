import networkx as nx
from typing import Dict, Any
from app.services.graph.criticality_engine import rank_critical_nodes

def get_node_scoring(G: nx.Graph, node_id: str) -> Dict[str, Any]:
    """
    Returns the comprehensive scoring profile for a single node.
    """
    if not G.has_node(node_id):
        return {}
        
    # We can reuse the criticality engine to score this specific node.
    # It calculates scores for all nodes, but we just filter it.
    # For a very large graph, we'd calculate this locally, but since MVP uses small graphs,
    # we'll just compute it all and extract the one we want.
    
    # Or to be efficient:
    deg_cent = nx.degree_centrality(G)
    dc = deg_cent.get(node_id, 0.0)
    
    neighbors = set(G.neighbors(node_id))
    campaign_count = sum(1 for n in neighbors if G.nodes[n].get("type") == "Campaign")
    scan_count = sum(1 for n in neighbors if G.nodes[n].get("type") == "Scan")
    
    risk_score = 0.0
    risk_edges = [d.get("confidence", "Low") for _, _, d in G.edges(node_id, data=True)]
    if "High" in risk_edges:
        risk_score = 100.0
    elif "Medium" in risk_edges:
        risk_score = 50.0
        
    # Criticality approximation without betweenness (which is slow for a single node lookup dynamically)
    # We'll just run rank_critical_nodes to get the exact value for consistency if it's an infrastructure node.
    # Wait, let's just do it directly.
    criticality_score = (dc * 30.0) + (campaign_count * 10.0) + (scan_count * 2.0) + (risk_score * 0.2)

    return {
        "node": node_id,
        "type": G.nodes[node_id].get("type"),
        "risk_score": risk_score,
        "centrality_score": round(dc * 100, 2), # Scaled to 0-100
        "campaign_score": campaign_count * 10.0,
        "criticality_score": round(criticality_score, 2)
    }
