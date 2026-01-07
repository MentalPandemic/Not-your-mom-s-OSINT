"""
Database Models and Integration for Username Enumeration

Provides SQLAlchemy models for PostgreSQL and Neo4j graph integration
for storing and querying username enumeration results.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, 
    ForeignKey, Index, JSON, UniqueConstraint, CheckConstraint,
    create_engine, select, func, and_, or_,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    relationship, 
    selectinload,
    joinedload,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, insert
import uuid

import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class ConfidenceLevel(str, Enum):
    """Confidence levels for matches"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class PlatformStatus(str, Enum):
    """Status codes for platform checks"""
    FOUND = "found"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    ERROR = "error"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class Identity(Base):
    """
    Core identity record representing a person/entity.
    
    This is the central table that ties together all discovered attributes
    (usernames, emails, phones) and sources across platforms.
    """
    __tablename__ = "identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Primary identifiers
    primary_username = Column(String(255), nullable=True, index=True)
    primary_email = Column(String(255), nullable=True, index=True)
    primary_phone = Column(String(50), nullable=True, index=True)
    
    # Computed fields
    confidence_score = Column(Float, default=0.0)
    last_verified = Column(DateTime(timezone=True), nullable=True)
    verification_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attributes = relationship("IdentityAttribute", back_populates="identity", cascade="all, delete-orphan")
    sources = relationship("IdentitySource", back_populates="identity", cascade="all, delete-orphan")
    relationships = relationship(
        "IdentityRelationship",
        primaryjoin="or_(IdentityRelationship.identity_a_id==Identity.id, IdentityRelationship.identity_b_id==Identity.id)",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index('idx_identity_primary', 'primary_username', 'primary_email', 'primary_phone'),
    )

    def __repr__(self):
        return f"<Identity(id={self.id}, primary_username={self.primary_username})>"


class IdentityAttribute(Base):
    """
    Attributes discovered for an identity (usernames, emails, phones).
    
    Each attribute is linked to the main identity and includes metadata
    about when and where it was discovered.
    """
    __tablename__ = "identity_attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id = Column(UUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    
    # Attribute type and value
    attribute_type = Column(String(50), nullable=False, index=True)  # username, email, phone, etc.
    attribute_value = Column(String(500), nullable=False, index=True)
    
    # Metadata
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    confidence = Column(String(20), default=ConfidenceLevel.MEDIUM.value)
    
    # Source information
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    discovered_from = Column(String(255))  # Platform or source where discovered
    
    # Relationships
    identity = relationship("Identity", back_populates="attributes")

    __table_args__ = (
        UniqueConstraint('identity_id', 'attribute_type', 'attribute_value', name='uq_attribute_identity'),
        Index('idx_attribute_value', 'attribute_type', 'attribute_value'),
    )

    def __repr__(self):
        return f"<IdentityAttribute(type={self.attribute_type}, value={self.attribute_value})>"


class IdentitySource(Base):
    """
    Sources/platforms where an identity was found.
    
    Records each platform check, including results, confidence scores,
    and response times.
    """
    __tablename__ = "identity_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id = Column(UUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    
    # Platform information
    platform = Column(String(100), nullable=False, index=True)
    platform_category = Column(String(50))
    
    # Profile information
    profile_url = Column(String(1000))
    username_found = Column(String(255))
    
    # Detection details
    status = Column(String(20), nullable=False)  # found, not_found, timeout, error, blocked
    confidence = Column(String(20), default=ConfidenceLevel.MEDIUM.value)
    confidence_score = Column(Float)  # 0-1 numeric score
    
    # Response data
    http_status = Column(Integer)
    response_time = Column(Float)  # seconds
    detection_method = Column(String(50))  # status_code, html_content, json_api, etc.
    
    # Additional profile data (JSON)
    profile_data = Column(JSONB)
    
    # Metadata
    last_checked = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    reliability_rating = Column(Float)  # 0-1 rating of platform reliability
    
    # Relationships
    identity = relationship("Identity", back_populates="sources")

    __table_args__ = (
        Index('idx_source_platform', 'platform', 'status'),
        Index('idx_source_last_checked', 'last_checked'),
    )

    def __repr__(self):
        return f"<IdentitySource(platform={self.platform}, status={self.status})>"


