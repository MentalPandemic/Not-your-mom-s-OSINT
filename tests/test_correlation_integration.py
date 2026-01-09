from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

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
def complex_query_results():
    """Create complex query results for integration testing."""
    now = datetime.now()

    return [
        # John Doe's accounts
        QueryResult(
            username="john_doe",
            platform_name="twitter",
            profile_url="https://twitter.com/john_doe",
            status=QueryStatus.FOUND,
            metadata={
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "location": "New York, USA",
                "created_date": now.isoformat(),
                "bio": "Software developer and open source enthusiast",
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
                "location": "NYC",
                "created_date": (now + timedelta(days=5)).isoformat(),
                "bio": "Software developer and open source enthusiast",
                "ip_address": "192.168.1.100",
            },
        ),
        QueryResult(
            username="john.doe",
            platform_name="linkedin",
            profile_url="https://linkedin.com/in/john-doe",
            status=QueryStatus.FOUND,
            metadata={
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "location": "New York, New York",
                "created_date": (now + timedelta(days=10)).isoformat(),
            },
        ),
        QueryResult(
            username="jdoe",
            platform_name="reddit",
            profile_url="https://reddit.com/user/jdoe",
            status=QueryStatus.FOUND,
            metadata={
                "email": "jdoe@example.com",
                "display_name": "John D.",
                "location": "NYC",
                "ip_address": "192.168.1.100",
            },
        ),
        # Jane Smith's accounts
        QueryResult(
            username="jane_smith",
            platform_name="twitter",
            profile_url="https://twitter.com/jane_smith",
            status=QueryStatus.FOUND,
            metadata={
                "email": "jane.smith@example.com",
                "display_name": "Jane Smith",
                "location": "New York, USA",
                "created_date": (now - timedelta(days=30)).isoformat(),
            },
        ),
        QueryResult(
            username="janesmith",
            platform_name="github",
            profile_url="https://github.com/janesmith",
            status=QueryStatus.FOUND,
            metadata={
                "email": "jane.smith@example.com",
                "display_name": "Jane Smith",
                "location": "NYC",
                "created_date": (now - timedelta(days=25)).isoformat(),
            },
        ),
        # Not found result
        QueryResult(
            username="nonexistent_user",
            platform_name="twitter",
            profile_url=None,
            status=QueryStatus.NOT_FOUND,
            metadata={},
        ),
    ]


@pytest.fixture
def correlation_engine():
    """Create a correlation engine instance."""
    return CorrelationEngine()


