import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Optional
import asyncpg
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Database Setup
POSTGRES_URI = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

# Create async engine
async_engine = create_async_engine(POSTGRES_URI, echo=False, pool_size=20, max_overflow=10)

# Create sync engine for migrations
sync_engine = create_engine(POSTGRES_URI.replace('+asyncpg', ''), echo=False)

# Session makers
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

Base = declarative_base()

# Neo4j Setup
neo4j_uri = os.getenv('NEO4J_URI')
neo4j_user = os.getenv('NEO4J_USER')
neo4j_password = os.getenv('NEO4J_PASSWORD')

neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

class Identity(Base):
    """Core identity table"""
    __tablename__ = 'identities'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20), index=True)
    username = Column(String(100), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    confidence_score = Column(Float, default=0.0)
    source = Column(String(100))
    metadata = Column(JSON)

class AdultProfile(Base):
    """Adult platform profiles"""
    __tablename__ = 'adult_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, index=True)
    platform = Column(String(50), index=True)
    username = Column(String(100), index=True)
    profile_url = Column(String(500))
    bio = Column(Text)
    join_date = Column(DateTime)
    profile_image_url = Column(String(500))
    linked_accounts = Column(JSON)
    confidence_score = Column(Float)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)

class PersonalsPost(Base):
    """Personals/classified posts"""
    __tablename__ = 'personals_posts'
    
    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, index=True)
    site = Column(String(50), index=True)
    post_id = Column(String(100), index=True)
    post_title = Column(String(255))
    post_content = Column(Text)
    phone_number = Column(String(20), index=True)
    email = Column(String(255), index=True)
    location = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    post_date = Column(DateTime)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float)
    image_urls = Column(JSON)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)

class Content(Base):
    """General content table"""
    __tablename__ = 'content'
    
    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, index=True)
    source_site = Column(String(100), index=True)
    post_id = Column(String(100), index=True)
    contact_info = Column(JSON)
    location_data = Column(JSON)
    post_content = Column(Text)
    image_urls = Column(JSON)
    posted_date = Column(DateTime)
    scraped_date = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)

class Attribute(Base):
    """Attributes associated with identities"""
    __tablename__ = 'attributes'
    
    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, index=True)
    attribute_type = Column(String(50), index=True)
    attribute_value = Column(String(255))
    source = Column(String(100))
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Source(Base):
    """Data sources"""
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    url = Column(String(500))
    source_type = Column(String(50))
    last_scraped = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=sync_engine)

async def init_async_db():
    """Initialize async database"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Neo4j Graph Operations
class Neo4jGraph:
    def __init__(self):
        self.driver = neo4j_driver
    
    def close(self):
        self.driver.close()
    
    def create_adult_profile_node(self, session, profile_data):
        """Create adult profile node in Neo4j"""
        query = """
        MERGE (p:AdultProfile {platform: $platform, username: $username})
        SET p.profile_url = $profile_url,
            p.bio = $bio,
            p.join_date = $join_date,
            p.profile_image_url = $profile_image_url,
            p.confidence_score = $confidence_score,
            p.scraped_at = $scraped_at
        """
        session.run(query, **profile_data)
    
    def create_personals_post_node(self, session, post_data):
        """Create personals post node in Neo4j"""
        query = """
        MERGE (p:PersonalsPost {site: $site, post_id: $post_id})
        SET p.post_title = $post_title,
            p.post_content = $post_content,
            p.phone_number = $phone_number,
            p.email = $email,
            p.location = $location,
            p.post_date = $post_date,
            p.confidence_score = $confidence_score,
            p.scraped_at = $scraped_at
        """
        session.run(query, **post_data)
    
    def create_identity_node(self, session, identity_data):
        """Create identity node in Neo4j"""
        query = """
        MERGE (i:Identity {id: $id})
        SET i.name = $name,
            i.email = $email,
            i.phone = $phone,
            i.username = $username,
            i.confidence_score = $confidence_score
        """
        session.run(query, **identity_data)
    
    def create_relationship(self, session, from_node, to_node, relationship_type, properties=None):
        """Create relationship between nodes"""
        if properties is None:
            properties = {}
        
        query = f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        MERGE (a)-[r:{relationship_type}]->(b)
        SET r += $properties
        """
        session.run(query, from_id=from_node['id'], to_id=to_node['id'], properties=properties)
