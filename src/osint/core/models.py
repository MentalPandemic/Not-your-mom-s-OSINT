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


class SocialPlatform(str, Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"


@dataclass(slots=True)
class EngagementMetrics:
    avg_engagement_rate: float
    total_engagement: int
    post_frequency: float
    most_active_hours: list[str] = field(default_factory=list)
    audience_demographics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "avg_engagement_rate": self.avg_engagement_rate,
            "total_engagement": self.total_engagement,
            "post_frequency": self.post_frequency,
            "most_active_hours": self.most_active_hours,
            "audience_demographics": self.audience_demographics,
        }


@dataclass(slots=True)
class Post:
    id: str
    platform: SocialPlatform
    text: str
    timestamp: datetime | None
    likes: int = 0
    shares: int = 0
    comments: int = 0
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    media_urls: list[str] = field(default_factory=list)
    sentiment: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "media_urls": self.media_urls,
            "sentiment": self.sentiment,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class SocialProfile:
    platform: SocialPlatform
    user_id: str
    username: str
    display_name: str
    bio: str
    profile_url: str
    profile_picture_url: str | None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    verified: bool = False
    created_date: datetime | None = None
    last_update: datetime = field(default_factory=lambda: datetime.now())
    metadata: dict[str, Any] = field(default_factory=dict)
    posts: list[Post] = field(default_factory=list)
    engagement_metrics: EngagementMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform.value,
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
            "profile_url": self.profile_url,
            "profile_picture_url": self.profile_picture_url,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "post_count": self.post_count,
            "verified": self.verified,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "last_update": self.last_update.isoformat(),
            "metadata": self.metadata,
            "posts": [p.to_dict() for p in self.posts],
            "engagement_metrics": self.engagement_metrics.to_dict() if self.engagement_metrics else None,
        }
