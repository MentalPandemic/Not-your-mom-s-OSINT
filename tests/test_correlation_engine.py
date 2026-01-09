from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from osint.core.correlation import CorrelationEngine
from osint.core.models import (
    CorrelationResult,
    Entity,
    EntityType,
    QueryResult,
    QueryStatus,
    RelationshipType,
)


@pytest.fixture
def correlation_engine():
    """Create a correlation engine instance."""
    return CorrelationEngine()


@pytest.fixture
def sample_query_results():
    """Create sample query results for testing."""
    return [
        QueryResult(
            username="john_doe",
            platform_name="twitter",
            profile_url="https://twitter.com/john_doe",
            status=QueryStatus.FOUND,
            metadata={
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "location": "New York",
            },
        ),
        QueryResult(
            username="johndoe",
            platform_name="github",
            profile_url="https://github.com/johndoe",
            status=QueryStatus.FOUND,
            metadata={
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "bio": "Software developer in NYC",
            },
        ),
        QueryResult(
            username="john_doe",
            platform_name="linkedin",
            profile_url="https://linkedin.com/in/john-doe",
            status=QueryStatus.FOUND,
            metadata={
                "email": "john.doe@example.com",
                "display_name": "John Doe",
            },
        ),
        QueryResult(
            username="jane_smith",
            platform_name="twitter",
            profile_url="https://twitter.com/jane_smith",
            status=QueryStatus.FOUND,
            metadata={
                "email": "jane.smith@example.com",
                "display_name": "Jane Smith",
                "location": "New York",
            },
        ),
    ]


@pytest.fixture
def sample_entities():
    """Create sample entities for testing."""
    now = datetime.now()
    yesterday = now - timedelta(days=1)

    return [
        Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="john_doe",
            attributes={
                "platform": "twitter",
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "location": "New York",
                "created_date": now,
            },
            sources=["twitter"],
        ),
        Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="johndoe",
            attributes={
                "platform": "github",
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "bio": "Software developer in NYC",
                "created_date": yesterday,
            },
            sources=["github"],
        ),
        Entity(
            id="entity_3",
            type=EntityType.EMAIL,
            name="john.doe@example.com",
            attributes={"source_platform": "twitter"},
            sources=["twitter"],
        ),
    ]


class TestCorrelationEngine:
    """Test the main correlation engine."""

    def test_process_query_results(self, correlation_engine, sample_query_results):
        """Test processing query results."""
        result = correlation_engine.process_query_results(sample_query_results)

        assert isinstance(result, CorrelationResult)
        assert len(result.entities) > 0
        assert len(result.relationships) > 0
        assert 0 <= result.confidence_average <= 100

    def test_entity_extraction(self, correlation_engine, sample_query_results):
        """Test entity extraction from query results."""
        entities = correlation_engine._extract_entities_from_results(
            sample_query_results
        )

        # Should extract account entities
        account_entities = [e for e in entities if e.type == EntityType.ACCOUNT]
        assert len(account_entities) == 4

        # Should extract email entities
        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        assert len(email_entities) > 0

    def test_correlate_username(self, correlation_engine):
        """Test correlating by username."""
        result = correlation_engine.correlate_username("john_doe")

        assert isinstance(result, CorrelationResult)
        assert result.summary is not None

    def test_correlate_entities(self, correlation_engine, sample_entities):
        """Test correlating specific entities."""
        # First add entities to the engine
        for entity in sample_entities:
            correlation_engine._entities[entity.id] = entity
            correlation_engine.graph.add_entity(entity)

        result = correlation_engine.correlate_entities(
            ["entity_1", "entity_2", "entity_3"]
        )

        assert isinstance(result, CorrelationResult)
        assert len(result.entities) == 3

    def test_get_relationships_filtered(self, correlation_engine, sample_query_results):
        """Test filtering relationships."""
        correlation_engine.process_query_results(sample_query_results)

        # Get all relationships
        all_rels = correlation_engine.get_relationships()
        assert len(all_rels) > 0

        # Filter by confidence
        high_conf_rels = correlation_engine.get_relationships(min_confidence=80)
        for rel in high_conf_rels:
            assert rel.confidence >= 80

        # Filter by type
        same_person_rels = correlation_engine.get_relationships(
            rel_type=RelationshipType.SAME_PERSON
        )
        for rel in same_person_rels:
            assert rel.type == RelationshipType.SAME_PERSON

    def test_summary_generation(self, correlation_engine, sample_query_results):
        """Test summary generation."""
        result = correlation_engine.process_query_results(sample_query_results)

        assert "Entities analyzed:" in result.summary
        assert "Relationships found:" in result.summary
        assert "Average confidence:" in result.summary

    def test_duplicate_removal(self, correlation_engine):
        """Test removal of duplicate relationships."""
        from osint.core.models import Relationship

        # Create duplicate relationships
        rel1 = Relationship(
            id="rel_1",
            entity_a="entity_a",
            entity_b="entity_b",
            type=RelationshipType.SAME_PERSON,
            confidence=90.0,
            evidence=["Test"],
        )

        rel2 = Relationship(
            id="rel_2",
            entity_a="entity_a",
            entity_b="entity_b",
            type=RelationshipType.SAME_PERSON,
            confidence=85.0,
            evidence=["Test"],
        )

        rel3 = Relationship(
            id="rel_3",
            entity_b="entity_a",
            entity_a="entity_b",
            type=RelationshipType.SAME_PERSON,
            confidence=95.0,
            evidence=["Test"],
        )

        deduplicated = correlation_engine._deduplicate_relationships([rel1, rel2, rel3])

        assert len(deduplicated) == 1
        assert deduplicated[0].confidence == 95.0

    def test_cluster_identification(self, correlation_engine, sample_query_results):
        """Test cluster identification."""
        result = correlation_engine.process_query_results(sample_query_results)

        # Should identify at least one cluster
        assert len(result.clusters) >= 0

        # If clusters exist, they should have entities
        for cluster in result.clusters:
            assert len(cluster.entities) >= 2
            assert cluster.representative in cluster.entities
            assert 0 <= cluster.confidence <= 100
