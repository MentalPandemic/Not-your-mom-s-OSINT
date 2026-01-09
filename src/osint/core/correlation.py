from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from osint.core.algorithms.email import EmailCorrelationAlgorithm
from osint.core.algorithms.metadata import MetadataCorrelationAlgorithm
from osint.core.algorithms.network import NetworkCorrelationAlgorithm
from osint.core.algorithms.temporal import TemporalCorrelationAlgorithm
from osint.core.algorithms.username import UsernameCorrelationAlgorithm
from osint.core.graph import RelationshipGraph
from osint.core.models import (
    CorrelationResult,
    Entity,
    EntityCluster,
    EntityType,
    QueryResult,
    QueryStatus,
    Relationship,
    RelationshipType,
)
from osint.core.reports import ReportGenerator
from osint.core.scoring import ConfidenceScoring


class CorrelationEngine:
    """Main correlation engine for analyzing OSINT findings."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

        # Initialize algorithms
        self.username_algorithm = UsernameCorrelationAlgorithm()
        self.email_algorithm = EmailCorrelationAlgorithm()
        self.metadata_algorithm = MetadataCorrelationAlgorithm()
        self.network_algorithm = NetworkCorrelationAlgorithm()
        self.temporal_algorithm = TemporalCorrelationAlgorithm()

        # Initialize scoring
        self.scoring = ConfidenceScoring()

        # Initialize graph
        self.graph = RelationshipGraph()

        # Store entities and relationships
        self._entities: dict[str, Entity] = {}
        self._relationships: list[Relationship] = []

    def process_query_results(self, results: list[QueryResult]) -> CorrelationResult:
        """Process query results and identify correlations."""
        # Extract entities from results
        entities = self._extract_entities_from_results(results)

        # Add entities to the system
        for entity in entities:
            self._entities[entity.id] = entity
            self.graph.add_entity(entity)

        # Run correlation algorithms
        relationships = self._run_correlation_algorithms(entities)

        # Add relationships to the graph
        for relationship in relationships:
            self._relationships.append(relationship)
            self.graph.add_relationship(relationship)

        # Find clusters
        clusters = self._find_clusters(entities, relationships)

        # Calculate average confidence
        avg_confidence = (
            sum(r.confidence for r in relationships) / len(relationships)
            if relationships
            else 0.0
        )

        # Generate summary
        summary = self._generate_summary(entities, relationships, clusters)

        return CorrelationResult(
            entities=entities,
            relationships=relationships,
            clusters=clusters,
            confidence_average=avg_confidence,
            summary=summary,
        )

    def correlate_username(self, username: str) -> CorrelationResult:
        """Correlate findings for a specific username."""
        # Create a dummy entity for the username
        entity = Entity(
            id=f"entity_{uuid.uuid4().hex}",
            type=EntityType.PERSON,
            name=username,
            sources=["manual"],
        )

        self._entities[entity.id] = entity
        self.graph.add_entity(entity)

        # Correlate with existing entities
        relationships = self._run_correlation_algorithms([entity] + list(self._entities.values()))

        # Remove the temporary entity from results
        relationships = [r for r in relationships if r.entity_a != entity.id and r.entity_b != entity.id]

        # Find clusters
        clusters = self._find_clusters(list(self._entities.values()), relationships)

        avg_confidence = (
            sum(r.confidence for r in relationships) / len(relationships)
            if relationships
            else 0.0
        )

        summary = self._generate_summary(
            list(self._entities.values()), relationships, clusters
        )

        return CorrelationResult(
            entities=list(self._entities.values()),
            relationships=relationships,
            clusters=clusters,
            confidence_average=avg_confidence,
            summary=summary,
        )

    def correlate_entities(self, entity_ids: list[str]) -> CorrelationResult:
        """Correlate specific entities."""
        entities = [
            e for e in self._entities.values() if e.id in entity_ids
        ]

        if not entities:
            return CorrelationResult(
                entities=[],
                relationships=[],
                clusters=[],
                confidence_average=0.0,
                summary="No entities found for correlation.",
            )

        # Run correlation algorithms on selected entities
        relationships = self._run_correlation_algorithms(entities)

        # Filter to only include relationships between selected entities
        relationship_ids = set(entity_ids)
        relationships = [
            r
            for r in relationships
            if r.entity_a in relationship_ids and r.entity_b in relationship_ids
        ]

        # Find clusters
        clusters = self._find_clusters(entities, relationships)

        avg_confidence = (
            sum(r.confidence for r in relationships) / len(relationships)
            if relationships
            else 0.0
        )

        summary = self._generate_summary(entities, relationships, clusters)

        return CorrelationResult(
            entities=entities,
            relationships=relationships,
            clusters=clusters,
            confidence_average=avg_confidence,
            summary=summary,
        )

    def get_relationships(
        self,
        entity_id: str | None = None,
        rel_type: RelationshipType | None = None,
        min_confidence: float = 0.0,
    ) -> list[Relationship]:
        """Get relationships with optional filters."""
        relationships = self._relationships

        if entity_id:
            relationships = [
                r for r in relationships if r.entity_a == entity_id or r.entity_b == entity_id
            ]

        if rel_type:
            relationships = [r for r in relationships if r.type == rel_type]

        if min_confidence > 0:
            relationships = [r for r in relationships if r.confidence >= min_confidence]

        return relationships

    def get_graph(self) -> RelationshipGraph:
        """Get the relationship graph."""
        return self.graph

    def generate_report(
        self, format: str = "text", output: Path | None = None
    ) -> str:
        """Generate a correlation report."""
        result = CorrelationResult(
            entities=list(self._entities.values()),
            relationships=self._relationships,
            clusters=self._find_clusters(
                list(self._entities.values()), self._relationships
            ),
            confidence_average=(
                sum(r.confidence for r in self._relationships) / len(self._relationships)
                if self._relationships
                else 0.0
            ),
            summary="",
        )

        generator = ReportGenerator()

        if format == "json":
            return generator.generate_json_report(result)
        elif format == "html":
            return generator.generate_html_report(result)
        else:
            return generator.generate_text_report(result)

    def _extract_entities_from_results(self, results: list[QueryResult]) -> list[Entity]:
        """Extract entities from query results."""
        entities: list[Entity] = []

        for result in results:
            if result.status != QueryStatus.FOUND:
                continue

            # Create account entity
            account_entity = Entity(
                id=f"account_{result.platform_name}_{result.username}",
                type=EntityType.ACCOUNT,
                name=result.username,
                attributes={
                    "platform": result.platform_name,
                    "profile_url": result.profile_url,
                    "response_time": result.response_time,
                    **result.metadata,
                },
                sources=[result.platform_name],
            )
            entities.append(account_entity)

            # Extract email from metadata if available
            if "email" in result.metadata:
                email_entity = Entity(
                    id=f"email_{result.metadata['email']}",
                    type=EntityType.EMAIL,
                    name=result.metadata["email"],
                    attributes={"source_platform": result.platform_name},
                    sources=[result.platform_name],
                )
                entities.append(email_entity)

            # Extract IP from metadata if available
            if "ip_address" in result.metadata:
                ip_entity = Entity(
                    id=f"ip_{result.metadata['ip_address']}",
                    type=EntityType.IP,
                    name=result.metadata["ip_address"],
                    attributes={"source_platform": result.platform_name},
                    sources=[result.platform_name],
                )
                entities.append(ip_entity)

        return entities

    def _run_correlation_algorithms(self, entities: list[Entity]) -> list[Relationship]:
        """Run all correlation algorithms and combine results."""
        all_relationships: list[Relationship] = []

        # Run each algorithm
        all_relationships.extend(self.username_algorithm.correlate(entities))
        all_relationships.extend(self.email_algorithm.correlate(entities))
        all_relationships.extend(self.metadata_algorithm.correlate(entities))
        all_relationships.extend(self.network_algorithm.correlate(entities))
        all_relationships.extend(self.temporal_algorithm.correlate(entities))

        # Update confidence scores
        for relationship in all_relationships:
            entity_a = self._entities.get(relationship.entity_a)
            entity_b = self._entities.get(relationship.entity_b)
            relationship.confidence = self.scoring.calculate_relationship_confidence(
                relationship, entity_a, entity_b
            )

        # Remove duplicates
        unique_relationships = self._deduplicate_relationships(all_relationships)

        return unique_relationships

    def _deduplicate_relationships(
        self, relationships: list[Relationship]
    ) -> list[Relationship]:
        """Remove duplicate relationships, keeping the one with highest confidence."""
        seen: dict[tuple[str, str], Relationship] = {}

        for relationship in relationships:
            key = tuple(sorted((relationship.entity_a, relationship.entity_b)))

            if key not in seen or relationship.confidence > seen[key].confidence:
                seen[key] = relationship

        return list(seen.values())

    def _find_clusters(
        self, entities: list[Entity], relationships: list[Relationship]
    ) -> list[EntityCluster]:
        """Find clusters of related entities."""
        graph_clusters = self.graph.find_clusters(min_confidence=50.0, min_size=2)

        clusters: list[EntityCluster] = []

        for i, cluster_entities in enumerate(graph_clusters):
            if len(cluster_entities) < 2:
                continue

            # Find relationships within this cluster
            cluster_rel_ids = set(cluster_entities)
            cluster_rels = [
                r
                for r in relationships
                if r.entity_a in cluster_rel_ids and r.entity_b in cluster_rel_ids
            ]

            if not cluster_rels:
                continue

            # Calculate cluster confidence
            cluster_confidence = self.scoring.calculate_cluster_confidence(
                [e for e in entities if e.id in cluster_rel_ids], cluster_rels
            )

            # Find representative entity (most central)
            entity_counts: dict[str, int] = {}
            for rel in cluster_rels:
                entity_counts[rel.entity_a] = entity_counts.get(rel.entity_a, 0) + 1
                entity_counts[rel.entity_b] = entity_counts.get(rel.entity_b, 0) + 1

            representative = max(entity_counts, key=entity_counts.get)

            clusters.append(
                EntityCluster(
                    id=f"cluster_{i}",
                    entities=cluster_entities,
                    representative=representative,
                    confidence=cluster_confidence,
                )
            )

        return clusters

    def _generate_summary(
        self,
        entities: list[Entity],
        relationships: list[Relationship],
        clusters: list[EntityCluster],
    ) -> str:
        """Generate a human-readable summary."""
        lines: list[str] = []

        lines.append(f"Correlation Analysis Summary")
        lines.append(f"=" * 40)
        lines.append(f"")
        lines.append(f"Entities analyzed: {len(entities)}")
        lines.append(f"Relationships found: {len(relationships)}")
        lines.append(f"Clusters identified: {len(clusters)}")

        if relationships:
            avg_confidence = sum(r.confidence for r in relationships) / len(
                relationships
            )
            lines.append(f"Average confidence: {avg_confidence:.1f}%")

            # Count by relationship type
            type_counts: dict[RelationshipType, int] = {}
            for rel in relationships:
                type_counts[rel.type] = type_counts.get(rel.type, 0) + 1

            lines.append(f"")
            lines.append(f"Relationships by type:")
            for rel_type, count in sorted(type_counts.items()):
                lines.append(f"  - {rel_type.value}: {count}")

        if clusters:
            lines.append(f"")
            lines.append(f"Top clusters:")
            for i, cluster in enumerate(sorted(clusters, key=lambda c: c.confidence, reverse=True)[:5]):
                lines.append(f"  {i + 1}. {len(cluster.entities)} entities (confidence: {cluster.confidence:.1f}%)")

        return "\n".join(lines)

    def load_from_file(self, path: Path) -> None:
        """Load correlation data from a file."""
        with path.open("r") as f:
            data = json.load(f)

        # Load entities
        for entity_data in data.get("entities", []):
            entity = Entity(
                id=entity_data["id"],
                type=EntityType(entity_data["type"]),
                name=entity_data["name"],
                attributes=entity_data.get("attributes", {}),
                sources=entity_data.get("sources", []),
                created_date=datetime.fromisoformat(entity_data["created_date"]),
            )
            self._entities[entity.id] = entity
            self.graph.add_entity(entity)

        # Load relationships
        for rel_data in data.get("relationships", []):
            rel = Relationship(
                id=rel_data["id"],
                entity_a=rel_data["entity_a"],
                entity_b=rel_data["entity_b"],
                type=RelationshipType(rel_data["type"]),
                confidence=rel_data["confidence"],
                evidence=rel_data.get("evidence", []),
                metadata=rel_data.get("metadata", {}),
            )
            self._relationships.append(rel)
            self.graph.add_relationship(rel)

    def save_to_file(self, path: Path) -> None:
        """Save correlation data to a file."""
        data = {
            "entities": [e.to_dict() for e in self._entities.values()],
            "relationships": [r.to_dict() for r in self._relationships],
            "clusters": [
                c.to_dict()
                for c in self._find_clusters(
                    list(self._entities.values()), self._relationships
                )
            ],
        }

        with path.open("w") as f:
            json.dump(data, f, indent=2)
