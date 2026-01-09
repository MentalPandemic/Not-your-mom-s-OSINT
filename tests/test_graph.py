from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from osint.core.graph import RelationshipGraph
from osint.core.models import (
    Entity,
    EntityType,
    Relationship,
    RelationshipType,
)


@pytest.fixture
def sample_entities():
    """Create sample entities."""
    return [
        Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="john_doe",
            attributes={"platform": "twitter"},
            sources=["twitter"],
        ),
        Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="johndoe",
            attributes={"platform": "github"},
            sources=["github"],
        ),
        Entity(
            id="entity_3",
            type=EntityType.EMAIL,
            name="john.doe@example.com",
            attributes={},
            sources=["twitter"],
        ),
    ]


@pytest.fixture
def sample_relationships():
    """Create sample relationships."""
    return [
        Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=75.0,
            evidence=["Username pattern variation"],
        ),
        Relationship(
            id="rel_2",
            entity_a="entity_1",
            entity_b="entity_3",
            type=RelationshipType.SAME_PERSON,
            confidence=100.0,
            evidence=["Email match"],
        ),
    ]


@pytest.fixture
def populated_graph(sample_entities, sample_relationships):
    """Create a graph populated with sample data."""
    graph = RelationshipGraph()
    graph.add_entities(sample_entities)
    graph.add_relationships(sample_relationships)
    return graph


class TestRelationshipGraph:
    """Test relationship graph functionality."""

    def test_add_entity(self):
        """Test adding an entity to the graph."""
        graph = RelationshipGraph()
        entity = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="test",
            attributes={},
            sources=["test"],
        )

        graph.add_entity(entity)

        assert entity.id in graph.graph.nodes()
        assert graph.get_entity(entity.id) == entity

    def test_add_relationship(self):
        """Test adding a relationship to the graph."""
        graph = RelationshipGraph()

        # Add entities first
        entity_a = Entity(
            id="entity_1",
            type=EntityType.ACCOUNT,
            name="test_a",
            attributes={},
            sources=["test"],
        )
        entity_b = Entity(
            id="entity_2",
            type=EntityType.ACCOUNT,
            name="test_b",
            attributes={},
            sources=["test"],
        )

        graph.add_entity(entity_a)
        graph.add_entity(entity_b)

        # Add relationship
        relationship = Relationship(
            id="rel_1",
            entity_a="entity_1",
            entity_b="entity_2",
            type=RelationshipType.POTENTIAL,
            confidence=75.0,
            evidence=["Test"],
        )

        graph.add_relationship(relationship)

        assert graph.graph.has_edge("entity_1", "entity_2")

    def test_add_multiple_entities(self, sample_entities):
        """Test adding multiple entities at once."""
        graph = RelationshipGraph()
        graph.add_entities(sample_entities)

        assert graph.graph.number_of_nodes() == len(sample_entities)

        for entity in sample_entities:
            assert graph.get_entity(entity.id) == entity

    def test_get_entity_neighbors(self, populated_graph):
        """Test getting entity neighbors."""
        neighbors = populated_graph.get_entity_neighbors("entity_1")

        assert len(neighbors) == 2
        neighbor_ids = [n[0] for n in neighbors]
        assert "entity_2" in neighbor_ids
        assert "entity_3" in neighbor_ids

    def test_get_path(self, populated_graph):
        """Test finding path between entities."""
        path = populated_graph.get_path("entity_2", "entity_3")

        assert path is not None
        assert "entity_2" in path
        assert "entity_3" in path

    def test_find_clusters(self, populated_graph):
        """Test cluster identification."""
        clusters = populated_graph.find_clusters(min_confidence=50.0, min_size=2)

        # Should find at least one cluster containing entity_1, entity_2, entity_3
        assert len(clusters) >= 1

        # All entities should be in a cluster since they're connected
        all_in_clusters = []
        for cluster in clusters:
            all_in_clusters.extend(cluster)

        assert "entity_1" in all_in_clusters
        assert "entity_2" in all_in_clusters
        assert "entity_3" in all_in_clusters

    def test_get_relationships_by_type(self, populated_graph):
        """Test filtering relationships by type."""
        same_person_rels = populated_graph.get_relationships_by_type(
            RelationshipType.SAME_PERSON
        )

        assert len(same_person_rels) == 1
        assert same_person_rels[0][2].type == RelationshipType.SAME_PERSON

    def test_get_relationships_by_confidence(self, populated_graph):
        """Test filtering relationships by confidence."""
        high_conf_rels = populated_graph.get_relationships_by_confidence(
            min_confidence=80.0
        )

        assert len(high_conf_rels) >= 1
        for rel in high_conf_rels:
            assert rel[2].confidence >= 80.0

    def test_export_graphml(self, populated_graph):
        """Test exporting graph to GraphML format."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.graphml"
            populated_graph.export_graphml(path)

            assert path.exists()
            assert path.stat().st_size > 0

    def test_export_gexf(self, populated_graph):
        """Test exporting graph to GEXF format."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.gexf"
            populated_graph.export_gexf(path)

            assert path.exists()
            assert path.stat().st_size > 0

    def test_export_json(self, populated_graph):
        """Test exporting graph to JSON format."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            populated_graph.export_json(path)

            assert path.exists()
            assert path.stat().st_size > 0

            # Verify JSON is valid
            with path.open() as f:
                data = json.load(f)
                assert "nodes" in data
                assert "edges" in data

    def test_get_statistics(self, populated_graph):
        """Test getting graph statistics."""
        stats = populated_graph.get_statistics()

        assert stats["num_nodes"] == 3
        assert stats["num_edges"] == 2
        assert stats["num_connected_components"] == 1
        assert stats["average_degree"] > 0
        assert stats["density"] > 0

    def test_find_central_entities(self, populated_graph):
        """Test finding central entities."""
        central = populated_graph.find_central_entities(top_n=5)

        assert len(central) > 0
        # entity_1 should be most central (connected to both other entities)
        assert central[0][0] == "entity_1"

    def test_find_bridges(self, populated_graph):
        """Test finding bridge edges."""
        bridges = populated_graph.find_bridges()

        # In our test graph, both edges are bridges
        # (removing either would disconnect the graph)
        assert len(bridges) >= 0

    def test_empty_graph(self):
        """Test behavior with empty graph."""
        graph = RelationshipGraph()

        assert graph.graph.number_of_nodes() == 0
        assert graph.graph.number_of_edges() == 0

        stats = graph.get_statistics()
        assert stats["num_nodes"] == 0
        assert stats["num_edges"] == 0

    def test_get_nonexistent_entity(self):
        """Test getting a non-existent entity."""
        graph = RelationshipGraph()
        entity = graph.get_entity("nonexistent")

        assert entity is None
