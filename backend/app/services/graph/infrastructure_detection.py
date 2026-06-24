import networkx as nx
from typing import List, Dict, Any

def detect_infrastructure_clusters(G: nx.Graph) -> List[Dict[str, Any]]:
    """
    Identifies shared attack infrastructure by isolating Domain, IP, Hash, and URL nodes.
    Returns connected components of infrastructure.
    """
    infra_types = {"Domain", "IP", "Hash", "URL"}
    infra_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") in infra_types]
    
    # Create subgraph with only infrastructure nodes
    infra_subgraph = G.subgraph(infra_nodes)
    
    # Find connected components (islands of shared infrastructure)
    components = list(nx.connected_components(infra_subgraph))
    
    clusters = []
    for idx, comp in enumerate(components):
        # We only care about clusters with > 1 node (shared infrastructure)
        if len(comp) > 1:
            comp_nodes = list(comp)
            # Classify the type of infrastructure
            domains = [n for n in comp_nodes if G.nodes[n].get("type") == "Domain"]
            ips = [n for n in comp_nodes if G.nodes[n].get("type") == "IP"]
            hashes = [n for n in comp_nodes if G.nodes[n].get("type") == "Hash"]
            urls = [n for n in comp_nodes if G.nodes[n].get("type") == "URL"]
            
            # Confidence based on size and variety
            confidence = "Low"
            if len(comp) > 5 or (len(domains) > 0 and len(ips) > 0):
                confidence = "High"
            elif len(comp) > 2:
                confidence = "Medium"
                
            clusters.append({
                "cluster_id": f"infra_cluster_{idx+1}",
                "confidence": confidence,
                "node_count": len(comp),
                "nodes": {
                    "domains": domains,
                    "ips": ips,
                    "hashes": hashes,
                    "urls": urls
                }
            })
            
    # Sort by size descending
    clusters.sort(key=lambda x: x["node_count"], reverse=True)
    return clusters
