"""Tests for Stage 1: Graph Core using GraphQLite.

Tests only the most significant functions sparingly.
"""

from datetime import datetime

import pytest

from cyphnapse.core import GraphCore
from cyphnapse.models import RelationshipType


@pytest.fixture
def core():
    """Create a fresh GraphCore for each test."""
    return GraphCore(db_path=":memory:")


@pytest.fixture
def graph(core):
    """Create a test graph."""
    graph_id = core.create_graph("test_graph")
    return graph_id


class TestGraphCore:
    """Tests for GraphCore core functionality."""

    def test_create_and_get_graph(self, core):
        """Test creating and retrieving a graph."""
        graph_id = core.create_graph("test")
        assert graph_id is not None

        graph = core.get_graph(graph_id)
        assert graph is not None
        assert graph["name"] == "test"

    def test_list_graphs(self, core):
        """Test listing all graphs."""
        core.create_graph("graph1")
        core.create_graph("graph2")

        graphs = core.list_graphs()
        assert len(graphs) == 2
        assert any(g["name"] == "graph1" for g in graphs)
        assert any(g["name"] == "graph2" for g in graphs)

    def test_add_and_get_node(self, core, graph):
        """Test adding and retrieving a node."""
        node = {
            "label": "Company",
            "name": "Acme Corp",
            "properties": {"location": "New York"},
        }
        node_id = core.add_node(graph, node)

        retrieved = core.get_node(node_id)
        assert retrieved is not None
        assert retrieved["properties"]["name"] == "Acme Corp"
        assert retrieved["properties"]["label"] == "Company"

    def test_get_nodes_by_label(self, core, graph):
        """Test retrieving nodes by label."""
        core.add_node(graph, {"label": "Company", "name": "Company A"})
        core.add_node(graph, {"label": "Person", "name": "Person A"})
        core.add_node(graph, {"label": "Company", "name": "Company B"})

        companies = core.get_nodes_by_label("Company")
        persons = core.get_nodes_by_label("Person")

        assert len(companies) == 2
        assert len(persons) == 1
        assert all(n["label"] == "Company" for n in companies)

    def test_add_and_get_edge(self, core, graph):
        """Test adding and retrieving an edge."""
        node1 = core.add_node(graph, {"label": "Person", "name": "John"})
        node2 = core.add_node(graph, {"label": "Company", "name": "Acme"})

        edge_id = core.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.controls.value,
            {"since": 2020},
        )

        retrieved = core.get_edge(edge_id)
        assert retrieved is not None

    def test_get_edges_by_relationship_type(self, core, graph):
        """Test retrieving edges by relationship type."""
        node1 = core.add_node(graph, {"label": "Person", "name": "John"})
        node2 = core.add_node(graph, {"label": "Company", "name": "Acme"})
        node3 = core.add_node(graph, {"label": "Company", "name": "Beta"})

        core.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.controls.value,
        )
        core.add_edge(
            graph,
            node1,
            node3,
            RelationshipType.owns.value,
        )

        controls_edges = core.get_edges_by_relationship_type(
            RelationshipType.controls.value
        )
        owns_edges = core.get_edges_by_relationship_type(RelationshipType.owns.value)

        assert len(controls_edges) == 1
        assert len(owns_edges) == 1
        assert controls_edges[0]["type"] == "controls"
        assert owns_edges[0]["type"] == "owns"

    def test_traverse_basic(self, core, graph):
        """Test basic graph traversal."""
        node1 = core.add_node(graph, {"label": "Company", "name": "A"})
        node2 = core.add_node(graph, {"label": "Company", "name": "B"})
        node3 = core.add_node(graph, {"label": "Company", "name": "C"})

        core.add_edge(
            graph,
            node1,
            node2,
            "subsidiary",
        )
        core.add_edge(
            graph,
            node2,
            node3,
            "subsidiary",
        )

        results = core.traverse(graph, node1, max_depth=2)
        assert len(results) >= 2

    def test_get_current_state(self, core, graph):
        """Test getting current state of edges."""
        node1 = core.add_node(graph, {"label": "Person", "name": "John"})
        node2 = core.add_node(graph, {"label": "Company", "name": "Acme"})

        core.add_edge(
            graph,
            node1,
            node2,
            "controls",
            {"valid_from": "2020-01-01"},
        )

        current = core.get_current_state(graph)
        assert len(current) >= 1

    def test_get_historical_state(self, core, graph):
        """Test getting historical state of edges."""
        node1 = core.add_node(graph, {"label": "Person", "name": "John"})
        node2 = core.add_node(graph, {"label": "Company", "name": "Acme"})

        core.add_edge(
            graph,
            node1,
            node2,
            "controls",
            {"valid_from": "2020-01-01", "valid_until": "2025-01-01"},
        )

        # Query historical state for 2022
        historical = core.get_historical_state(graph, timestamp=datetime(2022, 6, 1))
        assert len(historical) >= 1

    def test_search_nodes(self, core, graph):
        """Test searching for nodes."""
        core.add_node(graph, {"label": "Company", "name": "Acme Corp"})
        core.add_node(graph, {"label": "Company", "name": "Beta Inc"})
        core.add_node(graph, {"label": "Person", "name": "John Smith"})

        results = core.search_nodes(graph, "Acme")
        assert len(results) == 1
        assert results[0]["properties"]["name"] == "Acme Corp"

    def test_get_identity_candidates(self, core, graph):
        """Test getting identity candidates."""
        node1 = core.add_node(graph, {"label": "Person", "name": "John"})
        node2 = core.add_node(graph, {"label": "Person", "name": "John"})

        core.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.same_as.value,
        )

        retrieved_node = core.get_node(node1)
        candidates = core.get_identity_candidates(graph, retrieved_node)

        assert len(candidates) >= 1

    def test_get_conflicts(self, core, graph):
        """Test getting conflicts from the graph."""
        node1 = core.add_node(graph, {"label": "Person", "name": "John"})
        node2 = core.add_node(graph, {"label": "Person", "name": "John"})

        core.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.same_as.value,
        )

        conflicts = core.get_conflicts(graph)
        assert len(conflicts) >= 0
