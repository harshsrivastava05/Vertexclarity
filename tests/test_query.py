import pytest
import networkx as nx
from graph.storage import GraphStorage
from graph.query import QueryEngine
from connectors.base import Node, Edge
import os

@pytest.fixture
def test_graph():
    storage = GraphStorage(persistence_file="test_query_graph.json")
    storage.graph = nx.DiGraph() # Reset
    
    # A -> B -> C
    # A -> D
    nodes = [
        Node("A", "service", "Service A", {"team": "Team A"}),
        Node("B", "service", "Service B", {"team": "Team B"}),
        Node("C", "database", "DB C", {"team": "Team B"}),
        Node("D", "cache", "Cache D", {"team": "Team A"}),
        Node("Team A", "team", "Team A"),
        Node("Team B", "team", "Team B")
    ]
    edges = [
        Edge("1", "calls", "A", "B"),
        Edge("2", "calls", "B", "C"),
        Edge("3", "calls", "A", "D"),
        Edge("4", "owns", "Team A", "A"),
        Edge("5", "owns", "Team B", "B")
    ]
    
    for n in nodes: storage.add_node(n)
    for e in edges: storage.add_edge(e)
    
    return QueryEngine(storage)

def test_downstream(test_graph):
    # A depends on B and D directly, and C transitive
    down = test_graph.downstream("A")
    ids = [n['id'] for n in down]
    assert "B" in ids
    assert "C" in ids
    assert "D" in ids
    assert len(ids) == 3

def test_upstream(test_graph):
    # C is used by B, which is used by A
    # Also B is owned by Team B, A is owned by Team A
    # So ancestors of C include: B, A, Team B, Team A
    up = test_graph.upstream("C")
    ids = [n['id'] for n in up]
    assert "B" in ids
    assert "A" in ids
    assert "Team B" in ids
    assert "Team A" in ids
    assert len(ids) == 4

def test_blast_radius(test_graph):
    # If C fails (DB C)
    # Upstream: B, A
    # Affected Teams: Team B (owns B), Team A (owns A)
    # Also Team B owns C itself? In our mock edge "owns" is implied by prop or edge
    
    radius = test_graph.blast_radius("C")
    
    # Predecessors: B, A, Team B, Team A
    assert radius['upstream_dependents_count'] == 4
    assert "Team A" in radius['affected_teams']
    assert "Team B" in radius['affected_teams']

def test_get_owner(test_graph):
    assert test_graph.get_owner("A") == "Team A"
    assert test_graph.get_owner("B") == "Team B"

def tearDown():
    if os.path.exists("test_query_graph.json"):
        os.remove("test_query_graph.json")
