import networkx as nx
from typing import Dict, Any

def traverse_graph(G: nx.Graph, root_id: str, depth: int = 3) -> Dict[str, Any]:
    """
    Performs a multi-hop traversal starting from root_id.
    Returns a tree structure representing the paths.
    """
    if not G.has_node(root_id):
        return {"error": "Node not found"}
        
    ego = nx.ego_graph(G, root_id, radius=depth, center=True, undirected=True)
    
    # We want to represent this as a hierarchical tree or just the subgraph nodes/edges.
    # The prompt says: Return traversal trees.
    # Let's generate a BFS tree from the ego graph.
    bfs_tree = nx.bfs_tree(ego, root_id, depth_limit=depth)
    
    def build_tree(node, current_depth):
        if current_depth >= depth:
            return {
                "id": node, 
                "type": G.nodes[node].get("type"),
                "children": []
            }
            
        children = []
        for child in bfs_tree.successors(node):
            children.append(build_tree(child, current_depth + 1))
            
        return {
            "id": node,
            "type": G.nodes[node].get("type"),
            "children": children
        }
        
    tree = build_tree(root_id, 0)
    
    return {
        "root": root_id,
        "depth": depth,
        "total_nodes": len(ego.nodes),
        "total_edges": len(ego.edges),
        "tree": tree
    }
