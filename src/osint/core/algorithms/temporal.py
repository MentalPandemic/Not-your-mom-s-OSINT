from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from osint.core.models import Entity, EntityType, Relationship, RelationshipType


class TemporalCorrelationAlgorithm:
    """Correlates entities based on temporal patterns (creation dates, activity, etc.)."""

    def __init__(
        self,
        creation_window_days: int = 30,
        activity_window_hours: int = 24,
    ) -> None:
        self.creation_window_days = creation_window_days
        self.activity_window_hours = activity_window_hours

    def correlate(self, entities: list[Entity]) -> list[Relationship]:
        """Find temporal correlations between entities."""
        relationships: list[Relationship] = []

        account_entities = [e for e in entities if e.type == EntityType.ACCOUNT]

        for i, entity_a in enumerate(account_entities):
            for entity_b in account_entities[i + 1 :]:
                # Check account creation date correlation
                creation_result = self._correlate_by_creation_date(entity_a, entity_b)
                if creation_result:
                    relationships.append(creation_result)

                # Check activity time correlation
                activity_result = self._correlate_by_activity_time(entity_a, entity_b)
                if activity_result:
                    relationships.append(activity_result)

        return relationships

    def _correlate_by_creation_date(
        self, entity_a: Entity, entity_b: Entity
    ) -> Relationship | None:
        """Correlate entities based on account creation dates."""
        created_a = entity_a.attributes.get("created_date")
        created_b = entity_b.attributes.get("created_date")

        if not created_a or not created_b:
            return None

        # Parse dates if they're strings
        if isinstance(created_a, str):
            created_a = self._parse_datetime(created_a)
        if isinstance(created_b, str):
            created_b = self._parse_datetime(created_b)

        if not created_a or not created_b:
            return None

        # Calculate the time difference
        time_diff = abs((created_a - created_b).total_seconds())
        window_seconds = self.creation_window_days * 24 * 60 * 60

        # Check if creation dates are within the window
        if time_diff <= window_seconds:
            # Calculate confidence based on how close the dates are
            confidence = 50.0 * (1.0 - (time_diff / window_seconds))

            evidence = f"Account creation dates within {self.creation_window_days} days"
            if time_diff < 86400:  # Within 24 hours
                evidence = f"Account creation dates within 24 hours"
                confidence = min(confidence + 20.0, 90.0)

            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_creation_date",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=confidence,
                evidence=[evidence],
                metadata={
                    "match_type": "creation_date",
                    "created_a": self._format_datetime(created_a),
                    "created_b": self._format_datetime(created_b),
                    "time_diff_hours": time_diff / 3600,
                },
            )

        return None

    def _correlate_by_activity_time(
        self, entity_a: Entity, entity_b: Entity
    ) -> Relationship | None:
        """Correlate entities based on activity time patterns."""
        activity_times_a = entity_a.attributes.get("activity_times", [])
        activity_times_b = entity_b.attributes.get("activity_times", [])

        if not activity_times_a or not activity_times_b:
            return None

        # Parse activity times if they're strings
        activity_times_a = [
            (self._parse_datetime(t) if isinstance(t, str) else t)
            for t in activity_times_a
            if (self._parse_datetime(t) if isinstance(t, str) else t)
        ]
        activity_times_b = [
            (self._parse_datetime(t) if isinstance(t, str) else t)
            for t in activity_times_b
            if (self._parse_datetime(t) if isinstance(t, str) else t)
        ]

        if not activity_times_a or not activity_times_b:
            return None

        # Check for overlapping activity times
        overlap_count = 0
        window_seconds = self.activity_window_hours * 3600

        for time_a in activity_times_a:
            for time_b in activity_times_b:
                time_diff = abs((time_a - time_b).total_seconds())
                if time_diff <= window_seconds:
                    overlap_count += 1
                    break

        # Calculate overlap ratio
        total_checks = min(len(activity_times_a), len(activity_times_b))
        overlap_ratio = overlap_count / total_checks if total_checks > 0 else 0

        # If significant overlap, create a relationship
        if overlap_ratio >= 0.3:  # At least 30% overlap
            confidence = 40.0 + (overlap_ratio * 40.0)

            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_activity_overlap",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=confidence,
                evidence=[
                    f"Activity time overlap: {overlap_ratio:.1%} of activities within {self.activity_window_hours} hours"
                ],
                metadata={
                    "match_type": "activity_overlap",
                    "overlap_ratio": overlap_ratio,
                    "overlap_count": overlap_count,
                    "total_checked": total_checks,
                },
            )

        return None

    def _parse_datetime(self, dt_str: str) -> datetime | None:
        """Parse a datetime string in various formats."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue

        return None

    def _format_datetime(self, dt: datetime) -> str:
        """Format a datetime for display."""
        return dt.isoformat()
