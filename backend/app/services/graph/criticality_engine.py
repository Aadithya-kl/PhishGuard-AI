import networkx as nx
from typing import Dict, Any

def rank_critical_nodes(G: nx.Graph, top_n: int = 10) -> list[Dict[str, Any]]:
    """
    Ranks the most important nodes in the graph based on Criticality Score.
    
    Factors:
    - degree_centrality
    - betweenness_centrality
    - campaign_count
    - scan_count
    - risk_score
    """
    if len(G.nodes) == 0:
        return []
        
    deg_cent = nx.degree_centrality(G)
    # Betweenness centrality can be expensive for large graphs, but fine for MVP
    # Cap k=50 to limit processing time if graph is very large
    k = min(len(G.nodes), 50)
    bet_cent = nx.betweenness_centrality(G, k=k)
    
    ranked_nodes = []
    
    for node, attr in G.nodes(data=True):
        # We generally care about infrastructure / IOCs, not the scans themselves
        if attr.get("type") in ("Scan", "Campaign"):
            continue
            
        neighbors = set(G.neighbors(node))
        
        # Calculate connected counts
        campaign_count = sum(1 for n in neighbors if G.nodes[n].get("type") == "Campaign")
        scan_count = sum(1 for n in neighbors if G.nodes[n].get("type") == "Scan")
        
        # Aggregate Risk Score based on connected scans/IOCs
        # If node has an intrinsic risk, use it, else inherit from neighbors
        risk_score = 0.0
        risk_edges = [d.get("confidence", "Low") for _, _, d in G.edges(node, data=True)]
        if "High" in risk_edges:
            risk_score = 100.0
        elif "Medium" in risk_edges:
            risk_score = 50.0
            
        dc = deg_cent.get(node, 0.0)
        bc = bet_cent.get(node, 0.0)
        
        # Criticality Score calculation (Weighted formula)
        # Degree (0-1) * 30 + Betweenness (0-1) * 30 + Campaign Count * 10 + Scan Count * 2 + Risk (0-100) * 0.2
        criticality_score = (dc * 30.0) + (bc * 30.0) + (campaign_count * 10.0) + (scan_count * 2.0) + (risk_score * 0.2)
        
        ranked_nodes.append({
            "node": node,
            "type": attr.get("type"),
            "criticality_score": round(criticality_score, 2),
            "degree_centrality": round(dc, 4),
            "betweenness_centrality": round(bc, 4),
            "campaign_count": campaign_count,
            "scan_count": scan_count,
            "risk_score": risk_score
        })
        
    # Sort descending
    ranked_nodes.sort(key=lambda x: x["criticality_score"], reverse=True)
    return ranked_nodes[:top_n]
