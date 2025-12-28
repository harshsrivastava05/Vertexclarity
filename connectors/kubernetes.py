import yaml
import os
try:
    from connectors.base import BaseConnector, Node, Edge
except ImportError:
    from .base import BaseConnector, Node, Edge

class KubernetesConnector(BaseConnector):
    def parse(self, file_path: str) -> tuple[list[Node], list[Edge]]:
        nodes = []
        edges = []
        
        if not os.path.exists(file_path):
            return [], []

        with open(file_path, 'r') as f:
            try:
                # k8s yaml can have multiple docs separated by ---
                docs = yaml.safe_load_all(f)
            except yaml.YAMLError:
                return [], []
            
            for doc in docs:
                if not doc: continue
                
                kind = doc.get('kind')
                metadata = doc.get('metadata', {})
                name = metadata.get('name')
                namespace = metadata.get('namespace', 'default')
                labels = metadata.get('labels', {}) or {}
                
                if kind == 'Deployment':
                    # Treat as Service for our graph
                    node_type = 'service'
                    node_id = f"{node_type}:{name}" # aligning ID with docker-compose for merging!
                    
                    spec = doc.get('spec', {}).get('template', {}).get('spec', {})
                    containers = spec.get('containers', [])
                    
                    # Merge properties from K8s
                    properties = {
                        "namespace": namespace,
                        "replicas": doc.get('spec', {}).get('replicas'),
                        "team": labels.get('team')
                    }
                    
                    nodes.append(Node(id=node_id, type=node_type, name=name, properties=properties))
                    
                    # Parse env vars for dependencies
                    for container in containers:
                        env = container.get('env', [])
                        for e in env:
                            val = e.get('value', '')
                            # Env var name often has hint
                            key = e.get('name', '')
                            
                            target_service = None
                            
                            if 'SERVICE_URL' in key and 'http' in val:
                                # http://payment-service.ecommerce.svc.cluster.local:8083
                                try:
                                    # Extract 'payment-service'
                                    # domain is service.namespace.svc...
                                    host_part = val.split('//')[1].split(':')[0]
                                    target_service = host_part.split('.')[0]
                                except:
                                    pass
                            
                            if target_service:
                                target_id = f"service:{target_service}"
                                edge_id = f"edge:{name}-calls-{target_service}"
                                edges.append(Edge(id=edge_id, type="calls", source=node_id, target=target_id))

        return nodes, edges
