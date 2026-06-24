import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1/graph"

def print_section(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

def run_audit():
    # 1. Total Node and Edge Count
    print_section("1 & 2. GRAPH SIZE (NODES & EDGES)")
    r_stats = requests.get(f"{API_BASE}/stats")
    if r_stats.status_code == 200:
        stats = r_stats.json()
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Edges: {stats['total_edges']}")
    else:
        print("Failed to get stats:", r_stats.text)

    # 3. Top Critical Assets
    print_section("3 & 8. TOP 10 CRITICAL ASSETS (CENTRALITY SCORING)")
    r_crit = requests.get(f"{API_BASE}/critical-assets")
    if r_crit.status_code == 200:
        assets = r_crit.json()
        for a in assets:
            print(f"- {a['type']}: {a['node']} | CritScore: {a['criticality_score']} | Centrality: {a['degree_centrality']} | Campaigns: {a['campaign_count']} | Risk: {a['risk_score']}")
    else:
        print("Failed to get critical assets:", r_crit.text)

    # 5. Infrastructure Clusters
    print_section("5. INFRASTRUCTURE CLUSTERS")
    r_infra = requests.get(f"{API_BASE}/clusters")
    if r_infra.status_code == 200:
        clusters = r_infra.json()
        print(f"Total Clusters Detected: {len(clusters)}")
        for c in clusters[:3]:
            print(f"\nCluster {c['cluster_id']} (Confidence: {c['confidence']}) - Nodes: {c['node_count']}")
            print(json.dumps(c['nodes'], indent=2))
    else:
        print("Failed to get infra clusters:", r_infra.text)

    # 6. Threat Actor Clusters
    print_section("6. THREAT ACTOR CLUSTERS")
    r_actors = requests.get(f"{API_BASE}/actors")
    if r_actors.status_code == 200:
        actors = r_actors.json()
        print(f"Total Threat Actors Detected: {len(actors)}")
        for a in actors[:2]:
            print(f"\nActor: {a['actor_name']} (Confidence: {a['confidence']})")
            print(f"Campaigns Linked: {a['campaign_count']}")
            print(f"IOCs Linked: {a['ioc_count']}")
            print(f"Campaign IDs: {a['campaigns']}")
    else:
        print("Failed to get actors:", r_actors.text)

    # 7. Entity Resolution
    print_section("7. ENTITY RESOLUTION EXAMPLES")
    r_res = requests.get(f"{API_BASE}/infrastructure")
    if r_res.status_code == 200:
        resolutions = r_res.json()
        print(f"Total Entity Resolutions: {len(resolutions)}")
        for res in resolutions[:2]:
            print(f"\nResolved Entity: {res['entity_id']}")
            print(f"Primary: {res['primary_entity']}")
            print(f"Merged Variants: {res['resolved_entities']}")
            print(json.dumps(res['evidence'], indent=2))
    else:
        print("Failed to resolve entities:", r_res.text)

    # 4. Traversal
    print_section("4. EXAMPLE TRAVERSAL (DEPTH=3)")
    # We need a valid IOC to traverse. Let's use the top critical asset if available.
    root_node = assets[0]['node'] if r_crit.status_code == 200 and assets else "paypal-secure.com"
    print(f"Traversing from Root: {root_node}")
    
    r_trav = requests.get(f"{API_BASE}/traverse", params={"ioc": root_node, "depth": 3})
    if r_trav.status_code == 200:
        trav = r_trav.json()
        print(f"Traversal Output Graph Nodes: {trav['total_nodes']}")
        print(f"Traversal Output Graph Edges: {trav['total_edges']}")
        # Only print first level of tree to avoid huge console dump
        tree = trav['tree']
        print(f"\nRoot: {tree['id']} ({tree['type']})")
        for child in tree['children']:
            print(f"  +- {child['id']} ({child['type']})")
            if 'children' in child:
                for gc in child['children'][:2]:
                    print(f"       +- {gc['id']} ({gc['type']})")
                if len(child['children']) > 2:
                    print(f"       +- ... and {len(child['children']) - 2} more")
    else:
        print("Failed to traverse:", r_trav.text)

if __name__ == "__main__":
    run_audit()
