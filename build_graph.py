from connectors.docker_compose import DockerComposeConnector
from connectors.teams import TeamsConnector
from connectors.kubernetes import KubernetesConnector
from graph.storage import GraphStorage
import os

def main():
    print("Initializing Connectors...")
    dc_conn = DockerComposeConnector()
    teams_conn = TeamsConnector()
    k8s_conn = KubernetesConnector()

    data_dir = os.path.join(os.getcwd(), 'data')
    
    files = [
        os.path.join(data_dir, 'docker-compose.yml'),
        os.path.join(data_dir, 'teams.yaml'),
        os.path.join(data_dir, 'k8s-deployments.yaml')
    ]
    
    print(f"Reading from {data_dir}...")
    
    storage = GraphStorage()
    print("Building Graph...")
    
    # We run connectors sequentially. 
    # Note: simple merging logic (last write wins for same ID)
    storage.build_from_connectors(
        [dc_conn, teams_conn, k8s_conn],
        files
    )
    
    print(f"Graph built successfully with {storage.graph.number_of_nodes()} nodes and {storage.graph.number_of_edges()} edges.")
    print("Saved to graph_data.json")

if __name__ == "__main__":
    main()
