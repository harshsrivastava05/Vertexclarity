from typing import List, Dict, Any, Set
import networkx as nx

class QueryEngine:
    def __init__(self, storage):
        self.storage = storage

    @property
    def graph(self):
        return self.storage.graph

    def _resolve_node_id(self, query: str) -> str:
        """
        Fuzzy matches a query string to a valid node ID.
        Strategy:
        1. Exact match
        2. Case-insensitive match
        3. Substring match (if query is part of ID)
        4. Name property match
        """
        if not query:
            return None
            
        # 1. Exact Match
        if self.graph.has_node(query):
            return query
            
        # 2. Case Insensitive & 3. Substring & 4. Name
        query_lower = query.lower()
        candidates = []
        
        for node_id, data in self.graph.nodes(data=True):
            # Check ID
            if query_lower == node_id.lower():
                return node_id
            
            # Check Name property
            node_name = data.get('name', '').lower()
            if query_lower == node_name:
                return node_id
                
            # Substring in ID (e.g. "orders" matches "service:order-service")
            if query_lower in node_id.lower():
                candidates.append(node_id)
                
            # Substring in Name
            if query_lower in node_name:
                candidates.append(node_id)
                
            # Handle singular/plural (simple heuristic)
            # if query is "user-db", match "users-db"
            if query_lower + 's' in node_name or query_lower + 's' in node_id:
                 candidates.append(node_id)
            if query_lower.rstrip('s') in node_name or query_lower.rstrip('s') in node_id:
                 candidates.append(node_id)

        # Return best candidate (shortest ID usually means less noise, e.g. 'redis' -> 'cache:redis-main' vs 'service:redis-consumer')
        if candidates:
            # Sort by length, picking the shortest ID as best bet
            candidates.sort(key=len)
            return candidates[0]
            
        return None

    def get_node(self, node_id: str) -> Dict:
        resolved_id = self._resolve_node_id(node_id)
        if resolved_id:
            return self.storage.get_node(resolved_id)
        return None

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
        resolved_id = self._resolve_node_id(node_id)
        if not resolved_id or not self.graph.has_node(resolved_id):
            return []
        # DFS successors
        descendants = nx.descendants(self.graph, resolved_id)
        return [self.get_node(n) for n in descendants]

    def upstream(self, node_id: str) -> List[Dict]:
         """All transitive dependents (what calls this node)"""
         resolved_id = self._resolve_node_id(node_id)
         if not resolved_id or not self.graph.has_node(resolved_id):
            return []
         ancestors = nx.ancestors(self.graph, resolved_id)
         return [self.get_node(n) for n in ancestors]

    def blast_radius(self, node_id: str) -> Dict[str, Any]:
        """Full impact analysis: upstream + downstream + affected teams"""
        resolved_id = self._resolve_node_id(node_id)
        if not resolved_id or not self.graph.has_node(resolved_id):
            return {}

        up = self.upstream(resolved_id)
        down = self.downstream(resolved_id)
        
        affected_teams = set()
        
        # Find owners of upstream nodes
        all_impacted_nodes = [self.get_node(resolved_id)] + up
        
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

        # Build Rich Impact Tree
        impact_tree = {
            "direct_dependents": [],
            "transitive_dependents": []
        }
        
        # Direct Upstream (Dependents)
        for predecessor in self.graph.predecessors(resolved_id):
            edge_data = self.graph.get_edge_data(predecessor, resolved_id)
            impact_tree["direct_dependents"].append({
                "id": predecessor,
                "relationship": edge_data.get("type", "connected_to"),
                "node_data": self.get_node(predecessor)
            })

        return {
            "query_node": resolved_id,
            "node_details": self.get_node(resolved_id),
            "summary": {
                "upstream_count": len(up),
                "downstream_count": len(down),
                "affected_teams": list(affected_teams)
            },
            "impact_analysis": impact_tree,
            "raw_graph_context": {
                "upstream_nodes": up,
                "downstream_nodes": down
            }
        }

    def path(self, from_id: str, to_id: str) -> List[str]:
        """Shortest path between nodes"""
        src = self._resolve_node_id(from_id)
        dst = self._resolve_node_id(to_id)
        
        if not src or not dst:
            return []
            
        try:
            return nx.shortest_path(self.graph, source=src, target=dst)
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    def get_owner(self, node_id: str) -> str:
        """Find owning team"""
        resolved_id = self._resolve_node_id(node_id)
        if not resolved_id:
             return "Unknown"
             
        node = self.get_node(resolved_id)
        if not node:
            return "Unknown"
        
        if 'team' in node and node['team'] != 'unknown':
            return node['team']
            
        # Check for 'owns' edge
        predecessors = self.graph.predecessors(resolved_id)
        for p in predecessors:
             if self.graph.nodes[p].get('type') == 'team':
                 # Verify edge type is 'owns'
                 if self.graph.get_edge_data(p, resolved_id).get('type') == 'owns':
                     return self.graph.nodes[p].get('name')
        
        return "Unknown"