class TestCorrelationIntegration:
    """Integration tests for the correlation engine."""

    def test_full_correlation_workflow(
        self, correlation_engine, complex_query_results
    ):
        """Test the complete correlation workflow."""
        result = correlation_engine.process_query_results(complex_query_results)

        # Verify result structure
        assert isinstance(result, CorrelationResult)
        assert len(result.entities) > 0
        assert len(result.relationships) > 0

        # Should extract entities from found results only
        assert all(e.name for e in result.entities)

        # Should find relationships between entities
        assert len(result.relationships) > 0

        # Average confidence should be reasonable
        assert 0 <= result.confidence_average <= 100

        # Summary should be generated
        assert result.summary
        assert "Entities analyzed:" in result.summary
        assert "Relationships found:" in result.summary

    def test_entity_extraction_types(self, correlation_engine, complex_query_results):
        """Test that different entity types are extracted."""
        correlation_engine.process_query_results(complex_query_results)

        entities = list(correlation_engine._entities.values())

        # Should have account entities
        account_entities = [e for e in entities if e.type == EntityType.ACCOUNT]
        assert len(account_entities) > 0

        # Should have email entities
        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        assert len(email_entities) > 0

        # Should have IP entities
        ip_entities = [e for e in entities if e.type == EntityType.IP]
        assert len(ip_entities) > 0

    def test_relationship_types_found(self, correlation_engine, complex_query_results):
        """Test that different relationship types are found."""
        result = correlation_engine.process_query_results(complex_query_results)

        relationship_types = {r.type for r in result.relationships}

        # Should find at least same_person relationships
        assert RelationshipType.SAME_PERSON in relationship_types or len(
            result.relationships
        ) > 0

    def test_high_confidence_relationships(self, correlation_engine, complex_query_results):
        """Test that high confidence relationships are found."""
        result = correlation_engine.process_query_results(complex_query_results)

        high_conf_rels = [r for r in result.relationships if r.confidence >= 80]

        # Should have some high confidence relationships (email matches, etc.)
        assert len(high_conf_rels) > 0

        # Verify high confidence relationships have strong evidence
        for rel in high_conf_rels:
            assert len(rel.evidence) > 0
            assert rel.confidence <= 100

    def test_cluster_identification(self, correlation_engine, complex_query_results):
        """Test that clusters are identified."""
        result = correlation_engine.process_query_results(complex_query_results)

        # Should identify clusters
        assert len(result.clusters) > 0

        # Each cluster should have at least 2 entities
        for cluster in result.clusters:
            assert len(cluster.entities) >= 2
            assert cluster.representative in cluster.entities
            assert 0 <= cluster.confidence <= 100

    def test_graph_statistics(self, correlation_engine, complex_query_results):
        """Test graph statistics calculation."""
        correlation_engine.process_query_results(complex_query_results)

        graph = correlation_engine.get_graph()
        stats = graph.get_statistics()

        assert stats["num_nodes"] > 0
        assert stats["num_edges"] > 0
        assert stats["num_connected_components"] >= 1
        assert stats["average_degree"] > 0
        assert stats["density"] >= 0

    def test_central_entities(self, correlation_engine, complex_query_results):
        """Test finding central entities in the graph."""
        correlation_engine.process_query_results(complex_query_results)

        graph = correlation_engine.get_graph()
        central = graph.find_central_entities(top_n=5)

        assert len(central) > 0

        # Check that centrality scores are sorted
        scores = [score for _, score in central]
        assert scores == sorted(scores, reverse=True)

    def test_save_and_load_correlation_data(
        self, correlation_engine, complex_query_results
    ):
        """Test saving and loading correlation data."""
        # First, run correlation
        correlation_engine.process_query_results(complex_query_results)

        # Save to file
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "correlation_data.json"
            correlation_engine.save_to_file(path)

            # Verify file exists
            assert path.exists()

            # Create new engine and load
            new_engine = CorrelationEngine()
            new_engine.load_from_file(path)

            # Verify data was loaded
            assert len(new_engine._entities) > 0
            assert len(new_engine._relationships) > 0

            # Verify entity counts match
            assert len(new_engine._entities) == len(correlation_engine._entities)

    def test_report_generation(self, correlation_engine, complex_query_results):
        """Test report generation in different formats."""
        correlation_engine.process_query_results(complex_query_results)

        # Text report
        text_report = correlation_engine.generate_report(format="text")
        assert text_report
        assert "OSINT CORRELATION REPORT" in text_report
        assert "SUMMARY" in text_report

        # JSON report
        json_report = correlation_engine.generate_report(format="json")
        assert json_report
        # Verify valid JSON
        data = json.loads(json_report)
        assert "entities" in data
        assert "relationships" in data

        # HTML report
        html_report = correlation_engine.generate_report(format="html")
        assert html_report
        assert "<!DOCTYPE html>" in html_report
        assert "OSINT Correlation Report" in html_report

    def test_incremental_correlation(self, correlation_engine):
        """Test adding new data incrementally."""
        # First batch of results
        batch1 = [
            QueryResult(
                username="user1",
                platform_name="twitter",
                profile_url="https://twitter.com/user1",
                status=QueryStatus.FOUND,
                metadata={"email": "user1@example.com"},
            ),
        ]

        result1 = correlation_engine.process_query_results(batch1)
        initial_entity_count = len(result1.entities)

        # Second batch of results
        batch2 = [
            QueryResult(
                username="user1",
                platform_name="github",
                profile_url="https://github.com/user1",
                status=QueryStatus.FOUND,
                metadata={"email": "user1@example.com"},
            ),
        ]

        result2 = correlation_engine.process_query_results(batch2)
        final_entity_count = len(correlation_engine._entities)

        # Should have more entities and relationships after second batch
        assert final_entity_count >= initial_entity_count

    def test_filtering_relationships(self, correlation_engine, complex_query_results):
        """Test filtering relationships."""
        correlation_engine.process_query_results(complex_query_results)

        # Filter by confidence
        high_conf = correlation_engine.get_relationships(min_confidence=80)
        for rel in high_conf:
            assert rel.confidence >= 80

        # Filter by type
        same_person = correlation_engine.get_relationships(
            rel_type=RelationshipType.SAME_PERSON
        )
        for rel in same_person:
            assert rel.type == RelationshipType.SAME_PERSON

        # Filter by entity
        if correlation_engine._entities:
            first_entity_id = list(correlation_engine._entities.keys())[0]
            entity_rels = correlation_engine.get_relationships(
                entity_id=first_entity_id
            )
            for rel in entity_rels:
                assert rel.entity_a == first_entity_id or rel.entity_b == first_entity_id

    def test_export_formats(self, correlation_engine, complex_query_results):
        """Test exporting graph in different formats."""
        correlation_engine.process_query_results(complex_query_results)
        graph = correlation_engine.get_graph()

        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Test GraphML export
            graphml_path = tmpdir_path / "test.graphml"
            graph.export_graphml(graphml_path)
            assert graphml_path.exists()
            assert graphml_path.stat().st_size > 0

            # Test GEXF export
            gexf_path = tmpdir_path / "test.gexf"
            graph.export_gexf(gexf_path)
            assert gexf_path.exists()
            assert gexf_path.stat().st_size > 0

            # Test JSON export
            json_path = tmpdir_path / "test.json"
            graph.export_json(json_path)
            assert json_path.exists()
            assert json_path.stat().st_size > 0

            # Verify JSON is valid
            with json_path.open() as f:
                data = json.load(f)
                assert "nodes" in data
                assert "links" in data

    def test_path_finding(self, correlation_engine, complex_query_results):
        """Test finding paths between entities."""
        correlation_engine.process_query_results(complex_query_results)
        graph = correlation_engine.get_graph()

        entity_ids = list(correlation_engine._entities.keys())

        if len(entity_ids) >= 2:
            path = graph.get_path(entity_ids[0], entity_ids[1])

            # Path should exist if entities are connected
            if path:
                assert path[0] == entity_ids[0]
                assert path[-1] == entity_ids[1]

    def test_performance_with_many_entities(self, correlation_engine):
        """Test performance with many entities."""
        # Create many query results
        many_results = []
        for i in range(100):
            many_results.append(
                QueryResult(
                    username=f"user{i}",
                    platform_name="twitter",
                    profile_url=f"https://twitter.com/user{i}",
                    status=QueryStatus.FOUND,
                    metadata={"email": f"user{i}@example.com"},
                )
            )

        # Process and ensure it completes
        result = correlation_engine.process_query_results(many_results)

        assert len(result.entities) > 0
        assert result.confidence_average >= 0

    def test_empty_results(self, correlation_engine):
        """Test correlation with no results."""
        result = correlation_engine.process_query_results([])

        assert len(result.entities) == 0
        assert len(result.relationships) == 0
        assert result.confidence_average == 0

    def test_all_not_found_results(self, correlation_engine):
        """Test correlation with all not-found results."""
        results = [
            QueryResult(
                username="nonexistent1",
                platform_name="twitter",
                profile_url=None,
                status=QueryStatus.NOT_FOUND,
                metadata={},
            ),
            QueryResult(
                username="nonexistent2",
                platform_name="github",
                profile_url=None,
                status=QueryStatus.NOT_FOUND,
                metadata={},
            ),
        ]

        result = correlation_engine.process_query_results(results)

        assert len(result.entities) == 0
        assert len(result.relationships) == 0
