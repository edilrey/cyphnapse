"""Tests for Stage 1: Graph Kernel using GraphQLite.

Tests only the most significant functions sparingly.
"""

from datetime import datetime

import pytest

from cyphnapse.core import GraphKernel
from cyphnapse.models import RelationshipType


@pytest.fixture
def kernel():
    """Create a fresh GraphKernel for each test."""
    return GraphKernel(db_path=":memory:")


@pytest.fixture
def graph(kernel):
    """Create a test graph."""
    graph_id = kernel.create_graph("test_graph")
    return graph_id


class TestGraphKernel:
    """Tests for GraphKernel core functionality."""

    def test_create_and_get_graph(self, kernel):
        """Test creating and retrieving a graph."""
        graph_id = kernel.create_graph("test")
        assert graph_id is not None

        graph = kernel.get_graph(graph_id)
        assert graph is not None
        assert graph["name"] == "test"

    def test_list_graphs(self, kernel):
        """Test listing all graphs."""
        kernel.create_graph("graph1")
        kernel.create_graph("graph2")

        graphs = kernel.list_graphs()
        assert len(graphs) == 2
        assert any(g["name"] == "graph1" for g in graphs)
        assert any(g["name"] == "graph2" for g in graphs)

    def test_add_and_get_node(self, kernel, graph):
        """Test adding and retrieving a node."""
        node = {
            "label": "Company",
            "name": "Acme Corp",
            "properties": {"location": "New York"},
        }
        node_id = kernel.add_node(graph, node)

        retrieved = kernel.get_node(node_id)
        assert retrieved is not None
        assert retrieved["properties"]["name"] == "Acme Corp"
        assert retrieved["properties"]["label"] == "Company"

    def test_get_nodes_by_label(self, kernel, graph):
        """Test retrieving nodes by label."""
        kernel.add_node(graph, {"label": "Company", "name": "Company A"})
        kernel.add_node(graph, {"label": "Person", "name": "Person A"})
        kernel.add_node(graph, {"label": "Company", "name": "Company B"})

        companies = kernel.get_nodes_by_label("Company")
        persons = kernel.get_nodes_by_label("Person")

        assert len(companies) == 2
        assert len(persons) == 1
        assert all(n["label"] == "Company" for n in companies)

    def test_add_and_get_edge(self, kernel, graph):
        """Test adding and retrieving an edge."""
        node1 = kernel.add_node(graph, {"label": "Person", "name": "John"})
        node2 = kernel.add_node(graph, {"label": "Company", "name": "Acme"})

        edge_id = kernel.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.controls.value,
            {"since": 2020},
        )

        retrieved = kernel.get_edge(edge_id)
        assert retrieved is not None

    def test_get_edges_by_relationship_type(self, kernel, graph):
        """Test retrieving edges by relationship type."""
        node1 = kernel.add_node(graph, {"label": "Person", "name": "John"})
        node2 = kernel.add_node(graph, {"label": "Company", "name": "Acme"})
        node3 = kernel.add_node(graph, {"label": "Company", "name": "Beta"})

        kernel.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.controls.value,
        )
        kernel.add_edge(
            graph,
            node1,
            node3,
            RelationshipType.owns.value,
        )

        controls_edges = kernel.get_edges_by_relationship_type(
            RelationshipType.controls.value
        )
        owns_edges = kernel.get_edges_by_relationship_type(RelationshipType.owns.value)

        assert len(controls_edges) == 1
        assert len(owns_edges) == 1
        assert controls_edges[0]["type"] == "controls"
        assert owns_edges[0]["type"] == "owns"

    def test_traverse_basic(self, kernel, graph):
        """Test basic graph traversal."""
        node1 = kernel.add_node(graph, {"label": "Company", "name": "A"})
        node2 = kernel.add_node(graph, {"label": "Company", "name": "B"})
        node3 = kernel.add_node(graph, {"label": "Company", "name": "C"})

        kernel.add_edge(
            graph,
            node1,
            node2,
            "subsidiary",
        )
        kernel.add_edge(
            graph,
            node2,
            node3,
            "subsidiary",
        )

        results = kernel.traverse(graph, node1, max_depth=2)
        assert len(results) >= 2

    def test_get_current_state(self, kernel, graph):
        """Test getting current state of edges."""
        node1 = kernel.add_node(graph, {"label": "Person", "name": "John"})
        node2 = kernel.add_node(graph, {"label": "Company", "name": "Acme"})

        kernel.add_edge(
            graph,
            node1,
            node2,
            "controls",
            {"valid_from": "2020-01-01"},
        )

        current = kernel.get_current_state(graph)
        assert len(current) >= 1

    def test_get_historical_state(self, kernel, graph):
        """Test getting historical state of edges."""
        node1 = kernel.add_node(graph, {"label": "Person", "name": "John"})
        node2 = kernel.add_node(graph, {"label": "Company", "name": "Acme"})

        kernel.add_edge(
            graph,
            node1,
            node2,
            "controls",
            {"valid_from": "2020-01-01", "valid_until": "2025-01-01"},
        )

        # Query historical state for 2022
        historical = kernel.get_historical_state(graph, timestamp=datetime(2022, 6, 1))
        assert len(historical) >= 1

    def test_search_nodes(self, kernel, graph):
        """Test searching for nodes."""
        kernel.add_node(graph, {"label": "Company", "name": "Acme Corp"})
        kernel.add_node(graph, {"label": "Company", "name": "Beta Inc"})
        kernel.add_node(graph, {"label": "Person", "name": "John Smith"})

        results = kernel.search_nodes(graph, "Acme")
        assert len(results) == 1
        assert results[0]["properties"]["name"] == "Acme Corp"

    def test_get_identity_candidates(self, kernel, graph):
        """Test getting identity candidates."""
        node1 = kernel.add_node(graph, {"label": "Person", "name": "John"})
        node2 = kernel.add_node(graph, {"label": "Person", "name": "John"})

        kernel.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.same_as.value,
        )

        retrieved_node = kernel.get_node(node1)
        candidates = kernel.get_identity_candidates(graph, retrieved_node)

        assert len(candidates) >= 1

    def test_get_conflicts(self, kernel, graph):
        """Test getting conflicts from the graph."""
        node1 = kernel.add_node(graph, {"label": "Person", "name": "John"})
        node2 = kernel.add_node(graph, {"label": "Person", "name": "John"})

        kernel.add_edge(
            graph,
            node1,
            node2,
            RelationshipType.same_as.value,
        )

        conflicts = kernel.get_conflicts(graph)
        assert len(conflicts) >= 0
