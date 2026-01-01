from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgresql import Base
import enum


class IdentityType(str, enum.Enum):
    """Types of identities"""
    PERSON = "person"
    ORGANIZATION = "organization"
    USERNAME = "username"
    EMAIL = "email"
    PHONE = "phone"
    DOMAIN = "domain"
    UNKNOWN = "unknown"


class AttributeType(str, enum.Enum):
    """Types of attributes"""
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    USERNAME = "username"
    SOCIAL_MEDIA = "social_media"
    WEBSITE = "website"
    BIO = "bio"
    LOCATION = "location"
    OCCUPATION = "occupation"
    EDUCATION = "education"
    PHOTO = "photo"
    OTHER = "other"


class RelationshipType(str, enum.Enum):
    """Types of relationships"""
    LINKED_TO = "linked_to"
    MENTIONED_IN = "mentioned_in"
    REGISTERED_ON = "registered_on"
    CONNECTED_VIA = "connected_via"
    POSTED_ON = "posted_on"
    ASSOCIATED_WITH = "associated_with"
    EMPLOYED_BY = "employed_by"
    LOCATED_AT = "located_at"
    OWNS = "owns"
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"


class ContentType(str, enum.Enum):
    """Types of content"""
    SOCIAL_POST = "social_post"
    PROFILE = "profile"
    ARTICLE = "article"
    COMMENT = "comment"
    REVIEW = "review"
    ADULT_PROFILE = "adult_profile"
    ADULT_CONTENT = "adult_content"
    PERSONALS_AD = "personals_ad"
    CLASSIFIED_AD = "classified_ad"
    FORUM_POST = "forum_post"
    OTHER = "other"


class Identity(Base):
    """Main identity table - represents entities (people, usernames, etc.)"""
    __tablename__ = "identities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    type = Column(SQLEnum(IdentityType), nullable=False, default=IdentityType.UNKNOWN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    attributes = relationship("Attribute", back_populates="identity", cascade="all, delete-orphan")
    content = relationship("Content", back_populates="identity", cascade="all, delete-orphan")
    relationships_from = relationship(
        "Relationship",
        foreign_keys="Relationship.identity_1_id",
        back_populates="identity_1",
        cascade="all, delete-orphan"
    )
    relationships_to = relationship(
        "Relationship",
        foreign_keys="Relationship.identity_2_id",
        back_populates="identity_2",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_identity_name_type', 'name', 'type'),
    )


class Attribute(Base):
    """Attributes associated with identities"""
    __tablename__ = "attributes"
    
    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    attribute_type = Column(SQLEnum(AttributeType), nullable=False)
    value = Column(Text, nullable=False)
    source = Column(String(500))
    confidence_score = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    identity = relationship("Identity", back_populates="attributes")
    
    __table_args__ = (
        Index('idx_attribute_identity', 'identity_id'),
        Index('idx_attribute_type_value', 'attribute_type', 'value'),
    )


class Source(Base):
    """Data sources for OSINT collection"""
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(255), unique=True, nullable=False)
    url = Column(String(1000))
    source_type = Column(String(100))
    last_scraped = Column(DateTime(timezone=True))
    reliability_rating = Column(Float, default=0.5)
    is_active = Column(Integer, default=1)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_source_name', 'source_name'),
    )


class Relationship(Base):
    """Relationships between identities"""
    __tablename__ = "relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    identity_1_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    identity_2_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    relationship_type = Column(SQLEnum(RelationshipType), nullable=False)
    strength = Column(Float, default=0.5)
    evidence = Column(Text)
    source = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    identity_1 = relationship("Identity", foreign_keys=[identity_1_id], back_populates="relationships_from")
    identity_2 = relationship("Identity", foreign_keys=[identity_2_id], back_populates="relationships_to")
    
    __table_args__ = (
        Index('idx_relationship_identities', 'identity_1_id', 'identity_2_id'),
    )


class Content(Base):
    """Content associated with identities (posts, profiles, ads, etc.)"""
    __tablename__ = "content"
    
    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, ForeignKey("identities.id"), nullable=False)
    source = Column(String(500), nullable=False)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    text = Column(Text)
    media_urls = Column(Text)
    posted_date = Column(DateTime(timezone=True))
    scraped_date = Column(DateTime(timezone=True), server_default=func.now())
    url = Column(String(1000))
    metadata = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    identity = relationship("Identity", back_populates="content")
    
    __table_args__ = (
        Index('idx_content_identity', 'identity_id'),
        Index('idx_content_type_source', 'content_type', 'source'),
        Index('idx_content_posted_date', 'posted_date'),
    )
