import pytest
import os
from connectors.docker_compose import DockerComposeConnector
from connectors.teams import TeamsConnector
from graph.storage import GraphStorage

@pytest.fixture
def data_dir():
    return os.path.join(os.getcwd(), 'data')

def test_docker_compose_parsing(data_dir):
    conn = DockerComposeConnector()
    file_path = os.path.join(data_dir, 'docker-compose.yml')
    nodes, edges = conn.parse(file_path)
    
    assert len(nodes) > 0
    assert len(edges) > 0
    
    # Check for specific service
    service_names = [n.name for n in nodes if n.type == 'service']
    assert 'order-service' in service_names
    assert 'auth-service' in service_names
    
    # Check for database
    db_names = [n.name for n in nodes if n.type == 'database']
    assert 'users-db' in db_names

def test_teams_parsing(data_dir):
    conn = TeamsConnector()
    file_path = os.path.join(data_dir, 'teams.yaml')
    nodes, edges = conn.parse(file_path)
    
    assert len(nodes) > 0
    assert len(edges) > 0
    
    # Check platform team
    team_names = [n.name for n in nodes]
    assert 'platform-team' in team_names
    
    # Check ownership edge
    # Edge source should be team:platform-team, target should be something it owns
    platform_edges = [e for e in edges if e.source == 'team:platform-team']
    assert len(platform_edges) > 0

def test_graph_integrity():
    # Build a small in-memory graph
    storage = GraphStorage(persistence_file="test_graph.json")
    from connectors.base import Node, Edge
    
    n1 = Node("s:1", "service", "s1")
    n2 = Node("d:1", "database", "d1")
    e1 = Edge("e:1", "calls", "s:1", "d:1")
    
    storage.add_node(n1)
    storage.add_node(n2)
    storage.add_edge(e1)
    
    assert storage.graph.number_of_nodes() == 2
    assert storage.graph.number_of_edges() == 1
    
    # Clean up
    if os.path.exists("test_graph.json"):
        os.remove("test_graph.json")
