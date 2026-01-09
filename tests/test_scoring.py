from __future__ import annotations

import pytest

from osint.core.models import Entity, EntityType, Relationship, RelationshipType
from osint.core.scoring import ConfidenceScoring


@pytest.fixture
def scoring_system():
    """Create a confidence scoring system."""
    return ConfidenceScoring()


@pytest.fixture
def sample_entity_a():
    """Create a sample entity A."""
    return Entity(
        id="entity_1",
        type=EntityType.ACCOUNT,
        name="john_doe",
        attributes={
            "platform": "twitter",
            "email": "john.doe@example.com",
            "display_name": "John Doe",
        },
        sources=["twitter"],
    )


@pytest.fixture
def sample_entity_b():
    """Create a sample entity B."""
    return Entity(
        id="entity_2",
        type=EntityType.ACCOUNT,
        name="johndoe",
        attributes={
            "platform": "github",
            "email": "john.doe@example.com",
            "display_name": "John Doe",
        },
        sources=["github"],
    )


class TestConfidenceScoring:
    """Test confidence scoring functionality."""

    def test_calculate_relationship_confidence_exact_match(
        self, scoring_system, sample_entity_a, sample_entity_b
    ):
        """Test confidence calculation for exact match."""
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.SAME_PERSON,
            confidence=100.0,
            evidence=["Exact email match"],
        )

        confidence = scoring_system.calculate_relationship_confidence(
            relationship, sample_entity_a, sample_entity_b
        )

        assert 0 <= confidence <= 100
        assert confidence >= 50.0  # Exact matches should be high confidence

    def test_calculate_relationship_confidence_potential(
        self, scoring_system, sample_entity_a, sample_entity_b
    ):
        """Test confidence calculation for potential match."""
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=60.0,
            evidence=["Username pattern variation"],
        )

        confidence = scoring_system.calculate_relationship_confidence(
            relationship, sample_entity_a, sample_entity_b
        )

        assert 0 <= confidence <= 100

    def test_calculate_relationship_confidence_no_entities(self, scoring_system):
        """Test confidence calculation without entity data."""
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=50.0,
            evidence=["Test evidence"],
        )

        confidence = scoring_system.calculate_relationship_confidence(relationship)

        assert 0 <= confidence <= 100

    def test_calculate_cluster_confidence(self, scoring_system):
        """Test cluster confidence calculation."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="user2",
                attributes={},
                sources=["github"],
            ),
            Entity(
                id="entity_3",
                type=EntityType.ACCOUNT,
                name="user3",
                attributes={},
                sources=["linkedin"],
            ),
        ]

        relationships = [
            Relationship(
                id="rel_1",
                entity_a="entity_1",
                entity_b="entity_2",
                type=RelationshipType.POTENTIAL,
                confidence=80.0,
                evidence=["Test"],
            ),
            Relationship(
                id="rel_2",
                entity_a="entity_2",
                entity_b="entity_3",
                type=RelationshipType.POTENTIAL,
                confidence=70.0,
                evidence=["Test"],
            ),
        ]

        confidence = scoring_system.calculate_cluster_confidence(entities, relationships)

        assert 0 <= confidence <= 100
        # Should be close to average of relationship confidences
        assert confidence > 60

    def test_calculate_cluster_confidence_empty(self, scoring_system):
        """Test cluster confidence with no relationships."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={},
                sources=["twitter"],
            ),
        ]

        confidence = scoring_system.calculate_cluster_confidence(entities, [])

        assert confidence == 0.0

    def test_source_quality_score(self, scoring_system, sample_entity_a, sample_entity_b):
        """Test source quality scoring."""
        score = scoring_system._calculate_source_quality_score(
            sample_entity_a, sample_entity_b
        )

        assert 0 <= score <= 1

    def test_source_quality_with_high_quality_sources(self, scoring_system):
        """Test source quality with high quality sources."""
        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user1",
            attributes={},
            sources=["verified"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user2",
            attributes={},
            sources=["verified"],
        )

        score = scoring_system._calculate_source_quality_score(entity_a, entity_b)

        assert score >= 0.9  # High quality sources should score high

    def test_source_quality_with_mixed_sources(self, scoring_system):
        """Test source quality with mixed quality sources."""
        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user1",
            attributes={},
            sources=["verified"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user2",
            attributes={},
            sources=["unknown"],
        )

        score = scoring_system._calculate_source_quality_score(entity_a, entity_b)

        assert 0.5 <= score <= 1.0  # Mixed quality

    def test_temporal_consistency_score(self, scoring_system):
        """Test temporal consistency scoring."""
        from datetime import datetime, timedelta

        now = datetime.now()

        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user1",
            attributes={"created_date": now},
            sources=["twitter"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user2",
            attributes={"created_date": now + timedelta(days=5)},
            sources=["github"],
        )

        score = scoring_system._calculate_temporal_consistency_score(
            entity_a, entity_b
        )

        assert 0 <= score <= 1
        # Same week should have good score
        assert score >= 0.8

    def test_temporal_consistency_old_accounts(self, scoring_system):
        """Test temporal consistency with old accounts."""
        from datetime import datetime, timedelta

        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user1",
            attributes={"created_date": datetime.now()},
            sources=["twitter"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user2",
            attributes={"created_date": datetime.now() - timedelta(days=365)},
            sources=["github"],
        )

        score = scoring_system._calculate_temporal_consistency_score(
            entity_a, entity_b
        )

        assert score < 0.5  # Old accounts should have lower score

    def test_temporal_consistency_no_dates(self, scoring_system):
        """Test temporal consistency with no dates."""
        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user1",
            attributes={},
            sources=["twitter"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user2",
            attributes={},
            sources=["github"],
        )

        score = scoring_system._calculate_temporal_consistency_score(
            entity_a, entity_b
        )

        assert score == 0.0

    def test_uniqueness_score_with_unique_attributes(self, scoring_system):
        """Test uniqueness score with unique attributes."""
        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user1",
            attributes={"email": "unique@example.com"},
            sources=["twitter"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user2",
            attributes={"email": "unique@example.com"},
            sources=["github"],
        )

        score = scoring_system._calculate_uniqueness_score(entity_a, entity_b)

        assert score >= 0.8  # Unique email should score high

    def test_uniqueness_score_with_common_username(self, scoring_system):
        """Test uniqueness score with common username."""
        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="user123",
            attributes={},
            sources=["twitter"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="user456",
            attributes={},
            sources=["github"],
        )

        score = scoring_system._calculate_uniqueness_score(entity_a, entity_b)

        assert score < 0.5  # Common username should score lower

    def test_attribute_match_score(self, scoring_system):
        """Test attribute match scoring."""
        # Single evidence
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=50.0,
            evidence=["Single evidence"],
        )

        score = scoring_system._calculate_attribute_match_score(relationship)

        assert 0 <= score <= 1

        # Multiple evidence
        relationship.evidence = ["Evidence 1", "Evidence 2", "Evidence 3"]
        score = scoring_system._calculate_attribute_match_score(relationship)

        assert score >= 0.6  # More evidence should score higher

    def test_is_unique_username(self, scoring_system):
        """Test username uniqueness detection."""
        # Common pattern
        assert not scoring_system._is_unique_username("user123")

        # Short username
        assert not scoring_system._is_unique_username("abc")

        # Unique looking username
        assert scoring_system._is_unique_username("john.doe.dev")

    def test_custom_weights(self):
        """Test scoring with custom weights."""
        scoring_system = ConfidenceScoring(
            attribute_weight=0.5,
            source_quality_weight=0.1,
            temporal_consistency_weight=0.1,
            uniqueness_weight=0.3,
        )

        assert scoring_system.attribute_weight == 0.5
        assert scoring_system.source_quality_weight == 0.1
        assert scoring_system.temporal_consistency_weight == 0.1
        assert scoring_system.uniqueness_weight == 0.3

    def test_confidence_bounds(self, scoring_system):
        """Test that confidence is always within bounds."""
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=150.0,  # Over 100
            evidence=["Test"],
        )

        confidence = scoring_system.calculate_relationship_confidence(relationship)

        assert 0 <= confidence <= 100

    def test_confidence_bounds_negative(self, scoring_system):
        """Test that confidence is always within bounds (negative case)."""
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=-50.0,  # Negative
            evidence=["Test"],
        )

        confidence = scoring_system.calculate_relationship_confidence(relationship)

        assert 0 <= confidence <= 100
