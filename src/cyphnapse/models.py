"""Data models for Graph Memory Layer.

These models are compatible with GraphQLite's API.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class NodeType(Enum):
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    EVENT = "event"
    EVIDENCE = "evidence"
    SOURCE = "source"
    CLAIM = "claim"


class RelationshipType(Enum):
    same_as = "same_as"
    different_from = "different_from"
    controls = "controls"
    owns = "owns"
    supplies = "supplies"
    acquired = "acquired"
    member_of = "member_of"
    born = "born"
    located_in = "located_in"
    active_during = "active_during"
    observed_by = "observed_by"
    supports = "supports"
    contradicts = "contradicts"


@dataclass
class Graph:
    id: str = None
    name: str = "default"


@dataclass
class Node:
    id: str = None
    graph_id: str = None
    label: str | None = None
    name: str | None = None
    properties: dict[str, Any] = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"node_{uuid.uuid4().hex[:8]}"
        if self.properties is None:
            self.properties = {}


@dataclass
class Edge:
    id: str = None
    graph_id: str = None
    source_node_id: str = None
    target_node_id: str = None
    relationship_type: str | None = None
    properties: dict[str, Any] = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"edge_{uuid.uuid4().hex[:8]}"
        if self.properties is None:
            self.properties = {}


@dataclass
class Evidence:
    id: str = None
    graph_id: str = None
    source: str = None
    content: str = None
    timestamp: datetime | None = None
    type: str | None = None
    confidence: float | None = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"evidence_{uuid.uuid4().hex[:8]}"


@dataclass
class Property:
    name: str
    value: Any
    type: str | None = None
    description: str | None = None


@dataclass
class Event:
    id: str = None
    graph_id: str = None
    timestamp: datetime = None
    description: str | None = None
    related_nodes: list[str] = None
    related_edges: list[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"event_{uuid.uuid4().hex[:8]}"
        if self.related_nodes is None:
            self.related_nodes = []
        if self.related_edges is None:
            self.related_edges = []


@dataclass
class Source:
    id: str = None
    graph_id: str = None
    type: str = None
    url: str | None = None
    citation: str | None = None
    title: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"source_{uuid.uuid4().hex[:8]}"
        if self.metadata is None:
            self.metadata = {}
