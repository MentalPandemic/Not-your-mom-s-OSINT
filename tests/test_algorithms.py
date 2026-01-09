from __future__ import annotations

import pytest

from osint.core.algorithms.email import EmailCorrelationAlgorithm
from osint.core.algorithms.metadata import MetadataCorrelationAlgorithm
from osint.core.algorithms.network import NetworkCorrelationAlgorithm
from osint.core.algorithms.temporal import TemporalCorrelationAlgorithm
from osint.core.algorithms.username import UsernameCorrelationAlgorithm
from osint.core.models import (
    Entity,
    EntityType,
    RelationshipType,
)


@pytest.fixture
def email_algorithm():
    """Create email correlation algorithm instance."""
    return EmailCorrelationAlgorithm()


@pytest.fixture
def username_algorithm():
    """Create username correlation algorithm instance."""
    return UsernameCorrelationAlgorithm()


@pytest.fixture
def metadata_algorithm():
    """Create metadata correlation algorithm instance."""
    return MetadataCorrelationAlgorithm()


@pytest.fixture
def network_algorithm():
    """Create network correlation algorithm instance."""
    return NetworkCorrelationAlgorithm()


@pytest.fixture
def temporal_algorithm():
    """Create temporal correlation algorithm instance."""
    return TemporalCorrelationAlgorithm()


class TestUsernameCorrelationAlgorithm:
    """Test username correlation algorithm."""

    def test_exact_username_match(self, username_algorithm):
        """Test exact username matching."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="john_doe",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="john_doe",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = username_algorithm.correlate(entities)

        assert len(relationships) == 1
        assert relationships[0].type == RelationshipType.SAME_PERSON
        assert relationships[0].confidence == 100.0

    def test_pattern_username_variation(self, username_algorithm):
        """Test username pattern variation matching."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="john_doe",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="johndoe",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = username_algorithm.correlate(entities)

        assert len(relationships) >= 1
        assert relationships[0].type == RelationshipType.POTENTIAL

    def test_no_correlation_different_usernames(self, username_algorithm):
        """Test that different usernames don't correlate."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="john_doe",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="jane_smith",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = username_algorithm.correlate(entities)

        # Should not correlate completely different usernames
        same_person_rels = [
            r for r in relationships if r.type == RelationshipType.SAME_PERSON
        ]
        assert len(same_person_rels) == 0


class TestEmailCorrelationAlgorithm:
    """Test email correlation algorithm."""

    def test_exact_email_match(self, email_algorithm):
        """Test exact email matching."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.EMAIL,
                name="john.doe@example.com",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.EMAIL,
                name="john.doe@example.com",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = email_algorithm.correlate(entities)

        assert len(relationships) == 1
        assert relationships[0].type == RelationshipType.SAME_PERSON
        assert relationships[0].confidence == 100.0

    def test_email_domain_correlation(self, email_algorithm):
        """Test email domain correlation."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="john_doe",
                attributes={"email": "john.doe@example.com"},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.EMAIL,
                name="john.doe@example.com",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = email_algorithm.correlate(entities)

        assert len(relationships) >= 1
        assert relationships[0].type == RelationshipType.SAME_PERSON

    def test_email_account_correlation(self, email_algorithm):
        """Test email to account correlation."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.EMAIL,
                name="test@example.com",
                attributes={},
                sources=["manual"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="username",
                attributes={"email": "test@example.com"},
                sources=["twitter"],
            ),
        ]

        relationships = email_algorithm.correlate(entities)

        assert len(relationships) >= 1


class TestMetadataCorrelationAlgorithm:
    """Test metadata correlation algorithm."""

    def test_bio_similarity(self, metadata_algorithm):
        """Test bio/description similarity matching."""
        bio_text = "Software developer and open source enthusiast"

        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={"bio": bio_text},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="user2",
                attributes={"bio": bio_text},
                sources=["github"],
            ),
        ]

        relationships = metadata_algorithm.correlate(entities)

        assert len(relationships) >= 1

    def test_location_match(self, metadata_algorithm):
        """Test location matching."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={"location": "New York, USA"},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="user2",
                attributes={"location": "New York, USA"},
                sources=["github"],
            ),
        ]

        relationships = metadata_algorithm.correlate(entities)

        # Should find location correlation
        location_rels = [
            r
            for r in relationships
            if "location" in r.metadata.get("match_type", "")
        ]
        assert len(location_rels) >= 1

    def test_display_name_match(self, metadata_algorithm):
        """Test display name matching."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={"display_name": "John Doe"},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="user2",
                attributes={"display_name": "John Doe"},
                sources=["github"],
            ),
        ]

        relationships = metadata_algorithm.correlate(entities)

        assert len(relationships) >= 1


class TestNetworkCorrelationAlgorithm:
    """Test network correlation algorithm."""

    def test_exact_ip_match(self, network_algorithm):
        """Test exact IP matching."""
        ip_address = "192.168.1.1"

        entities = [
            Entity(
                id="entity_1",
                type=EntityType.IP,
                name=ip_address,
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.IP,
                name=ip_address,
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = network_algorithm.correlate(entities)

        assert len(relationships) == 1
        assert relationships[0].confidence == 100.0

    def test_ip_subnet_correlation(self, network_algorithm):
        """Test IP subnet correlation."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.IP,
                name="192.168.1.10",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.IP,
                name="192.168.1.20",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = network_algorithm.correlate(entities)

        assert len(relationships) >= 1

    def test_exact_domain_match(self, network_algorithm):
        """Test exact domain matching."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.DOMAIN,
                name="example.com",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.DOMAIN,
                name="example.com",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = network_algorithm.correlate(entities)

        assert len(relationships) == 1
        assert relationships[0].confidence == 100.0

    def test_subdomain_correlation(self, network_algorithm):
        """Test subdomain relationship detection."""
        entities = [
            Entity(
                id="entity_1",
                type=EntityType.DOMAIN,
                name="www.example.com",
                attributes={},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.DOMAIN,
                name="example.com",
                attributes={},
                sources=["github"],
            ),
        ]

        relationships = network_algorithm.correlate(entities)

        assert len(relationships) >= 1
        assert relationships[0].type == RelationshipType.RELATED


class TestTemporalCorrelationAlgorithm:
    """Test temporal correlation algorithm."""

    def test_account_creation_correlation(self, temporal_algorithm):
        """Test account creation date correlation."""
        from datetime import datetime, timedelta

        now = datetime.now()

        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={"created_date": now},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="user2",
                attributes={"created_date": now + timedelta(days=10)},
                sources=["github"],
            ),
        ]

        relationships = temporal_algorithm.correlate(entities)

        # Should find correlation for accounts created within 30 days
        assert len(relationships) >= 1

    def test_no_temporal_correlation_old_accounts(self, temporal_algorithm):
        """Test that old accounts don't correlate temporally."""
        from datetime import datetime, timedelta

        entities = [
            Entity(
                id="entity_1",
                type=EntityType.ACCOUNT,
                name="user1",
                attributes={"created_date": datetime.now()},
                sources=["twitter"],
            ),
            Entity(
                id="entity_2",
                type=EntityType.ACCOUNT,
                name="user2",
                attributes={"created_date": datetime.now() - timedelta(days=365)},
                sources=["github"],
            ),
        ]

        relationships = temporal_algorithm.correlate(entities)

        # Should not correlate accounts created a year apart
        assert len(relationships) == 0
