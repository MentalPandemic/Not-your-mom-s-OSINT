from __future__ import annotations

import re
from typing import Any

try:
    import Levenshtein
except ImportError:
    Levenshtein = None

from osint.core.models import Entity, EntityType, Relationship, RelationshipType


class UsernameCorrelationAlgorithm:
    """Correlates usernames across platforms using various matching strategies."""

    def __init__(self, fuzzy_threshold: float = 0.85) -> None:
        self.fuzzy_threshold = fuzzy_threshold
        # Store patterns with their regex pattern strings
        self.patterns = [
            (r"^(.+)_(.+)$", r"^(.+)_(.+)$"),  # firstname_lastname
            (r"^(.+?)[-_](.+)$", r"^(.+?)[-_](.+)$"),  # separator variants
            (r"^(.+)\.(.+)$", r"^(.+)\.(.+)$"),  # firstname.lastname
            (r"^(.+?)\d+$", r"^(.+?)\d+$"),  # johndoe99 -> johndoe
            (r"^(.+)\d+$", r"^(.+)\d+$"),  # johndoe99 -> johndoe
        ]

    def correlate(self, entities: list[Entity]) -> list[Relationship]:
        """Find username correlations between entities."""
        relationships: list[Relationship] = []

        for i, entity_a in enumerate(entities):
            for entity_b in entities[i + 1 :]:
                if self._can_correlate(entity_a, entity_b):
                    result = self._correlate_pair(entity_a, entity_b)
                    if result:
                        relationships.append(result)

        return relationships

    def _can_correlate(self, entity_a: Entity, entity_b: Entity) -> bool:
        """Check if two entities can be correlated by username."""
        if entity_a.type not in {EntityType.ACCOUNT, EntityType.PERSON}:
            return False
        if entity_b.type not in {EntityType.ACCOUNT, EntityType.PERSON}:
            return False
        if entity_a.id == entity_b.id:
            return False

        return bool(entity_a.name and entity_b.name)

    def _correlate_pair(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate a pair of entities by username."""
        username_a = entity_a.name.lower()
        username_b = entity_b.name.lower()

        # Try exact match first
        if username_a == username_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.SAME_PERSON,
                confidence=100.0,
                evidence=["Exact username match"],
                metadata={"match_type": "exact"},
            )

        # Try fuzzy match
        fuzzy_result = self._fuzzy_match(entity_a, entity_b, username_a, username_b)
        if fuzzy_result:
            return fuzzy_result

        # Try pattern variations
        pattern_result = self._pattern_match(entity_a, entity_b, username_a, username_b)
        if pattern_result:
            return pattern_result

        return None

    def _fuzzy_match(
        self, entity_a: Entity, entity_b: Entity, username_a: str, username_b: str
    ) -> Relationship | None:
        """Check if usernames are similar using fuzzy matching."""
        if Levenshtein:
            distance = Levenshtein.distance(username_a, username_b)
            max_len = max(len(username_a), len(username_b))
            if max_len == 0:
                return None

            similarity = 1.0 - (distance / max_len)
            if similarity >= self.fuzzy_threshold:
                confidence = similarity * 80.0
                return Relationship(
                    id=f"rel_{entity_a.id}_{entity_b.id}_fuzzy",
                    entity_a=entity_a.id,
                    entity_b=entity_b.id,
                    type=RelationshipType.POTENTIAL,
                    confidence=confidence,
                    evidence=[f"Fuzzy match: {similarity:.2%} similarity"],
                    metadata={
                        "match_type": "fuzzy",
                        "similarity": similarity,
                        "distance": distance,
                    },
                )

        return None

    def _pattern_match(
        self, entity_a: Entity, entity_b: Entity, username_a: str, username_b: str
    ) -> Relationship | None:
        """Check if usernames follow common variation patterns."""
        patterns = [
            # john_doe vs johndoe
            (r"^(.+)_(.+)$", lambda m: m.group(1) + m.group(2)),
            # johndoe vs john_doe
            (r"^(.+?)[-_](.+)$", lambda m: m.group(1) + m.group(2)),
            # john.doe vs johndoe
            (r"^(.+)\.(.+)$", lambda m: m.group(1) + m.group(2)),
            # johndoe99 vs johndoe
            (r"^(.+?)\d+$", lambda m: m.group(1)),
            # johndoe vs johndoe99
            (r"^(.+)\d+$", lambda m: m.group(1)),
        ]

        for pattern_str, transform in patterns:
            # Try to transform username_a to match username_b
            match_a = re.match(pattern_str, username_a)
            if match_a:
                transformed = transform(match_a)
                if transformed == username_b:
                    return Relationship(
                        id=f"rel_{entity_a.id}_{entity_b.id}_pattern",
                        entity_a=entity_a.id,
                        entity_b=entity_b.id,
                        type=RelationshipType.POTENTIAL,
                        confidence=75.0,
                        evidence=[f"Pattern variation: {username_a} -> {username_b}"],
                        metadata={"match_type": "pattern", "pattern": pattern_str},
                    )

            # Try to transform username_b to match username_a
            match_b = re.match(pattern_str, username_b)
            if match_b:
                transformed = transform(match_b)
                if transformed == username_a:
                    return Relationship(
                        id=f"rel_{entity_a.id}_{entity_b.id}_pattern",
                        entity_a=entity_a.id,
                        entity_b=entity_b.id,
                        type=RelationshipType.POTENTIAL,
                        confidence=75.0,
                        evidence=[f"Pattern variation: {username_b} -> {username_a}"],
                        metadata={"match_type": "pattern", "pattern": pattern_str},
                    )

        # Check for common separators
        normalized_a = re.sub(r"[-_.]", "", username_a).lower()
        normalized_b = re.sub(r"[-_.]", "", username_b).lower()

        if normalized_a == normalized_b and username_a != username_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_separator",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=70.0,
                evidence=["Same username with different separators"],
                metadata={
                    "match_type": "separator",
                    "normalized": normalized_a,
                },
            )

        return None
