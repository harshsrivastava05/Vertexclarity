import yaml
import os
# Adjust import for local running vs package
try:
    from connectors.base import BaseConnector, Node, Edge
except ImportError:
    from .base import BaseConnector, Node, Edge

class DockerComposeConnector(BaseConnector):
    def parse(self, file_path: str) -> tuple[list[Node], list[Edge]]:
        nodes = []
        edges = []

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return [], []

        with open(file_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}")
                return [], []

        services = data.get('services', {})

        for service_name, config in services.items():
            # Create Node
            # Determine type (service, database, cache) based on image or name or labels
            node_type = "service"
            labels = config.get('labels', {}) or {} # Handle None labels
            
            if 'type' in labels:
                node_type = labels['type']
            elif 'postgres' in config.get('image', ''):
                node_type = 'database'
            elif 'redis' in config.get('image', ''):
                node_type = 'cache'

            node_id = f"{node_type}:{service_name}"
            
            properties = {
                "team": labels.get('team', 'unknown'),
                "oncall": labels.get('oncall', 'unknown'),
                "image": config.get('image', config.get('build', 'local-build')),
            }
            
            # Extract ports
            ports = config.get('ports', [])
            if ports:
                properties['ports'] = ports

            nodes.append(Node(id=node_id, type=node_type, name=service_name, properties=properties))

            # Create Edges from depends_on
            depends_on = config.get('depends_on', [])
            if isinstance(depends_on, list):
                for dep in depends_on:
                    # We need to guess the type of the dependency. 
                    # For now, we'll try to look it up in the current services list to see if we can resolve it, 
                    # but easiest is to defer linking or make a generic assumption.
                    # Since we are iterating, we might not have seen all nodes. 
                    # However, we can construct the ID if we assume standard naming.
                    # Use a lookup later or just assume 'service' prefix if not found? 
                    # Actually, the problem says "infer dependencies".
                    # Let's try to infer target type from the name (e.g. ends in -db -> database) or look at the target service definition.
                    
                    target_config = services.get(dep, {})
                    target_labels = target_config.get('labels', {}) or {}
                    target_type = target_labels.get('type', 'service') # default to service
                    
                    # Heuristics if no label
                    if target_type == 'service':
                        if 'postgres' in target_config.get('image', '') or dep.endswith('-db'):
                            target_type = 'database'
                        elif 'redis' in target_config.get('image', '') or 'redis' in dep:
                            target_type = 'cache'
                    
                    target_id = f"{target_type}:{dep}"
                    
                    edge_id = f"edge:{service_name}-depends_on-{dep}"
                    edges.append(Edge(id=edge_id, type="depends_on", source=node_id, target=target_id))

            # Create Edges from environment variables (explicit URLs)
            env_vars = config.get('environment', [])
            env_dict = {}
            if isinstance(env_vars, list):
                for item in env_vars:
                    if '=' in item:
                        k, v = item.split('=', 1)
                        env_dict[k] = v
            elif isinstance(env_vars, dict):
                env_dict = env_vars

            for key, value in env_dict.items():
                target_service = None
                edge_type = "calls"
                
                if '_URL' in key:
                    # Extract service name from URL (e.g. http://auth-service:8081 -> auth-service)
                    # or postgresql://.../users-db... -> users-db
                    if 'http://' in value:
                        parts = value.split('http://')
                        if len(parts) > 1:
                            target_service = parts[1].split(':')[0]
                    elif 'postgresql://' in value or 'postgres://' in value:
                        # Extract host
                        # format: postgresql://user:pass@host:port/db
                        try:
                            target_service = value.split('@')[1].split(':')[0]
                            edge_type = "connects_to" # specific for DB
                        except:
                            pass
                    elif 'redis://' in value:
                         try:
                            target_service = value.split('redis://')[1].split(':')[0]
                            edge_type = "connects_to"
                         except:
                            pass
                
                if target_service and target_service in services:
                    # Resolve type
                    tgt_conf = services.get(target_service, {})
                    tgt_lbl = tgt_conf.get('labels', {}) or {}
                    tgt_type = tgt_lbl.get('type', 'service')
                     # Heuristics 
                    if tgt_type == 'service':
                        if 'postgres' in tgt_conf.get('image', '') or target_service.endswith('-db'):
                            tgt_type = 'database'
                        elif 'redis' in tgt_conf.get('image', '') or 'redis' in target_service:
                            tgt_type = 'cache'

                    target_id = f"{tgt_type}:{target_service}"
                    edge_id = f"edge:{service_name}-{edge_type}-{target_service}"
                    
                    # Avoid duplicates if depends_on already covered it? 
                    # depends_on is purely startup dependency, calls is functional. We can keep both or merge. 
                    # Let's keep distinct types as they mean different things.
                    edges.append(Edge(id=edge_id, type=edge_type, source=node_id, target=target_id))

        return nodes, edges
