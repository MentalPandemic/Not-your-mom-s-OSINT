from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

from osint.core.models import Entity, Relationship, RelationshipType
from osint.utils.file_handler import FileHandler


def _serialize_value(value: Any) -> Any:
    """Serialize a value for JSON storage."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _serialize_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """Serialize attributes for JSON storage."""
    return {k: _serialize_value(v) for k, v in attributes.items()}


class RelationshipGraph:
    """Manages entity relationships using NetworkX."""

    def __init__(self) -> None:
        self.graph = nx.Graph()
        self._entities: dict[str, Entity] = {}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph."""
        self.graph.add_node(
            entity.id,
            type=entity.type.value,
            name=entity.name,
            attributes=json.dumps(_serialize_attributes(entity.attributes)),
            sources=json.dumps(entity.sources),
        )
        self._entities[entity.id] = entity

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the graph."""
        self.graph.add_edge(
            relationship.entity_a,
            relationship.entity_b,
            type=relationship.type.value,
            confidence=relationship.confidence,
            evidence=json.dumps(relationship.evidence),
            id=relationship.id,
        )

    def add_entities(self, entities: list[Entity]) -> None:
        """Add multiple entities to the graph."""
        for entity in entities:
            self.add_entity(entity)

    def add_relationships(self, relationships: list[Relationship]) -> None:
        """Add multiple relationships to the graph."""
        for relationship in relationships:
            self.add_relationship(relationship)

    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entity_neighbors(self, entity_id: str) -> list[tuple[str, Relationship]]:
        """Get all entities connected to the given entity."""
        if entity_id not in self.graph:
            return []

        neighbors = []
        for neighbor in self.graph.neighbors(entity_id):
            edge_data = self.graph.get_edge_data(entity_id, neighbor)
            relationship = Relationship(
                id=edge_data["id"],
                entity_a=entity_id,
                entity_b=neighbor,
                type=RelationshipType(edge_data["type"]),
                confidence=edge_data["confidence"],
                evidence=json.loads(edge_data["evidence"]),
            )
            neighbors.append((neighbor, relationship))

        return neighbors

    def get_path(self, entity_a: str, entity_b: str) -> list[str] | None:
        """Find shortest path between two entities."""
        try:
            return nx.shortest_path(self.graph, entity_a, entity_b)
        except nx.NetworkXNoPath:
            return None

    def find_clusters(
        self, min_confidence: float = 50.0, min_size: int = 2
    ) -> list[list[str]]:
        """Find clusters of connected entities."""
        # Filter edges by confidence
        filtered_edges = [
            (u, v, data)
            for u, v, data in self.graph.edges(data=True)
            if data["confidence"] >= min_confidence
        ]

        # Create subgraph with filtered edges
        subgraph = nx.Graph()
        subgraph.add_nodes_from(self.graph.nodes(data=True))
        subgraph.add_edges_from(filtered_edges)

        # Find connected components
        clusters = [
            list(component)
            for component in nx.connected_components(subgraph)
            if len(component) >= min_size
        ]

        return clusters

    def find_communities(self) -> list[list[str]]:
        """Find communities using the Louvain algorithm."""
        try:
            communities = nx.community.louvain_communities(self.graph)
            return [list(community) for community in communities]
        except Exception:
            # Fallback to connected components if Louvain fails
            return [
                list(component) for component in nx.connected_components(self.graph)
            ]

    def get_relationships_by_type(
        self, rel_type: RelationshipType
    ) -> list[tuple[str, str, Relationship]]:
        """Get all relationships of a specific type."""
        relationships = []
        for u, v, data in self.graph.edges(data=True):
            if data["type"] == rel_type.value:
                relationship = Relationship(
                    id=data["id"],
                    entity_a=u,
                    entity_b=v,
                    type=rel_type,
                    confidence=data["confidence"],
                    evidence=json.loads(data["evidence"]),
                )
                relationships.append((u, v, relationship))

        return relationships

    def get_relationships_by_confidence(
        self, min_confidence: float, max_confidence: float = 100.0
    ) -> list[tuple[str, str, Relationship]]:
        """Get all relationships within a confidence range."""
        relationships = []
        for u, v, data in self.graph.edges(data=True):
            if min_confidence <= data["confidence"] <= max_confidence:
                relationship = Relationship(
                    id=data["id"],
                    entity_a=u,
                    entity_b=v,
                    type=RelationshipType(data["type"]),
                    confidence=data["confidence"],
                    evidence=json.loads(data["evidence"]),
                )
                relationships.append((u, v, relationship))

        return relationships

    def export_graphml(self, path: Path) -> None:
        """Export graph to GraphML format."""
        nx.write_graphml(self.graph, path)

    def export_gexf(self, path: Path) -> None:
        """Export graph to GEXF format."""
        nx.write_gexf(self.graph, path)

    def export_json(self, path: Path) -> None:
        """Export graph to JSON format using FileHandler utility."""
        from networkx.readwrite import json_graph

        data = json_graph.node_link_data(self.graph)
        FileHandler.write_json(data, path)

    def get_statistics(self) -> dict[str, Any]:
        """Get graph statistics."""
        stats = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "num_connected_components": nx.number_connected_components(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values())
            / self.graph.number_of_nodes()
            if self.graph.number_of_nodes() > 0
            else 0,
            "density": nx.density(self.graph),
        }

        # Get degree distribution
        degrees = dict(self.graph.degree())
        stats["min_degree"] = min(degrees.values()) if degrees else 0
        stats["max_degree"] = max(degrees.values()) if degrees else 0

        # Get confidence distribution
        confidences = [
            data["confidence"]
            for u, v, data in self.graph.edges(data=True)
            if "confidence" in data
        ]
        if confidences:
            stats["min_confidence"] = min(confidences)
            stats["max_confidence"] = max(confidences)
            stats["avg_confidence"] = sum(confidences) / len(confidences)

        return stats

    def find_central_entities(self, top_n: int = 10) -> list[tuple[str, float]]:
        """Find most central entities using degree centrality."""
        centrality = nx.degree_centrality(self.graph)
        sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_centrality[:top_n]

    def find_bridges(self) -> list[tuple[str, str]]:
        """Find bridge edges (edges whose removal increases number of components)."""
        return list(nx.bridges(self.graph))
