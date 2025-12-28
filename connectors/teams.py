import yaml
import os
try:
    from connectors.base import BaseConnector, Node, Edge
except ImportError:
    from .base import BaseConnector, Node, Edge

class TeamsConnector(BaseConnector):
    def parse(self, file_path: str) -> tuple[list[Node], list[Edge]]:
        nodes = []
        edges = []

        if not os.path.exists(file_path):
            return [], []

        with open(file_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                return [], []
        
        teams = data.get('teams', [])
        
        for team in teams:
            team_name = team.get('name')
            node_id = f"team:{team_name}"
            
            properties = {
                "lead": team.get('lead'),
                "slack": team.get('slack_channel'),
                "pagerduty": team.get('pagerduty_schedule')
            }
            
            nodes.append(Node(id=node_id, type="team", name=team_name, properties=properties))
            
            # Ownership edges
            owns = team.get('owns', [])
            for item in owns:
                # We don't know the type of the owned item purely from teams.yaml easily, 
                # but we can try to guess or simple use a generic lookup or wait for graph merge.
                # Since we need to emit an Edge with a valid target ID, and our Node IDs are type:name...
                # We need to know the type.
                # However, the assignment says "Extract team entities, Link ownership relationships".
                # If we emit the edge with a guessed type, it might not match the node from docker-compose.
                # Strategy: We can emit multiple edges or try to be smart. 
                # Better: In the graph loader, we can handle ID application. 
                # BUT, here we must return standard Edge objects.
                # Let's assume standard conventions: -db suffix is database, redis is cache.
                
                target_type = "service" # Default
                if item.endswith('-db'):
                    target_type = "database"
                elif 'redis' in item:
                    target_type = "cache"
                
                # Check for "service" suffix to confirm? 
                # Actually, docker-compose connector handles the authoritative typing.
                # Maybe we can just return a partial edge or update the node properties?
                # "Extract team ownership from labels" in Docker Compose connector is ALREADY doing this (inverse).
                # The Teams file adds explicit "owns" list. 
                # Let's output "owns" edges.
                
                target_id = f"{target_type}:{item}"
                edge_id = f"edge:{team_name}-owns-{item}"
                
                edges.append(Edge(id=edge_id, type="owns", source=node_id, target=target_id))

        return nodes, edges
