import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.cyphnapse.models import (
    Edge,
    Evidence,
    Graph,
    Node,
    RelationshipType,
    Source,
)


class GraphKernel:
    """Core graph memory functionality."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize the graph kernel with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graphs (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                graph_id TEXT,
                node_type TEXT,
                name TEXT,
                properties TEXT,
                FOREIGN KEY (graph_id) REFERENCES graphs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                graph_id TEXT,
                source_node_id TEXT,
                target_node_id TEXT,
                relationship_type TEXT,
                properties TEXT,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                FOREIGN KEY (graph_id) REFERENCES graphs(id),
                FOREIGN KEY (source_node_id) REFERENCES nodes(id),
                FOREIGN KEY (target_node_id) REFERENCES nodes(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                graph_id TEXT,
                source TEXT,
                content TEXT,
                timestamp TIMESTAMP,
                type TEXT,
                confidence REAL,
                FOREIGN KEY (graph_id) REFERENCES graphs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                graph_id TEXT,
                type TEXT,
                url TEXT,
                citation TEXT,
                title TEXT,
                metadata TEXT,
                FOREIGN KEY (graph_id) REFERENCES graphs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                graph_id TEXT,
                source_node_id TEXT,
                target_node_id TEXT,
                relationship_type TEXT,
                properties TEXT,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                FOREIGN KEY (graph_id) REFERENCES graphs(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_graph(self, name: str) -> str:
        """Create a new graph.

        Args:
            name: Name for the new graph

        Returns:
            Graph ID of the created graph
        """
        graph_id = f"graph_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO graphs (id, name) VALUES (?, ?)",
            (graph_id, name)
        )

        conn.commit()
        conn.close()

        return graph_id

    def get_graph(self, graph_id: str) -> Optional[Graph]:
        """Get a graph by ID.

        Args:
            graph_id: ID of the graph to retrieve

        Returns:
            Graph object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM graphs WHERE id = ?", (graph_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return Graph(id=row[0], name=row[1])
        return None

    def list_graphs(self) -> List[Graph]:
        """List all graphs.

        Returns:
            List of Graph objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM graphs")
        rows = cursor.fetchall()

        conn.close()

        return [Graph(id=row[0], name=row[1]) for row in rows]

    def add_node(self, graph_id: str, node: Node) -> str:
        """Add a node to a graph.

        Args:
            graph_id: ID of the graph
            node: Node to add

        Returns:
            Node ID
        """
        node_id = node.id or f"node_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        properties_json = str(node.properties)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO nodes (id, graph_id, node_type, name, properties)
            VALUES (?, ?, ?, ?, ?)
            """,
            (node_id, graph_id, node.node_type, node.name, properties_json)
        )

        conn.commit()
        conn.close()

        return node_id

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID.

        Args:
            node_id: ID of the node to retrieve

        Returns:
            Node object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, graph_id, node_type, name, properties FROM nodes WHERE id = ?",
            (node_id,)
        )
        row = cursor.fetchone()

        conn.close()

        if row:
            properties = eval(row[4]) if row[4] else {}
            return Node(
                id=row[0],
                graph_id=row[1],
                node_type=row[2],
                name=row[3],
                properties=properties
            )
        return None

    def get_nodes_by_type(self, graph_id: str, node_type: str) -> List[Node]:
        """Get nodes by type.

        Args:
            graph_id: ID of the graph
            node_type: Type of nodes to retrieve

        Returns:
            List of Node objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, graph_id, node_type, name, properties
            FROM nodes
            WHERE graph_id = ? AND node_type = ?
            """,
            (graph_id, node_type)
        )
        rows = cursor.fetchall()

        conn.close()

        nodes = []
        for row in rows:
            properties = eval(row[4]) if row[4] else {}
            nodes.append(Node(
                id=row[0],
                graph_id=row[1],
                node_type=row[2],
                name=row[3],
                properties=properties
            ))
        return nodes

    def add_edge(self, graph_id: str, edge: Edge) -> str:
        """Add an edge to a graph.

        Args:
            graph_id: ID of the graph
            edge: Edge to add

        Returns:
            Edge ID
        """
        edge_id = edge.id or f"edge_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        properties_json = str(edge.properties)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO edges (
                id, graph_id, source_node_id, target_node_id,
                relationship_type, properties, valid_from, valid_until
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge_id,
                graph_id,
                edge.source_node_id,
                edge.target_node_id,
                edge.relationship_type,
                properties_json,
                edge.valid_from,
                edge.valid_until
            )
        )

        conn.commit()
        conn.close()

        return edge_id

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID.

        Args:
            edge_id: ID of the edge to retrieve

        Returns:
            Edge object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, graph_id, source_node_id, target_node_id,
                   relationship_type, properties, valid_from, valid_until
            FROM edges
            WHERE id = ?
            """,
            (edge_id,)
        )
        row = cursor.fetchone()

        conn.close()

        if row:
            properties = eval(row[5]) if row[5] else {}
            return Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=properties,
                valid_from=row[6],
                valid_until=row[7]
            )
        return None

    def get_edges_by_relationship_type(
        self,
        graph_id: str,
        relationship_type: str
    ) -> List[Edge]:
        """Get edges by relationship type.

        Args:
            graph_id: ID of the graph
            relationship_type: Type of relationship to filter by

        Returns:
            List of Edge objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, graph_id, source_node_id, target_node_id,
                   relationship_type, properties, valid_from, valid_until
            FROM edges
            WHERE graph_id = ? AND relationship_type = ?
            """,
            (graph_id, relationship_type)
        )
        rows = cursor.fetchall()

        conn.close()

        edges = []
        for row in rows:
            properties = eval(row[5]) if row[5] else {}
            edges.append(Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=properties,
                valid_from=row[6],
                valid_until=row[7]
            ))
        return edges

    def add_evidence(self, graph_id: str, evidence: Evidence) -> str:
        """Add evidence to a graph.

        Args:
            graph_id: ID of the graph
            evidence: Evidence to add

        Returns:
            Evidence ID
        """
        evidence_id = evidence.id or f"evidence_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO evidence (
                id, graph_id, source, content, timestamp, type, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                graph_id,
                evidence.source,
                evidence.content,
                evidence.timestamp,
                evidence.type,
                evidence.confidence
            )
        )

        conn.commit()
        conn.close()

        return evidence_id

    def add_source(self, graph_id: str, source: Source) -> str:
        """Add a source to a graph.

        Args:
            graph_id: ID of the graph
            source: Source to add

        Returns:
            Source ID
        """
        source_id = source.id or f"source_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        metadata_json = str(source.metadata)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sources (
                id, graph_id, type, url, citation, title, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                graph_id,
                source.type,
                source.url,
                source.citation,
                source.title,
                metadata_json
            )
        )

        conn.commit()
        conn.close()

        return source_id

    def get_relationships_by_type(
        self,
        graph_id: str,
        relationship_type: str
    ) -> List[Edge]:
        """Get relationships by type.

        Args:
            graph_id: ID of the graph
            relationship_type: Type of relationship to retrieve

        Returns:
            List of Edge objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, graph_id, source_node_id, target_node_id,
                   relationship_type, properties, valid_from, valid_until
            FROM relationships
            WHERE graph_id = ? AND relationship_type = ?
            """,
            (graph_id, relationship_type)
        )
        rows = cursor.fetchall()

        conn.close()

        relationships = []
        for row in rows:
            properties = eval(row[6]) if row[6] else {}
            relationships.append(Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=properties,
                valid_from=row[7],
                valid_until=row[8]
            ))
        return relationships

    def get_nodes_by_ids(self, node_ids: List[str]) -> List[Node]:
        """Get nodes by their IDs.

        Args:
            node_ids: List of node IDs to retrieve

        Returns:
            List of Node objects
        """
        if not node_ids:
            return []

        placeholders = ','.join('?' for _ in node_ids)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT id, graph_id, node_type, name, properties
            FROM nodes
            WHERE id IN ({placeholders})
            """,
            node_ids
        )
        rows = cursor.fetchall()

        conn.close()

        nodes = []
        for row in rows:
            properties = eval(row[4]) if row[4] else {}
            nodes.append(Node(
                id=row[0],
                graph_id=row[1],
                node_type=row[2],
                name=row[3],
                properties=properties
            ))
        return nodes

    def get_edges_by_ids(self, edge_ids: List[str]) -> List[Edge]:
        """Get edges by their IDs.

        Args:
            edge_ids: List of edge IDs to retrieve

        Returns:
            List of Edge objects
        """
        if not edge_ids:
            return []

        placeholders = ','.join('?' for _ in edge_ids)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT id, graph_id, source_node_id, target_node_id,
                   relationship_type, properties, valid_from, valid_until
            FROM edges
            WHERE id IN ({placeholders})
            """,
            edge_ids
        )
        rows = cursor.fetchall()

        conn.close()

        edges = []
        for row in rows:
            properties = eval(row[5]) if row[5] else {}
            edges.append(Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=properties,
                valid_from=row[6],
                valid_until=row[7]
            ))
        return edges

    def traverse(
        self,
        graph_id: str,
        start_node_id: str,
        max_depth: int = 5,
        relationship_filters: Optional[List[str]] = None,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Traverse the graph from a starting node.

        Args:
            graph_id: ID of the graph to traverse
            start_node_id: ID of the starting node
            max_depth: Maximum traversal depth
            relationship_filters: Optional list of relationship types to filter by
            direction: Traversal direction ('both', 'incoming', 'outgoing')

        Returns:
            List of traversal results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        visited = set()
        visited.add(start_node_id)
        queue = [(start_node_id, 0)]
        traversal_result = []

        while queue:
            current_node_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            if relationship_filters:
                relationship_filters_str = ','.join(f"'{r}'" for r in relationship_filters)
            else:
                relationship_filters_str = None

            # Check outgoing edges
            if direction in ["both", "outgoing"]:
                if relationship_filters:
                    cursor.execute(
                        """
                        SELECT id, source_node_id, target_node_id, relationship_type,
                               properties, valid_from, valid_until
                        FROM edges
                        WHERE source_node_id = ?
                          AND relationship_type IN ({})
                          AND (valid_until IS NULL OR valid_until >= ?)
                        """.format(relationship_filters_str),
                        (current_node_id, datetime.now())
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, source_node_id, target_node_id, relationship_type,
                               properties, valid_from, valid_until
                        FROM edges
                        WHERE source_node_id = ?
                          AND (valid_until IS NULL OR valid_until >= ?)
                        """,
                        (current_node_id, datetime.now())
                    )

                rows = cursor.fetchall()

                for row in rows:
                    edge = Edge(
                        id=row[0],
                        graph_id=row[1],
                        source_node_id=row[2],
                        target_node_id=row[3],
                        relationship_type=row[4],
                        properties=eval(row[5]) if row[5] else {},
                        valid_from=row[6],
                        valid_until=row[7]
                    )

                    if edge.target_node_id not in visited:
                        visited.add(edge.target_node_id)
                        queue.append((edge.target_node_id, depth + 1))

                        target_node = self.get_node(edge.target_node_id)
                        traversal_result.append({
                            "path": [current_node_id, edge.target_node_id],
                            "edge": edge,
                            "target_node": target_node,
                            "depth": depth + 1
                        })

            # Check incoming edges
            if direction in ["both", "incoming"]:
                if relationship_filters:
                    cursor.execute(
                        """
                        SELECT id, source_node_id, target_node_id, relationship_type,
                               properties, valid_from, valid_until
                        FROM edges
                        WHERE target_node_id = ?
                          AND relationship_type IN ({})
                          AND (valid_until IS NULL OR valid_until >= ?)
                        """.format(relationship_filters_str),
                        (current_node_id, datetime.now())
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, source_node_id, target_node_id, relationship_type,
                               properties, valid_from, valid_until
                        FROM edges
                        WHERE target_node_id = ?
                          AND (valid_until IS NULL OR valid_until >= ?)
                        """,
                        (current_node_id, datetime.now())
                    )

                rows = cursor.fetchall()

                for row in rows:
                    edge = Edge(
                        id=row[0],
                        graph_id=row[1],
                        source_node_id=row[2],
                        target_node_id=row[3],
                        relationship_type=row[4],
                        properties=eval(row[5]) if row[5] else {},
                        valid_from=row[6],
                        valid_until=row[7]
                    )

                    if edge.source_node_id not in visited:
                        visited.add(edge.source_node_id)
                        queue.append((edge.source_node_id, depth + 1))

                        source_node = self.get_node(edge.source_node_id)
                        traversal_result.append({
                            "path": [edge.source_node_id, current_node_id],
                            "edge": edge,
                            "target_node": source_node,
                            "depth": depth + 1
                        })

        conn.close()
        return traversal_result

    def get_current_state(
        self,
        graph_id: str,
        node_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> List[Edge]:
        """Get current state of edges in the graph.

        Args:
            graph_id: ID of the graph
            node_id: Optional node ID to filter by
            timestamp: Optional timestamp to check (defaults to now)

        Returns:
            List of Edge objects representing current state
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = timestamp or datetime.now()

        if node_id:
            cursor.execute(
                """
                SELECT id, graph_id, source_node_id, target_node_id,
                       relationship_type, properties, valid_from, valid_until
                FROM edges
                WHERE graph_id = ?
                  AND (valid_until IS NULL OR valid_until >= ?)
                  AND (valid_from IS NULL OR valid_from <= ?)
                  AND (source_node_id = ? OR target_node_id = ?)
                """,
                (graph_id, current_time, current_time, node_id, node_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, graph_id, source_node_id, target_node_id,
                       relationship_type, properties, valid_from, valid_until
                FROM edges
                WHERE graph_id = ?
                  AND (valid_until IS NULL OR valid_until >= ?)
                  AND (valid_from IS NULL OR valid_from <= ?)
                """,
                (graph_id, current_time, current_time)
            )

        rows = cursor.fetchall()

        conn.close()

        current_state = []
        for row in rows:
            properties = eval(row[6]) if row[6] else {}
            current_state.append(Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=properties,
                valid_from=row[7],
                valid_until=row[8]
            ))
        return current_state

    def get_historical_state(
        self,
        graph_id: str,
        node_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> List[Edge]:
        """Get historical state of edges in the graph.

        Args:
            graph_id: ID of the graph
            node_id: Optional node ID to filter by
            timestamp: Optional timestamp to check

        Returns:
            List of Edge objects representing historical state
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query_time = timestamp or datetime.now()

        if node_id:
            cursor.execute(
                """
                SELECT id, graph_id, source_node_id, target_node_id,
                       relationship_type, properties, valid_from, valid_until
                FROM edges
                WHERE graph_id = ?
                  AND valid_from <= ?
                  AND (valid_until >= ? OR valid_until IS NULL)
                  AND (source_node_id = ? OR target_node_id = ?)
                """,
                (graph_id, query_time, query_time, node_id, node_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, graph_id, source_node_id, target_node_id,
                       relationship_type, properties, valid_from, valid_until
                FROM edges
                WHERE graph_id = ?
                  AND valid_from <= ?
                  AND (valid_until >= ? OR valid_until IS NULL)
                """,
                (graph_id, query_time, query_time)
            )

        rows = cursor.fetchall()

        conn.close()

        historical_state = []
        for row in rows:
            properties = eval(row[6]) if row[6] else {}
            historical_state.append(Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=properties,
                valid_from=row[7],
                valid_until=row[8]
            ))
        return historical_state

    def get_identity_candidates(
        self,
        graph_id: str,
        node: Node
    ) -> List[Node]:
        """Get identity candidates for a node.

        Args:
            graph_id: ID of the graph
            node: Node to find identity candidates for

        Returns:
            List of Node objects that are identity candidates
        """
        nodes = self.get_nodes_by_type(graph_id, node.node_type)
        candidates = []

        for candidate_node in nodes:
            if candidate_node.id == node.id:
                continue

            same_as_edges = self.get_edges_by_relationship_type(
                graph_id, RelationshipType.same_as.value
            )

            candidate_edges = [
                edge for edge in same_as_edges
                if (edge.source_node_id == node.id and edge.target_node_id == candidate_node.id) or
                   (edge.source_node_id == candidate_node.id and edge.target_node_id == node.id)
            ]

            if candidate_edges:
                candidates.append(candidate_node)

        return candidates

    def search_nodes(
        self,
        graph_id: str,
        query: str,
        search_fields: Optional[List[str]] = None
    ) -> List[Node]:
        """Search for nodes in the graph.

        Args:
            graph_id: ID of the graph
            query: Search query string
            search_fields: Optional list of fields to search in

        Returns:
            List of Node objects matching the search
        """
        search_fields = search_fields or ["name", "node_type"]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        conditions = []
        params = []

        for field in search_fields:
            if field == "name":
                conditions.append("name LIKE ?")
                params.append(f"%{query}%")
            elif field == "node_type":
                conditions.append("node_type LIKE ?")
                params.append(f"%{query}%")

        if not conditions:
            conditions.append("name LIKE ?")
            params.append(f"%{query}%")

        where_clause = " OR ".join([f"({condition})" for condition in conditions])

        cursor.execute(
            f"""
            SELECT id, graph_id, node_type, name, properties
            FROM nodes
            WHERE graph_id = ? AND {where_clause}
            """,
            (graph_id,) + tuple(params)
        )
        rows = cursor.fetchall()

        conn.close()

        search_results = []
        for row in rows:
            properties = eval(row[4]) if row[4] else {}
            search_results.append(Node(
                id=row[0],
                graph_id=row[1],
                node_type=row[2],
                name=row[3],
                properties=properties
            ))
        return search_results

    def traverse_focused(
        self,
        graph_id: str,
        start_node_id: str,
        max_depth: int,
        relationship_filters: List[str],
        direction: str
    ) -> List[Dict[str, Any]]:
        """Traverse the graph with specific filters.

        Args:
            graph_id: ID of the graph
            start_node_id: ID of the starting node
            max_depth: Maximum traversal depth
            relationship_filters: List of relationship types to filter by
            direction: Traversal direction

        Returns:
            List of traversal results
        """
        return self.traverse(
            graph_id,
            start_node_id,
            max_depth,
            relationship_filters,
            direction
        )

    def get_identity_candidates_list(
        self,
        graph_id: str,
        node_id: str,
        candidate_nodes: List[Node]
    ) -> List[Node]:
        """Get identity candidates from a list of candidate nodes.

        Args:
            graph_id: ID of the graph
            node_id: ID of the node to find candidates for
            candidate_nodes: List of candidate Node objects

        Returns:
            List of Node objects that are identity candidates
        """
        same_as_edges = self.get_edges_by_relationship_type(
            graph_id, RelationshipType.same_as.value
        )

        candidates = []
        for candidate in candidate_nodes:
            candidate_edges = [
                edge for edge in same_as_edges
                if (edge.source_node_id == node_id and edge.target_node_id == candidate.id) or
                   (edge.source_node_id == candidate.id and edge.target_node_id == node_id)
            ]

            if candidate_edges:
                candidates.append(candidate)

        return candidates

    def get_conflicts(self, graph_id: str) -> List[Dict[str, Any]]:
        """Get conflicts in the graph.

        Args:
            graph_id: ID of the graph

        Returns:
            List of conflict dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM edges WHERE graph_id = ?", (graph_id,))
        rows = cursor.fetchall()

        conn.close()

        conflict_map = {}
        for row in rows:
            edge = Edge(
                id=row[0],
                graph_id=row[1],
                source_node_id=row[2],
                target_node_id=row[3],
                relationship_type=row[4],
                properties=eval(row[5]) if row[5] else {},
                valid_from=row[6],
                valid_until=row[7]
            )

            if edge.relationship_type == "same_as":
                conflict_pair = (edge.source_node_id, edge.target_node_id)
            elif edge.relationship_type == "different_from":
                conflict_pair = (edge.source_node_id, edge.target_node_id)
            else:
                conflict_pair = None

            if conflict_pair and conflict_pair not in conflict_map:
                conflict_map[conflict_pair] = []

            if conflict_pair:
                conflict_map[conflict_pair].append(edge)

        conflicts = []
        for pair, edges in conflict_map.items():
            if len(edges) > 1:
                conflicts.append({
                    "node_pair": pair,
                    "edges": edges
                })

        return conflicts