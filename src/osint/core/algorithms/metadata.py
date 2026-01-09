from __future__ import annotations

import re
from typing import Any

from osint.core.models import Entity, EntityType, Relationship, RelationshipType


class MetadataCorrelationAlgorithm:
    """Correlates entities based on metadata (bios, locations, profile images, etc.)."""

    def __init__(self, similarity_threshold: float = 0.7) -> None:
        self.similarity_threshold = similarity_threshold

    def correlate(self, entities: list[Entity]) -> list[Relationship]:
        """Find metadata correlations between entities."""
        relationships: list[Relationship] = []

        account_entities = [e for e in entities if e.type == EntityType.ACCOUNT]

        for i, entity_a in enumerate(account_entities):
            for entity_b in account_entities[i + 1 :]:
                # Check each type of metadata
                bio_result = self._correlate_by_bio(entity_a, entity_b)
                if bio_result:
                    relationships.append(bio_result)

                location_result = self._correlate_by_location(entity_a, entity_b)
                if location_result:
                    relationships.append(location_result)

                name_result = self._correlate_by_name(entity_a, entity_b)
                if name_result:
                    relationships.append(name_result)

                website_result = self._correlate_by_website(entity_a, entity_b)
                if website_result:
                    relationships.append(website_result)

        return relationships

    def _correlate_by_bio(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate entities based on bio/description text."""
        bio_a = entity_a.attributes.get("bio", "")
        bio_b = entity_b.attributes.get("bio", "")

        if not bio_a or not bio_b:
            return None

        # Normalize bios for comparison
        normalized_a = self._normalize_text(bio_a)
        normalized_b = self._normalize_text(bio_b)

        # Check for exact match
        if normalized_a == normalized_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_bio_exact",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=85.0,
                evidence=["Identical bio/description text"],
                metadata={"match_type": "bio_exact", "bio": bio_a},
            )

        # Check for partial overlap
        if len(normalized_a) > 20 and len(normalized_b) > 20:
            overlap = self._calculate_text_overlap(normalized_a, normalized_b)
            if overlap >= self.similarity_threshold:
                confidence = 50.0 + (overlap * 30.0)
                return Relationship(
                    id=f"rel_{entity_a.id}_{entity_b.id}_bio_similar",
                    entity_a=entity_a.id,
                    entity_b=entity_b.id,
                    type=RelationshipType.POTENTIAL,
                    confidence=confidence,
                    evidence=[f"Similar bio text: {overlap:.1%} overlap"],
                    metadata={
                        "match_type": "bio_similar",
                        "overlap": overlap,
                        "bio_a": bio_a[:100],
                        "bio_b": bio_b[:100],
                    },
                )

        return None

    def _correlate_by_location(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate entities based on location."""
        location_a = entity_a.attributes.get("location", "").lower()
        location_b = entity_b.attributes.get("location", "").lower()

        if not location_a or not location_b:
            return None

        # Normalize location strings
        normalized_a = self._normalize_location(location_a)
        normalized_b = self._normalize_location(location_b)

        # Exact match
        if normalized_a == normalized_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_location_exact",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=60.0,
                evidence=[f"Same location: {location_a}"],
                metadata={"match_type": "location_exact", "location": location_a},
            )

        # Check for hierarchical relationships (e.g., "New York" vs "New York, USA")
        if normalized_a in normalized_b or normalized_b in normalized_a:
            confidence = 45.0 if normalized_a != normalized_b else 60.0
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_location_related",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=confidence,
                evidence=[f"Related locations: {location_a} <-> {location_b}"],
                metadata={
                    "match_type": "location_related",
                    "location_a": location_a,
                    "location_b": location_b,
                },
            )

        return None

    def _correlate_by_name(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate entities based on display name."""
        name_a = entity_a.attributes.get("display_name", "")
        name_b = entity_b.attributes.get("display_name", "")

        if not name_a or not name_b:
            return None

        # Normalize names
        normalized_a = self._normalize_name(name_a)
        normalized_b = self._normalize_name(name_b)

        # Exact match
        if normalized_a == normalized_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_name_exact",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=75.0,
                evidence=[f"Same display name: {name_a}"],
                metadata={"match_type": "name_exact", "name": name_a},
            )

        # Check for partial name match
        name_parts_a = set(normalized_a.split())
        name_parts_b = set(normalized_b.split())

        if len(name_parts_a) > 1 and len(name_parts_b) > 1:
            intersection = name_parts_a & name_parts_b
            if intersection:
                # Calculate overlap ratio
                overlap_ratio = len(intersection) / min(
                    len(name_parts_a), len(name_parts_b)
                )
                if overlap_ratio >= 0.5:
                    confidence = 40.0 + (overlap_ratio * 20.0)
                    return Relationship(
                        id=f"rel_{entity_a.id}_{entity_b.id}_name_partial",
                        entity_a=entity_a.id,
                        entity_b=entity_b.id,
                        type=RelationshipType.POTENTIAL,
                        confidence=confidence,
                        evidence=[
                            f"Partial name match: {', '.join(sorted(intersection))}"
                        ],
                        metadata={
                            "match_type": "name_partial",
                            "name_a": name_a,
                            "name_b": name_b,
                            "common_parts": list(intersection),
                        },
                    )

        return None

    def _correlate_by_website(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate entities based on website/URL."""
        website_a = entity_a.attributes.get("website", "").lower()
        website_b = entity_b.attributes.get("website", "").lower()

        if not website_a or not website_b:
            return None

        # Normalize URLs
        normalized_a = self._normalize_url(website_a)
        normalized_b = self._normalize_url(website_b)

        # Exact match
        if normalized_a == normalized_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_website_exact",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=80.0,
                evidence=[f"Same website: {website_a}"],
                metadata={"match_type": "website_exact", "website": website_a},
            )

        return None

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace and convert to lowercase
        text = re.sub(r"\s+", " ", text)
        text = text.strip().lower()
        # Remove common punctuation
        text = re.sub(r'[.,!?;:"\'()]', "", text)
        return text

    def _normalize_location(self, location: str) -> str:
        """Normalize location for comparison."""
        location = location.strip().lower()
        # Remove common suffixes
        location = re.sub(r"\s+(usa|us|united states|uk|united kingdom)$", "", location)
        return location

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        name = name.strip().lower()
        # Remove common titles
        name = re.sub(r"^(mr|ms|mrs|dr|prof)\.?\s+", "", name)
        # Remove extra whitespace
        name = re.sub(r"\s+", " ", name)
        return name

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        url = url.strip().lower()
        # Remove protocol and www
        url = re.sub(r"^https?://(www\.)?", "", url)
        # Remove trailing slash
        url = url.rstrip("/")
        return url

    def _calculate_text_overlap(self, text_a: str, text_b: str) -> float:
        """Calculate the overlap ratio between two texts using n-grams."""
        def get_ngrams(text: str, n: int = 3) -> set[str]:
            ngrams: set[str] = set()
            for i in range(len(text) - n + 1):
                ngrams.add(text[i : i + n])
            return ngrams

        ngrams_a = get_ngrams(text_a)
        ngrams_b = get_ngrams(text_b)

        if not ngrams_a or not ngrams_b:
            return 0.0

        intersection = ngrams_a & ngrams_b
        union = ngrams_a | ngrams_b

        return len(intersection) / len(union) if union else 0.0
