from typing import List, Dict, Any, Set
import networkx as nx

class QueryEngine:
    def __init__(self, storage):
        self.storage = storage

    @property
    def graph(self):
        return self.storage.graph

    def get_node(self, node_id: str) -> Dict:
        return self.storage.get_node(node_id)

    def get_nodes(self, type: str = None, **filters) -> List[Dict]:
        nodes = []
        if type:
            nodes = self.storage.get_nodes_by_type(type)
        else:
            nodes = self.storage.get_all_nodes()
        
        # Apply filters
        # Filter syntax: key=value
        if filters:
            filtered = []
            for n in nodes:
                match = True
                for k, v in filters.items():
                    # check properties
                    if n.get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(n)
            return filtered
        return nodes

    def downstream(self, node_id: str) -> List[Dict]:
        """All transitive dependencies (what this node calls/depends on)"""
        if not self.graph.has_node(node_id):
            return []
        # DFS successors
        descendants = nx.descendants(self.graph, node_id)
        return [self.get_node(n) for n in descendants]

    def upstream(self, node_id: str) -> List[Dict]:
         """All transitive dependents (what calls this node)"""
         if not self.graph.has_node(node_id):
            return []
         ancestors = nx.ancestors(self.graph, node_id)
         return [self.get_node(n) for n in ancestors]

    def blast_radius(self, node_id: str) -> Dict[str, Any]:
        """Full impact analysis: upstream + downstream + affected teams"""
        if not self.graph.has_node(node_id):
            return {}

        up = self.upstream(node_id)
        down = self.downstream(node_id)
        
        # Teams affected: check ownership of upstream nodes (things that depend on this)
        # If I am a DB, and Service A depends on me, then Service A breaks. 
        # The team owning Service A is affected.
        affected_teams = set()
        
        # Also include owner of the node itself? Maybe.
        
        # Logic: If X fails, who cares? 
        # 1. The team owning X (they fix it).
        # 2. The teams owning services that depend on X (they are broken).
        
        # Find owners of upstream nodes
        all_impacted_nodes = [self.get_node(node_id)] + up
        
        for n in all_impacted_nodes:
            # Check ownership edges incoming to this node
            # OR check 'team' property if available (faster)
            if 'team' in n:
                affected_teams.add(n['team'])
            
            # Also check 'owns' edges from Team nodes
            predecessors = self.graph.predecessors(n['id'])
            for p in predecessors:
                p_node = self.graph.nodes[p]
                if p_node.get('type') == 'team':
                     affected_teams.add(p_node.get('name'))

        return {
            "node": self.get_node(node_id),
            "upstream_dependents_count": len(up),
            "downstream_dependencies_count": len(down),
            "affected_teams": list(affected_teams),
            "upstream_nodes": [n['id'] for n in up],
            "downstream_nodes": [n['id'] for n in down]
        }

    def path(self, from_id: str, to_id: str) -> List[str]:
        """Shortest path between nodes"""
        try:
            return nx.shortest_path(self.graph, source=from_id, target=to_id)
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    def get_owner(self, node_id: str) -> str:
        """Find owning team"""
        node = self.get_node(node_id)
        if not node:
            return "Unknown"
        
        if 'team' in node and node['team'] != 'unknown':
            return node['team']
            
        # Check for 'owns' edge
        predecessors = self.graph.predecessors(node_id)
        for p in predecessors:
             if self.graph.nodes[p].get('type') == 'team':
                 # Verify edge type is 'owns'
                 if self.graph.get_edge_data(p, node_id).get('type') == 'owns':
                     return self.graph.nodes[p].get('name')
        
        return "Unknown"
