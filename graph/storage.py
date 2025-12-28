import networkx as nx
import json
import os
from typing import List, Dict, Any, Optional
# Adjust import for local vs package
try:
    from connectors.base import Node, Edge
except ImportError:
    from .connectors.base import Node, Edge

class GraphStorage:
    def __init__(self, persistence_file: str = "graph_data.json"):
        self.graph = nx.DiGraph()
        self.persistence_file = persistence_file
        self.load()

    def add_node(self, node: Node):
        """Upsert a node"""
        self.graph.add_node(node.id, type=node.type, name=node.name, **node.properties)

    def add_edge(self, edge: Edge):
        """Upsert an edge"""
        self.graph.add_edge(edge.source, edge.target, id=edge.id, type=edge.type, **edge.properties)

    def get_node(self, node_id: str) -> Optional[Dict]:
        if self.graph.has_node(node_id):
            return dict(id=node_id, **self.graph.nodes[node_id])
        return None

    def get_nodes_by_type(self, node_type: str) -> List[Dict]:
        return [
            dict(id=n, **self.graph.nodes[n]) 
            for n in self.graph.nodes 
            if self.graph.nodes[n].get('type') == node_type
        ]
    
    def get_all_nodes(self) -> List[Dict]:
         return [dict(id=n, **self.graph.nodes[n]) for n in self.graph.nodes]

    def delete_node(self, node_id: str):
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)

    def save(self):
        data = nx.node_link_data(self.graph)
        with open(self.persistence_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data)
            except (json.JSONDecodeError, IndexError, Exception) as e:
                print(f"Failed to load graph: {e}. Starting fresh.")
                self.graph = nx.DiGraph()
        else:
            self.graph = nx.DiGraph()

    def build_from_connectors(self, connectors: List[Any], files: List[str]):
        """
        Orchestrates running connectors and populating the graph.
        """
        all_nodes = []
        all_edges = []
        
        for connector, file_path in zip(connectors, files):
            nodes, edges = connector.parse(file_path)
            all_nodes.extend(nodes)
            all_edges.extend(edges)
            
        for node in all_nodes:
            self.add_node(node)
            
        for edge in all_edges:
            # Only add edge if both source/target exist? 
            # NetworkX adds missing nodes automatically, but they won't have properties.
            # Ideally we ensure all nodes are present. 
            self.add_edge(edge)
            
        self.save()
