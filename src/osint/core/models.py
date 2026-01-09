from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class QueryStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"


class EntityType(str, Enum):
    PERSON = "person"
    ACCOUNT = "account"
    EMAIL = "email"
    PHONE = "phone"
    DOMAIN = "domain"
    IP = "ip"


class RelationshipType(str, Enum):
    SAME_PERSON = "same_person"
    RELATED = "related"
    POTENTIAL = "potential"
    SUSPICIOUS = "suspicious"


@dataclass(frozen=True, slots=True)
class QueryResult:
    username: str
    platform_name: str
    profile_url: str | None
    status: QueryStatus
    response_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "platform_name": self.platform_name,
            "profile_url": self.profile_url,
            "status": self.status.value,
            "response_time": self.response_time,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class Entity:
    id: str
    type: EntityType
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "attributes": self.attributes,
            "sources": self.sources,
            "created_date": self.created_date.isoformat(),
        }


@dataclass(slots=True)
class Relationship:
    id: str
    entity_a: str
    entity_b: str
    type: RelationshipType
    confidence: float
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entity_a": self.entity_a,
            "entity_b": self.entity_b,
            "type": self.type.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class EntityCluster:
    id: str
    entities: list[str]
    representative: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "entities": self.entities,
            "representative": self.representative,
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class CorrelationResult:
    entities: list[Entity]
    relationships: list[Relationship]
    clusters: list[EntityCluster]
    confidence_average: float
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "clusters": [c.to_dict() for c in self.clusters],
            "confidence_average": self.confidence_average,
            "summary": self.summary,
        }
