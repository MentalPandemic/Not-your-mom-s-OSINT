"""
Unit tests for Database Module
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.database import (
    DatabaseManager,
    Identity,
    IdentityAttribute,
    IdentitySource,
    SearchCache,
    ConfidenceLevel,
    PlatformStatus,
    Base,
)


@pytest.fixture
def db_manager():
    """Fixture for DatabaseManager with in-memory database"""
    # Use in-memory SQLite for testing
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    return manager


@pytest.mark.asyncio
async def test_database_initialization(db_manager):
    """Test database manager initialization"""
    await db_manager.initialize()
    
    assert db_manager.engine is not None
    assert db_manager.async_session_maker is not None
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_create_tables(db_manager):
    """Test creating database tables"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    # Check that tables exist by querying metadata
    from sqlalchemy import inspect
    async with db_manager.engine.begin() as conn:
        inspector = await conn.run_sync(inspect)
        tables = inspector.get_table_names()
        
        assert "identities" in tables
        assert "identity_attributes" in tables
        assert "identity_sources" in tables
        assert "search_cache" in tables
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_find_or_create_identity_new(db_manager):
    """Test creating a new identity"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    async with db_manager.get_session() as session:
        identity = await db_manager._find_or_create_identity(
            session,
            "test_user",
            "username",
        )
        
        assert identity.primary_username == "test_user"
        assert identity.id is not None
        assert len(identity.attributes) == 1
        assert identity.attributes[0].attribute_value == "test_user"
        assert identity.attributes[0].is_primary is True
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_find_or_create_identity_existing(db_manager):
    """Test finding existing identity"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    async with db_manager.get_session() as session:
        # Create initial identity
        identity1 = await db_manager._find_or_create_identity(
            session,
            "test_user",
            "username",
        )
        identity_id = identity1.id
        
        # Try to find same identity
        identity2 = await db_manager._find_or_create_identity(
            session,
            "test_user",
            "username",
        )
        
        # Should return same identity
        assert identity2.id == identity_id
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_store_search_results(db_manager):
    """Test storing search results"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    results = [
        {
            "platform": "twitter",
            "url": "https://twitter.com/test_user",
            "status": PlatformStatus.FOUND.value,
            "confidence": ConfidenceLevel.HIGH.value,
            "response_code": 200,
            "response_time": 1.5,
            "category": "social_media",
        },
        {
            "platform": "github",
            "url": "https://github.com/test_user",
            "status": PlatformStatus.FOUND.value,
            "confidence": ConfidenceLevel.HIGH.value,
            "response_code": 200,
            "response_time": 1.2,
            "category": "code",
        }
    ]
    
    identity = await db_manager.store_search_results(
        "test_user",
        "username",
        results,
        duration=2.0,
    )
    
    assert identity.primary_username == "test_user"
    assert identity.verification_count == 1
    assert len(identity.sources) == 2
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_get_identity_by_username(db_manager):
    """Test retrieving identity by username"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    # Store initial results
    results = [
        {
            "platform": "twitter",
            "url": "https://twitter.com/test_user",
            "status": PlatformStatus.FOUND.value,
            "confidence": ConfidenceLevel.HIGH.value,
            "category": "social_media",
        }
    ]
    
    await db_manager.store_search_results("test_user", "username", results)
    
    # Retrieve identity
    identity_dict = await db_manager.get_identity_by_username("test_user")
    
    assert identity_dict is not None
    assert identity_dict["primary_username"] == "test_user"
    assert len(identity_dict["sources"]) == 1
    assert identity_dict["sources"][0]["platform"] == "twitter"
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_get_identity_not_found(db_manager):
    """Test retrieving non-existent identity"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    identity = await db_manager.get_identity_by_username("nonexistent_user")
    
    assert identity is None
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_search_by_attribute(db_manager):
    """Test searching identities by attribute"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    # Store identity with email attribute
    results = [
        {
            "platform": "twitter",
            "url": "https://twitter.com/test_user",
            "status": PlatformStatus.FOUND.value,
            "confidence": ConfidenceLevel.HIGH.value,
        }
    ]
    
    await db_manager.store_search_results("test_user", "username", results)
    
    # Add email attribute
    async with db_manager.get_session() as session:
        from sqlalchemy import select
        identity = await session.execute(
            select(Identity).where(Identity.primary_username == "test_user")
        )
        identity = identity.scalar_one()
        
        email_attr = IdentityAttribute(
            identity_id=identity.id,
            attribute_type="email",
            attribute_value="test@example.com",
            is_verified=True,
        )
        session.add(email_attr)
        await session.commit()
    
    # Search by email
    identities = await db_manager.search_by_attribute("email", "test@example.com")
    
    assert len(identities) == 1
    assert identities[0]["primary_username"] == "test_user"
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_cache_search_results(db_manager):
    """Test caching search results"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    search_key = "username:test_user"
    results = [
        {"platform": "twitter", "url": "https://twitter.com/test_user"},
        {"platform": "github", "url": "https://github.com/test_user"},
    ]
    
    await db_manager.cache_search_results(
        search_key,
        "username",
        results,
        platform_count=100,
        duration=5.0,
        ttl_hours=24,
    )
    
    # Retrieve cached results
    cached = await db_manager.get_cached_results(search_key)
    
    assert cached is not None
    assert len(cached) == 2
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_get_cached_results_expired(db_manager):
    """Test retrieving expired cache entry"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    search_key = "username:test_user"
    results = [{"platform": "twitter"}]
    
    # Cache with short TTL
    await db_manager.cache_search_results(
        search_key,
        "username",
        results,
        platform_count=100,
        duration=1.0,
        ttl_hours=0,  # Expired immediately
    )
    
    # Try to retrieve - should return None
    cached = await db_manager.get_cached_results(search_key)
    
    assert cached is None
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_get_platform_statistics(db_manager):
    """Test getting platform statistics"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    # Store results for multiple platforms
    results = [
        {
            "platform": "twitter",
            "url": "https://twitter.com/test_user",
            "status": PlatformStatus.FOUND.value,
            "confidence": ConfidenceLevel.HIGH.value,
            "response_time": 1.5,
        },
        {
            "platform": "github",
            "url": "https://github.com/test_user",
            "status": PlatformStatus.NOT_FOUND.value,
            "confidence": ConfidenceLevel.NONE.value,
            "response_time": 1.2,
        }
    ]
    
    await db_manager.store_search_results("test_user", "username", results)
    
    # Get statistics
    stats = await db_manager.get_platform_statistics()
    
    assert "twitter" in stats
    assert "github" in stats
    assert stats["twitter"]["total_checks"] == 1
    assert stats["twitter"]["found_count"] == 1
    assert stats["github"]["found_count"] == 0
    
    await db_manager.close()


@pytest.mark.asyncio
async def test_calculate_identity_confidence(db_manager):
    """Test identity confidence calculation"""
    await db_manager.initialize()
    await db_manager.create_tables()
    
    async with db_manager.get_session() as session:
        # Create identity
        identity = await db_manager._find_or_create_identity(
            session,
            "test_user",
            "username",
        )
        
        # Add multiple high-confidence sources
        for i in range(5):
            source = IdentitySource(
                identity_id=identity.id,
                platform=f"platform_{i}",
                status=PlatformStatus.FOUND.value,
                confidence=ConfidenceLevel.HIGH.value,
                confidence_score=1.0,
            )
            session.add(source)
        
        await session.commit()
        identity_id = identity.id
    
    # Calculate confidence
    confidence = await db_manager._calculate_identity_confidence(None, identity_id)
    
    # Should have high confidence due to multiple sources
    assert confidence > 0.8
    
    await db_manager.close()
