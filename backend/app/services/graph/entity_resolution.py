import networkx as nx
from typing import List, Dict, Any
from Levenshtein import ratio

def resolve_entities(G: nx.Graph, entity_type: str = "Domain") -> List[Dict[str, Any]]:
    """
    Identifies duplicate or heavily related entities using Composite Resolution Scoring.
    Composite Weights:
      - 40% String Similarity (Levenshtein)
      - 20% Shared IP Infrastructure
      - 20% Shared URLs
      - 10% Shared Hashes
      - 10% Shared Campaign Membership
    Resolves when total score >= 70.
    """
    nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == entity_type]
    resolved = []
    
    # Track nodes we've already merged into a cluster to avoid redundant pairs
    seen = set()
    
    for i in range(len(nodes)):
        if nodes[i] in seen: continue
        
        cluster = [nodes[i]]
        evidence_log = []
        
        for j in range(i + 1, len(nodes)):
            if nodes[j] in seen: continue
            
            node_a = nodes[i]
            node_b = nodes[j]
            
            # 1. String Similarity (40 points max)
            str_sim = ratio(node_a.lower(), node_b.lower())
            score_string = str_sim * 40.0
            
            # Get neighbors for infrastructural overlap
            neighbors_a = set(G.neighbors(node_a))
            neighbors_b = set(G.neighbors(node_b))
            
            # Shared subsets
            shared_ips = [n for n in neighbors_a.intersection(neighbors_b) if G.nodes[n].get("type") == "IP"]
            shared_urls = [n for n in neighbors_a.intersection(neighbors_b) if G.nodes[n].get("type") == "URL"]
            shared_hashes = [n for n in neighbors_a.intersection(neighbors_b) if G.nodes[n].get("type") == "Hash"]
            shared_campaigns = [n for n in neighbors_a.intersection(neighbors_b) if G.nodes[n].get("type") == "Campaign"]
            
            # 2. Shared IP (20 points max, 1 shared is enough for full points for now, or scaled)
            score_ip = 20.0 if shared_ips else 0.0
            
            # 3. Shared URLs (20 points max)
            score_url = 20.0 if shared_urls else 0.0
            
            # 4. Shared Hashes (10 points max)
            score_hash = 10.0 if shared_hashes else 0.0
            
            # 5. Shared Campaign (10 points max)
            score_campaign = 10.0 if shared_campaigns else 0.0
            
            total_score = score_string + score_ip + score_url + score_hash + score_campaign
            
            if total_score >= 70.0:
                cluster.append(node_b)
                seen.add(node_b)
                evidence_log.append({
                    "target": node_b,
                    "resolution_score": round(total_score, 2),
                    "evidence": {
                        "string_similarity": round(str_sim * 100, 1),
                        "shared_ips": len(shared_ips),
                        "shared_urls": len(shared_urls),
                        "shared_hashes": len(shared_hashes),
                        "shared_campaigns": len(shared_campaigns)
                    },
                    "supporting_relationships": shared_ips + shared_urls + shared_hashes + shared_campaigns
                })
                
        if len(cluster) > 1:
            seen.add(nodes[i])
            resolved.append({
                "entity_id": f"resolved_{cluster[0]}",
                "primary_entity": cluster[0],
                "resolved_entities": cluster[1:],
                "evidence": evidence_log
            })
            
    return resolved
