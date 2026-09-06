"""Graph Memory Layer for AI Agents using GraphQLite (Cypher queries over SQLite)."""

import uuid
from datetime import datetime
from typing import Any

from graphqlite import Graph

__all__ = [
    "GraphKernel",
]


class GraphKernel:
    """Core graph memory functionality using GraphQLite Cypher queries."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize the GraphQLite graph kernel.

        Args:
            db_path: Path to SQLite database file (':memory:' for in-memory)
        """
        self.graph = Graph(db_path)

    def create_graph(self, name: str) -> str:
        """Create a new graph.

        Args:
            name: Name for the new graph

        Returns:
            Graph ID of the created graph
        """
        # GraphQLite creates graphs implicitly with unique IDs
        # Use UUID-based ID for identification
        graph_id = f"graph_{uuid.uuid4().hex[:8]}"
        # Store the name in the graph's properties
        self.graph.upsert_node(graph_id, {"name": name}, label="GraphMeta")
        return graph_id

    def get_graph(self, graph_id: str) -> dict[str, Any] | None:
        """Get a graph by ID.

        Args:
            graph_id: ID of the graph to retrieve

        Returns:
            Graph dict if found, None otherwise
        """
        try:
            results = self.graph.query(
                f"MATCH (g:GraphMeta {{id: '{graph_id}'}}) RETURN g"
            )
            if results:
                g = results[0]["g"]
                return {
                    "id": g["properties"]["id"],
                    "name": g["properties"].get("name", "default"),
                }
        except Exception:
            pass
        return None

    def list_graphs(self) -> list[dict[str, Any]]:
        """List all graphs.

        Returns:
            List of Graph objects
        """
        graphs = []
        try:
            results = self.graph.query("MATCH (g:GraphMeta) RETURN g")
            for record in results:
                g = record["g"]
                graphs.append(
                    {
                        "id": g["properties"]["id"],
                        "name": g["properties"].get("name", "default"),
                    }
                )
        except Exception:
            pass
        return graphs

    def add_node(self, graph_id: str, node: dict[str, Any]) -> str:
        """Add a node to a graph using GraphQLite.

        Args:
            graph_id: ID of the graph (not used in GraphQLite, graphs are global)
            node: Node data dict with properties and optional label

        Returns:
            Node key/ID
        """
        label = node.get("label", "Entity")
        name = node.get("name", "")
        properties = node.get("properties", {})

        # Add metadata for graph tracking
        properties["graph_id"] = graph_id
        if name:
            properties["name"] = name

        # Generate a unique node ID
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        properties["node_id"] = node_id

        # Use upsert_node to create the node
        self.graph.upsert_node(node_id, properties, label=label)

        return node_id

    def get_node(self, node_key: str) -> dict[str, Any] | None:
        """Get a node by key.

        Args:
            node_key: Key of the node to retrieve

        Returns:
            Node data dict if found, None otherwise
        """
        try:
            results = self.graph.query(f"MATCH (n {{node_id: '{node_key}'}}) RETURN n")
            if results:
                n = results[0]["n"]
                return {
                    "id": n["properties"]["node_id"],
                    "label": list(n.labels)[0] if n.labels else "Entity",
                    "properties": dict(n["properties"]),
                }
        except Exception:
            pass
        return None

    def get_nodes_by_label(self, label: str) -> list[dict[str, Any]]:
        """Get nodes by label.

        Args:
            label: Node label/type

        Returns:
            List of Node objects
        """
        results = self.graph.query(f"MATCH (n:{label}) RETURN n")
        nodes = []
        for record in results:
            n = record["n"]
            nodes.append(
                {
                    "id": n["properties"]["node_id"],
                    "label": label,
                    "properties": dict(n["properties"]),
                }
            )
        return nodes

    def add_edge(
        self,
        graph_id: str,
        source_node_key: str,
        target_node_key: str,
        relationship_type: str,
        edge_properties: dict[str, Any] | None = None,
    ) -> str:
        """Add an edge between two nodes using GraphQLite.

        Args:
            graph_id: ID of the graph (not used in GraphQLite, graphs are global)
            source_node_key: Key of the source node
            target_node_key: Key of the target node
            relationship_type: Type of relationship
            edge_properties: Optional edge properties

        Returns:
            Edge key
        """
        properties = edge_properties or {}

        # Add graph_id metadata
        properties["graph_id"] = graph_id

        # Generate a unique edge ID
        edge_id = f"edge_{uuid.uuid4().hex[:8]}"
        properties["edge_id"] = edge_id

        # Use upsert_edge to create the relationship
        self.graph.upsert_edge(
            source_node_key,
            target_node_key,
            properties,
            rel_type=relationship_type,
        )

        return edge_id

    def get_edge(self, edge_key: str) -> dict[str, Any] | None:
        """Get an edge by key.

        Args:
            edge_key: Key of the edge to retrieve

        Returns:
            Edge data dict if found, None otherwise
        """
        # GraphQLite edges are relationships, not nodes
        # Use Cypher to find the edge
        try:
            results = self.graph.query(
                f"MATCH ()-[r {{edge_id: '{edge_key}'}}]->() RETURN r"
            )
            if results:
                r = results[0]["r"]
                return {
                    "id": r["properties"]["edge_id"],
                    "type": type(r).__name__,
                    "properties": dict(r["properties"]),
                }
        except Exception:
            pass
        return None

    def get_edges_by_relationship_type(
        self, relationship_type: str
    ) -> list[dict[str, Any]]:
        """Get edges by relationship type.

        Args:
            relationship_type: Type of relationship to filter by

        Returns:
            List of Edge objects
        """
        results = self.graph.query(f"MATCH ()-[r:{relationship_type}]->() RETURN r")
        edges = []
        for record in results:
            r = record["r"]
            edges.append(
                {
                    "id": r["properties"]["edge_id"],
                    "type": type(r).__name__,
                    "properties": dict(r["properties"]),
                }
            )
        return edges

    def traverse(
        self,
        graph_id: str,
        start_node_key: str,
        max_depth: int = 5,
        relationship_filters: list[str] | None = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """Traverse the graph from a starting node using Cypher.

        Args:
            graph_id: ID of the graph (not used in GraphQLite)
            start_node_key: ID of the starting node
            max_depth: Maximum traversal depth
            relationship_filters: Optional list of relationship types to filter by
            direction: Traversal direction ('both', 'incoming', 'outgoing')

        Returns:
            List of traversal results
        """
        # Get internal ID for the start node
        start_internal_id = self._get_internal_id(start_node_key)
        if start_internal_id is None:
            return []

        # Build Cypher query based on direction
        filters_str = ""
        if relationship_filters:
            filter_list = [f"'{f}'" for f in relationship_filters]
            filters_str = f"AND type(r) IN [{','.join(filter_list)}]"

        if direction == "outgoing":
            query = f"""
            MATCH (start)-[r]->(end)
            WHERE id(start) = {start_internal_id}
            {filters_str}
            RETURN start, r, end
            """
        elif direction == "incoming":
            query = f"""
            MATCH (start)<-[r]-(end)
            WHERE id(end) = {start_internal_id}
            {filters_str}
            RETURN start, r, end
            """
        else:  # both
            query = f"""
            MATCH p = (start)-[r*0..{max_depth}]->(end)
            WHERE id(start) = {start_internal_id}
            {filters_str}
            RETURN p
            """

        results = self.graph.query(query)

        traversal_result = []
        for record in results:
            path = record.get("p")
            if path:
                traversal_result.append(
                    {
                        "path": str(path),
                        "start_node": start_node_key,
                        "max_depth": max_depth,
                    }
                )
            else:
                # Single edge result
                start = record.get("start")
                r = record.get("r")
                end = record.get("end")
                if start and r and end:
                    start_id = start["properties"]["node_id"]
                    end_id = end["properties"]["node_id"]
                    rel_name = type(r).__name__
                    traversal_result.append(
                        {
                            "path": (f"({start_id})-[{rel_name}]->({end_id})"),
                            "start_node": start_node_key,
                            "max_depth": 1,
                        }
                    )

        return traversal_result

    def _get_internal_id(self, node_key: str) -> int | None:
        """Get internal node ID from node_key."""
        try:
            results = self.graph.query(
                f"MATCH (n {{node_id: '{node_key}'}}) RETURN id(n) as internal_id"
            )
            if results:
                return results[0]["internal_id"]
        except Exception:
            pass
        return None

    def get_current_state(
        self, graph_id: str, node_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get current state of edges in the graph.

        Args:
            graph_id: ID of the graph
            node_id: Optional node ID to filter by

        Returns:
            List of Edge objects representing current state
        """
        # GraphQLite doesn't have explicit valid_from/valid_until in basic API
        # We'll return all edges
        try:
            if node_id:
                internal_id = self._get_internal_id(node_id)
                if internal_id is None:
                    return []
                results = self.graph.query(
                    f"MATCH (n)-[r]->() WHERE id(n) = {internal_id} RETURN r"
                )
            else:
                results = self.graph.query("MATCH ()-[r]->() RETURN r")

            edges = []
            for record in results:
                r = record["r"]
                edges.append(
                    {
                        "id": r["properties"]["edge_id"],
                        "type": type(r).__name__,
                        "properties": dict(r["properties"]),
                    }
                )
            return edges
        except Exception:
            return []

    def get_historical_state(
        self,
        graph_id: str,
        node_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get historical state of edges in the graph.

        Args:
            graph_id: ID of the graph
            node_id: Optional node ID to filter by
            timestamp: Optional timestamp to check

        Returns:
            List of Edge objects representing historical state
        """
        # GraphQLite basic API doesn't support temporal queries natively
        # We'll return all edges and let the caller filter by properties
        try:
            if node_id:
                internal_id = self._get_internal_id(node_id)
                if internal_id is None:
                    return []
                results = self.graph.query(
                    f"MATCH (n)-[r]->() WHERE id(n) = {internal_id} RETURN r"
                )
            else:
                results = self.graph.query("MATCH ()-[r]->() RETURN r")

            edges = []
            for record in results:
                r = record["r"]
                props = dict(r["properties"])
                # Check if there are temporal properties
                valid_from = props.get("valid_from")
                valid_until = props.get("valid_until")

                # Filter by timestamp if provided
                if timestamp and (valid_from or valid_until):
                    ts = timestamp
                    if valid_from and valid_until:
                        # Keep edge if valid_from <= timestamp <= valid_until
                        if ts < valid_from or ts > valid_until:
                            continue
                    elif valid_from:
                        if ts < valid_from:
                            continue
                    elif valid_until:
                        if ts > valid_until:
                            continue

                edges.append(
                    {
                        "id": r["properties"]["edge_id"],
                        "type": type(r).__name__,
                        "properties": props,
                    }
                )
            return edges
        except Exception:
            return []

    def get_identity_candidates(
        self,
        graph_id: str,
        node: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Get identity candidates for a node.

        Args:
            graph_id: ID of the graph
            node: Node data with properties

        Returns:
            List of Node objects that are identity candidates
        """
        name = node.get("name", "")
        label = node.get("label", "Entity")
        node_id = node.get("id", "")

        # Use Cypher to find nodes with same name and label
        query = f"""
        MATCH (n:{label})
        WHERE n.name = '{name}'
        AND n.node_id <> '{node_id}'
        RETURN n
        """

        results = self.graph.query(query)

        candidates = []
        for record in results:
            n = record["n"]
            candidates.append(
                {
                    "id": n["properties"]["node_id"],
                    "label": list(n.labels)[0] if n.labels else label,
                    "properties": dict(n["properties"]),
                }
            )

        return candidates

    def search_nodes(
        self,
        graph_id: str,
        query: str,
        search_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for nodes in the graph.

        Args:
            graph_id: ID of the graph
            query: Search query string
            search_fields: Optional list of fields to search in

        Returns:
            List of Node objects matching the search
        """
        label = search_fields[0] if search_fields else "Entity"

        # Build search query - search in name property
        search_conditions = " OR ".join(
            [f"n.name CONTAINS '{query}'" for _ in (search_fields or ["name"])]
        )

        cypher_query = f"""
        MATCH (n:{label})
        WHERE {search_conditions}
        RETURN n
        """

        results = self.graph.query(cypher_query)

        search_results = []
        for record in results:
            n = record["n"]
            search_results.append(
                {
                    "id": n["properties"]["node_id"],
                    "label": list(n.labels)[0] if n.labels else label,
                    "properties": dict(n["properties"]),
                }
            )

        return search_results

    def get_conflicts(self, graph_id: str) -> list[dict[str, Any]]:
        """Get conflicts in the graph.

        Args:
            graph_id: ID of the graph

        Returns:
            List of conflict dictionaries
        """
        # GraphQLite doesn't have explicit conflict detection
        # We'll look for same_as relationships
        try:
            results = self.graph.query("MATCH ()-[r:same_as]->() RETURN r")
            conflicts = []
            for record in results:
                r = record["r"]
                conflicts.append(
                    {
                        "id": r["properties"]["edge_id"],
                        "type": type(r).__name__,
                        "properties": dict(r["properties"]),
                        "source": r.start_node["properties"]["node_id"],
                        "target": r.end_node["properties"]["node_id"],
                    }
                )
            return conflicts
        except Exception:
            return []