class IdentityRelationship(Base):
    """
    Relationships between identities (e.g., same person, linked accounts).
    
    Represents connections between different identity records, such as
    when a username found on one platform links to another username/email
    that belongs to a different identity record.
    """
    __tablename__ = "identity_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Related identities
    identity_a_id = Column(UUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    identity_b_id = Column(UUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    
    # Relationship details
    relationship_type = Column(String(50), nullable=False)  # SAME_PERSON, LINKED_ACCOUNT, POSSIBLE_MATCH
    confidence = Column(Float, default=0.0)
    
    # Source of relationship
    source_platform = Column(String(100))
    evidence = Column(Text)  # Description of evidence for this relationship
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    verified = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('identity_a_id', 'identity_b_id', 'relationship_type', name='uq_relationship'),
        CheckConstraint('identity_a_id != identity_b_id', name='check_different_identities'),
    )

    def __repr__(self):
        return f"<IdentityRelationship(type={self.relationship_type}, confidence={self.confidence})>"


class SearchCache(Base):
    """
    Cache for search results to avoid redundant platform checks.
    
    Stores recent enumeration results with TTL for quick lookups.
    """
    __tablename__ = "search_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Search parameters
    search_key = Column(String(500), nullable=False, unique=True, index=True)
    search_type = Column(String(50), nullable=False)  # username, email, phone
    
    # Search results (JSON)
    results = Column(JSONB, nullable=False)
    
    # Cache metadata
    platform_count = Column(Integer)  # Number of platforms checked
    matches_found = Column(Integer)  # Number of matches found
    search_duration = Column(Float)  # Time taken for search
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    hit_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<SearchCache(key={self.search_key}, matches={self.matches_found})>"


class DatabaseManager:
    """
    Manager for database operations with async support.
    
    Handles connections, sessions, and common operations for username
    enumeration data.
    """

    def __init__(self, database_url: str):
        """
        Initialize the database manager.
        
        Args:
            database_url: PostgreSQL async connection URL
                (e.g., postgresql+asyncpg://user:pass@localhost/dbname)
        """
        self.database_url = database_url
        self.engine = None
        self.async_session_maker = None

    async def initialize(self):
        """Initialize database engine and session maker"""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=40,
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info("Database manager initialized")

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

    async def create_tables(self):
        """Create all tables (for development/testing)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return self.async_session_maker()

    async def store_search_results(
        self,
        search_identifier: str,
        search_type: str,
        results: List[Dict],
        duration: float = 0.0,
    ) -> Identity:
        """
        Store search results in the database.
        
        Args:
            search_identifier: The identifier that was searched (username, email, etc.)
            search_type: Type of identifier (username, email, phone)
            results: List of search results from enumeration
            duration: Time taken for the search
            
        Returns:
            The created or updated Identity record
        """
        async with self.get_session() as session:
            # Find or create identity
            identity = await self._find_or_create_identity(
                session,
                search_identifier,
                search_type,
            )
            
            # Store each result as a source
            for result in results:
                source = IdentitySource(
                    identity_id=identity.id,
                    platform=result.get("platform", "unknown"),
                    platform_category=result.get("category"),
                    profile_url=result.get("profile_url"),
                    username_found=result.get("username"),
                    status=result.get("status", PlatformStatus.UNKNOWN.value),
                    confidence=result.get("confidence", ConfidenceLevel.MEDIUM.value),
                    confidence_score=self._confidence_to_score(result.get("confidence")),
                    http_status=result.get("response_code"),
                    response_time=result.get("response_time"),
                    detection_method=result.get("detection_method"),
                    profile_data=result.get("profile_data", {}),
                    reliability_rating=result.get("reliability", 0.8),
                )
                session.add(source)
            
            # Update identity metadata
            identity.last_verified = datetime.utcnow()
            identity.verification_count += 1
            identity.confidence_score = await self._calculate_identity_confidence(session, identity.id)
            
            await session.commit()
            await session.refresh(identity)
            
            logger.info(f"Stored {len(results)} results for {search_type}: {search_identifier}")
            return identity

    async def _find_or_create_identity(
        self,
        session: AsyncSession,
        identifier: str,
        identifier_type: str,
    ) -> Identity:
        """Find existing identity or create a new one"""
        # Try to find existing identity by attribute
        result = await session.execute(
            select(Identity)
            .join(IdentityAttribute)
            .where(
                and_(
                    IdentityAttribute.attribute_value == identifier.lower(),
                    IdentityAttribute.attribute_type == identifier_type,
                )
            )
            .limit(1)
        )
        identity = result.scalar_one_or_none()
        
        if identity:
            return identity
        
        # Create new identity
        identity = Identity()
        
        # Set primary identifier
        if identifier_type == "username":
            identity.primary_username = identifier
        elif identifier_type == "email":
            identity.primary_email = identifier
        elif identifier_type == "phone":
            identity.primary_phone = identifier
        
        session.add(identity)
        await session.flush()
        
        # Add initial attribute
        attribute = IdentityAttribute(
            identity_id=identity.id,
            attribute_type=identifier_type,
            attribute_value=identifier.lower(),
            is_primary=True,
        )
        session.add(attribute)
        
        return identity

    async def _calculate_identity_confidence(
        self,
        session: AsyncSession,
        identity_id: uuid.UUID,
    ) -> float:
        """Calculate overall confidence score for an identity"""
        result = await session.execute(
            select(
                func.avg(IdentitySource.confidence_score),
                func.count(IdentitySource.id),
            )
            .where(
                and_(
                    IdentitySource.identity_id == identity_id,
                    IdentitySource.status == PlatformStatus.FOUND.value,
                )
            )
        )
        avg_confidence, count = result.one()
        
        # Weight by number of verified sources
        if count == 0:
            return 0.0
        
        # Base confidence from sources
        base_confidence = float(avg_confidence or 0.0)
        
        # Boost based on number of sources
        source_multiplier = min(count / 10.0, 1.5)  # Max 1.5x boost for 10+ sources
        
        # Calculate final confidence (0-1)
        final_confidence = min(base_confidence * source_multiplier, 1.0)
        
        return final_confidence

    def _confidence_to_score(self, confidence: str) -> float:
        """Convert confidence level to numeric score (0-1)"""
        mapping = {
            ConfidenceLevel.HIGH.value: 1.0,
            ConfidenceLevel.MEDIUM.value: 0.6,
            ConfidenceLevel.LOW.value: 0.3,
            ConfidenceLevel.NONE.value: 0.0,
        }
        return mapping.get(confidence, 0.5)

    async def get_identity_by_username(self, username: str) -> Optional[Dict]:
        """
        Get complete identity information for a username.
        
        Args:
            username: Username to look up
            
        Returns:
            Dictionary with identity information, sources, and attributes
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(Identity)
                .where(Identity.primary_username == username.lower())
                .options(
                    selectinload(Identity.sources),
                    selectinload(Identity.attributes),
                    selectinload(Identity.relationships),
                )
            )
            identity = result.scalar_one_or_none()
            
            if not identity:
                return None
            
            return self._identity_to_dict(identity)

    async def search_by_attribute(
        self,
        attribute_type: str,
        attribute_value: str,
    ) -> List[Dict]:
        """
        Search for identities by attribute type and value.
        
        Args:
            attribute_type: Type of attribute (username, email, phone)
            attribute_value: Value to search for
            
        Returns:
            List of matching identities
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(Identity)
                .join(IdentityAttribute)
                .where(
                    and_(
                        IdentityAttribute.attribute_type == attribute_type,
                        IdentityAttribute.attribute_value == attribute_value.lower(),
                    )
                )
                .options(
                    selectinload(Identity.sources),
                    selectinload(Identity.attributes),
                )
            )
            identities = result.scalars().all()
            
            return [self._identity_to_dict(i) for i in identities]

    def _identity_to_dict(self, identity: Identity) -> Dict:
        """Convert Identity object to dictionary"""
        return {
            "id": str(identity.id),
            "primary_username": identity.primary_username,
            "primary_email": identity.primary_email,
            "primary_phone": identity.primary_phone,
            "confidence_score": identity.confidence_score,
            "last_verified": identity.last_verified.isoformat() if identity.last_verified else None,
            "verification_count": identity.verification_count,
            "created_at": identity.created_at.isoformat(),
            "updated_at": identity.updated_at.isoformat(),
            "attributes": [
                {
                    "type": attr.attribute_type,
                    "value": attr.attribute_value,
                    "is_primary": attr.is_primary,
                    "is_verified": attr.is_verified,
                    "confidence": attr.confidence,
                    "discovered_at": attr.discovered_at.isoformat(),
                    "discovered_from": attr.discovered_from,
                }
                for attr in identity.attributes
            ],
            "sources": [
                {
                    "platform": source.platform,
                    "platform_category": source.platform_category,
                    "profile_url": source.profile_url,
                    "username_found": source.username_found,
                    "status": source.status,
                    "confidence": source.confidence,
                    "confidence_score": source.confidence_score,
                    "http_status": source.http_status,
                    "response_time": source.response_time,
                    "last_checked": source.last_checked.isoformat(),
                    "reliability_rating": source.reliability_rating,
                    "profile_data": source.profile_data,
                }
                for source in identity.sources
            ],
        }

    async def cache_search_results(
        self,
        search_key: str,
        search_type: str,
        results: List[Dict],
        platform_count: int,
        duration: float,
        ttl_hours: int = 24,
    ):
        """
        Cache search results for future lookups.
        
        Args:
            search_key: Unique key for the search (e.g., "username:john_doe")
            search_type: Type of search
            results: Results to cache
            platform_count: Number of platforms checked
            duration: Time taken for search
            ttl_hours: Time to live for cache entry
        """
        async with self.get_session() as session:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            cache_entry = SearchCache(
                search_key=search_key,
                search_type=search_type,
                results=results,
                platform_count=platform_count,
                matches_found=len([r for r in results if r.get("status") == PlatformStatus.FOUND.value]),
                search_duration=duration,
                expires_at=expires_at,
            )
            
            await session.merge(cache_entry)  # Use merge to handle duplicates
            await session.commit()
            
            logger.debug(f"Cached search results for {search_key}")

    async def get_cached_results(self, search_key: str) -> Optional[List[Dict]]:
        """
        Get cached search results if available and not expired.
        
        Args:
            search_key: Unique key for the search
            
        Returns:
            Cached results or None
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(SearchCache)
                .where(
                    and_(
                        SearchCache.search_key == search_key,
                        SearchCache.expires_at > datetime.utcnow(),
                    )
                )
            )
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                # Increment hit count
                cache_entry.hit_count += 1
                await session.commit()
                
                logger.debug(f"Cache hit for {search_key}")
                return cache_entry.results
            
            return None

    async def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about platform checks and success rates.
        
        Returns:
            Dictionary with platform statistics
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(
                    IdentitySource.platform,
                    func.count(IdentitySource.id).label('total_checks'),
                    func.sum(
                        func.case(
                            (IdentitySource.status == PlatformStatus.FOUND.value, 1),
                            else_=0
                        )
                    ).label('found_count'),
                    func.avg(IdentitySource.response_time).label('avg_response_time'),
                    func.count(
                        func.case(
                            (IdentitySource.status == PlatformStatus.BLOCKED.value, 1),
                            else_=0
                        )
                    ).label('blocked_count'),
                )
                .group_by(IdentitySource.platform)
                .order_by(func.count(IdentitySource.id).desc())
            )
            
            stats = {}
            for row in result:
                stats[row.platform] = {
                    "total_checks": row.total_checks,
                    "found_count": row.found_count or 0,
                    "success_rate": (row.found_count / row.total_checks * 100) if row.total_checks > 0 else 0,
                    "avg_response_time": float(row.avg_response_time or 0),
                    "blocked_count": row.blocked_count or 0,
                }
            
            return stats


from datetime import timedelta
