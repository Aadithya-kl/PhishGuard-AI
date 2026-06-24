import networkx as nx
from typing import List, Dict, Any

def cluster_threat_actors(G: nx.Graph) -> List[Dict[str, Any]]:
    """
    Groups campaigns into potential Threat Actors based on shared infrastructure.
    """
    # 1. Identify all Campaign nodes
    campaigns = [n for n, attr in G.nodes(data=True) if attr.get("type") == "Campaign"]
    
    if not campaigns:
        return []
        
    # 2. Create a bipartite projection of Campaigns based on shared infrastructure
    # If two campaigns share an IP, Domain, or Hash, we link them.
    infra_types = {"Domain", "IP", "Hash"}
    
    actor_graph = nx.Graph()
    actor_graph.add_nodes_from(campaigns)
    
    # Check all pairs of campaigns
    for i in range(len(campaigns)):
        for j in range(i + 1, len(campaigns)):
            c1 = campaigns[i]
            c2 = campaigns[j]
            
            n1 = set(G.neighbors(c1))
            n2 = set(G.neighbors(c2))
            
            shared = n1.intersection(n2)
            shared_infra = [n for n in shared if G.nodes[n].get("type") in infra_types]
            
            # If they share at least 1 piece of core infrastructure, link them
            if len(shared_infra) >= 1:
                actor_graph.add_edge(c1, c2, shared_infra=shared_infra)
                
    # 3. Find connected components (Threat Actors)
    actor_components = list(nx.connected_components(actor_graph))
    
    actors = []
    for idx, comp in enumerate(actor_components):
        # Even isolated campaigns are tracked as single actors, but we'll focus on multi-campaign clusters
        comp_campaigns = list(comp)
        
        # Aggregate IOCs across all campaigns in this actor
        all_iocs = set()
        for c in comp_campaigns:
            c_neighbors = [n for n in G.neighbors(c) if G.nodes[n].get("type") in infra_types or G.nodes[n].get("type") == "URL"]
            all_iocs.update(c_neighbors)
            
        confidence = "Low"
        if len(comp_campaigns) > 3 or len(all_iocs) > 10:
            confidence = "High"
        elif len(comp_campaigns) > 1:
            confidence = "Medium"
            
        actors.append({
            "actor_name": f"Threat Actor Alpha-{idx+1}",
            "confidence": confidence,
            "campaign_count": len(comp_campaigns),
            "campaigns": comp_campaigns,
            "ioc_count": len(all_iocs),
            "iocs": list(all_iocs)
        })
        
    actors.sort(key=lambda x: x["campaign_count"], reverse=True)
    return actors
