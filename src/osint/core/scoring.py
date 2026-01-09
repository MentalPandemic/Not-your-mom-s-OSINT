from __future__ import annotations

from typing import Any

from osint.core.models import Entity, Relationship


class ConfidenceScoring:
    """Calculate confidence scores for correlations."""

    def __init__(
        self,
        attribute_weight: float = 0.3,
        source_quality_weight: float = 0.2,
        temporal_consistency_weight: float = 0.2,
        uniqueness_weight: float = 0.3,
    ) -> None:
        self.attribute_weight = attribute_weight
        self.source_quality_weight = source_quality_weight
        self.temporal_consistency_weight = temporal_consistency_weight
        self.uniqueness_weight = uniqueness_weight

    def calculate_relationship_confidence(
        self,
        relationship: Relationship,
        entity_a: Entity | None = None,
        entity_b: Entity | None = None,
    ) -> float:
        """Calculate confidence score for a relationship."""
        if not relationship.confidence:
            return 0.0

        # Start with the base confidence from the relationship
        base_confidence = relationship.confidence

        # Apply adjustments based on various factors
        adjustments = 0.0

        # Check source quality
        if entity_a and entity_b:
            source_score = self._calculate_source_quality_score(entity_a, entity_b)
            adjustments += source_score * self.source_quality_weight

            # Check temporal consistency
            temporal_score = self._calculate_temporal_consistency_score(
                entity_a, entity_b
            )
            adjustments += temporal_score * self.temporal_consistency_weight

            # Check uniqueness
            uniqueness_score = self._calculate_uniqueness_score(entity_a, entity_b)
            adjustments += uniqueness_score * self.uniqueness_weight

        # Apply attribute match bonus
        attribute_score = self._calculate_attribute_match_score(relationship)
        adjustments += attribute_score * self.attribute_weight

        # Combine base confidence with adjustments
        final_confidence = base_confidence + adjustments

        # Ensure confidence is between 0 and 100
        return max(0.0, min(100.0, final_confidence))

    def calculate_cluster_confidence(
        self, entities: list[Entity], relationships: list[Relationship]
    ) -> float:
        """Calculate confidence score for a cluster of entities."""
        if not relationships:
            return 0.0

        # Average confidence of all relationships
        avg_confidence = sum(r.confidence for r in relationships) / len(relationships)

        # Adjust based on number of relationships (more relationships = higher confidence)
        relationship_factor = min(1.0, len(relationships) / 10.0)

        # Adjust based on number of entities (more entities = slightly lower confidence)
        entity_factor = max(0.7, 1.0 - (len(entities) - 3) * 0.05)

        final_confidence = avg_confidence * relationship_factor * entity_factor

        return max(0.0, min(100.0, final_confidence))

    def _calculate_source_quality_score(
        self, entity_a: Entity, entity_b: Entity
    ) -> float:
        """Calculate score based on source reliability."""
        source_quality_map = {
            "sherlock": 0.8,
            "api": 0.9,
            "manual": 0.95,
            "verified": 1.0,
        }

        # Get quality scores for each entity's sources
        scores_a = [
            source_quality_map.get(s.lower(), 0.7) for s in entity_a.sources
        ]
        scores_b = [
            source_quality_map.get(s.lower(), 0.7) for s in entity_b.sources
        ]

        if not scores_a or not scores_b:
            return 0.0

        avg_a = sum(scores_a) / len(scores_a)
        avg_b = sum(scores_b) / len(scores_b)

        # Combine scores
        return (avg_a + avg_b) / 2.0

    def _calculate_temporal_consistency_score(
        self, entity_a: Entity, entity_b: Entity
    ) -> float:
        """Calculate score based on temporal consistency."""
        from datetime import datetime, timedelta

        created_a = entity_a.attributes.get("created_date")
        created_b = entity_b.attributes.get("created_date")

        if not created_a or not created_b:
            return 0.0

        # Parse dates if they're strings
        if isinstance(created_a, str):
            from osint.core.algorithms.temporal import TemporalCorrelationAlgorithm

            created_a = TemporalCorrelationAlgorithm()._parse_datetime(created_a)
        if isinstance(created_b, str):
            from osint.core.algorithms.temporal import TemporalCorrelationAlgorithm

            created_b = TemporalCorrelationAlgorithm()._parse_datetime(created_b)

        if not created_a or not created_b:
            return 0.0

        # Calculate time difference in days
        time_diff = abs((created_a - created_b).total_seconds()) / 86400

        # Scores decrease as time difference increases
        if time_diff <= 1:
            return 1.0
        elif time_diff <= 7:
            return 0.8
        elif time_diff <= 30:
            return 0.6
        elif time_diff <= 90:
            return 0.4
        else:
            return 0.2

    def _calculate_uniqueness_score(
        self, entity_a: Entity, entity_b: Entity
    ) -> float:
        """Calculate score based on uniqueness of the match."""
        # Check if the matching attribute is typically unique
        for key, value in entity_a.attributes.items():
            if key in {"email", "phone", "ip_address", "website"}:
                if value and entity_b.attributes.get(key) == value:
                    return 1.0

        # Check username uniqueness
        username_a = entity_a.name.lower()
        username_b = entity_b.name.lower()

        if username_a == username_b:
            # Exact username match is fairly unique
            return 0.8
        elif self._is_unique_username(username_a) or self._is_unique_username(
            username_b
        ):
            return 0.6

        return 0.4

    def _calculate_attribute_match_score(self, relationship: Relationship) -> float:
        """Calculate score based on number and quality of attribute matches."""
        evidence_count = len(relationship.evidence)

        if evidence_count == 0:
            return 0.0
        elif evidence_count == 1:
            return 0.3
        elif evidence_count == 2:
            return 0.6
        elif evidence_count == 3:
            return 0.8
        else:
            return 1.0

    def _is_unique_username(self, username: str) -> bool:
        """Check if a username appears to be unique."""
        # Very short usernames are less likely to be unique
        if len(username) < 5:
            return False

        # Check for common patterns that suggest non-uniqueness
        import re

        if re.match(r"^user\d+$", username):
            return False
        if re.match(r"^\w+\d{3,}$", username):
            return False

        # Otherwise, assume it's somewhat unique
        return True
