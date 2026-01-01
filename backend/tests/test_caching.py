"""Tests for caching functionality"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from backend.utils.cache import (
    CacheManager,
    InMemoryCache,
    RedisCache,
    get_cache_manager
)


@pytest.fixture
def cache_config():
    """Test cache configuration"""
    return {
        'enabled': True,
        'use_redis': False,
        'default_ttl': 3600,
        'key_prefix': 'test:'
    }


@pytest.mark.asyncio
class TestInMemoryCache:
    """Tests for in-memory cache"""
    
    async def test_initialization(self, cache_config):
        """Test cache initialization"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        assert cache.config == cache_config
        assert cache._cache == {}
    
    async def test_set_and_get(self, cache_config):
        """Test setting and getting cache values"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        await cache.set("test_key", {"data": "test_value"}, ttl=60)
        
        result = await cache.get("test_key")
        assert result is not None
        assert result["data"] == "test_value"
    
    async def test_get_nonexistent_key(self, cache_config):
        """Test getting non-existent key"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        result = await cache.get("nonexistent_key")
        assert result is None
    
    async def test_ttl_expiration(self, cache_config):
        """Test that cached values expire after TTL"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        # Set with very short TTL
        await cache.set("expiring_key", {"data": "test"}, ttl=1)
        
        # Should exist immediately
        result = await cache.get("expiring_key")
        assert result is not None
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await cache.get("expiring_key")
        assert result is None
    
    async def test_delete(self, cache_config):
        """Test deleting cached values"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        await cache.set("delete_key", {"data": "test"})
        await cache.delete("delete_key")
        
        result = await cache.get("delete_key")
        assert result is None
    
    async def test_clear(self, cache_config):
        """Test clearing all cached values"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        await cache.set("key1", {"data": "test1"})
        await cache.set("key2", {"data": "test2"})
        
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    async def test_set_with_default_ttl(self, cache_config):
        """Test setting value with default TTL from config"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        await cache.set("default_ttl_key", {"data": "test"})
        
        result = await cache.get("default_ttl_key")
        assert result is not None
    
    async def test_set_json_serializable(self, cache_config):
        """Test caching JSON-serializable data"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        complex_data = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        await cache.set("complex_key", complex_data)
        result = await cache.get("complex_key")
        
        assert result == complex_data


@pytest.mark.asyncio
class TestRedisCache:
    """Tests for Redis-based cache"""
    
    async def test_initialization(self):
        """Test Redis cache initialization"""
        config = {
            'enabled': True,
            'use_redis': True,
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'default_ttl': 3600
        }
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache = RedisCache(config)
            await cache.initialize()
            
            assert cache.client is not None
    
    async def test_set_and_get_redis(self):
        """Test setting and getting values in Redis"""
        config = {
            'enabled': True,
            'use_redis': True,
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'default_ttl': 3600
        }
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_client.get.return_value = b'{"data": "test"}'
            mock_redis.return_value = mock_client
            
            cache = RedisCache(config)
            await cache.initialize()
            
            await cache.set("test_key", {"data": "test"}, ttl=60)
            result = await cache.get("test_key")
            
            mock_client.setex.assert_called()
            mock_client.get.assert_called()
            assert result is not None
    
    async def test_delete_redis(self):
        """Test deleting from Redis"""
        config = {
            'enabled': True,
            'use_redis': True,
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0
        }
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache = RedisCache(config)
            await cache.initialize()
            
            await cache.delete("test_key")
            
            mock_client.delete.assert_called_once()


@pytest.mark.asyncio
class TestCacheManager:
    """Tests for cache manager"""
    
    async def test_initialization(self, cache_config):
        """Test cache manager initialization"""
        manager = CacheManager(cache_config)
        await manager.initialize()
        
        assert manager.cache is not None
    
    async def test_get_cache_key_for_search(self, cache_config):
        """Test generating cache key for search"""
        manager = CacheManager(cache_config)
        await manager.initialize()
        
        key = manager.get_cache_key_for_search(
            'username_search',
            username='johndoe',
            email='john@example.com',
            phone='+1234567890'
        )
        
        assert 'username_search' in key
        assert 'johndoe' in key
    
    async def test_get_and_set(self, cache_config):
        """Test cache manager get and set"""
        manager = CacheManager(cache_config)
        await manager.initialize()
        
        await manager.set("manager_key", {"data": "test"}, ttl=60)
        result = await manager.get("manager_key")
        
        assert result is not None
        assert result["data"] == "test"
    
    async def test_cache_disabled(self):
        """Test that cache manager respects disabled flag"""
        config = {
            'enabled': False,
            'use_redis': False
        }
        
        manager = CacheManager(config)
        await manager.initialize()
        
        await manager.set("disabled_key", {"data": "test"})
        result = await manager.get("disabled_key")
        
        # When disabled, should return None
        assert result is None


class TestCacheFactory:
    """Tests for cache manager factory"""
    
    def test_get_in_memory_cache(self):
        """Test getting in-memory cache"""
        config = {
            'enabled': True,
            'use_redis': False,
            'default_ttl': 3600
        }
        
        manager = CacheManager(config)
        assert isinstance(manager._cache_impl, InMemoryCache)
    
    def test_get_redis_cache(self):
        """Test getting Redis cache"""
        config = {
            'enabled': True,
            'use_redis': True,
            'default_ttl': 3600
        }
        
        manager = CacheManager(config)
        assert isinstance(manager._cache_impl, RedisCache)


class TestCacheIntegration:
    """Integration tests for caching"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate(self, cache_config):
        """Test cache hit rate tracking"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        # Set value
        await cache.set("test_key", {"data": "test"})
        
        # Hit
        await cache.get("test_key")
        
        # Miss
        await cache.get("nonexistent_key")
        
        # Check stats (if implemented)
        if hasattr(cache, 'get_stats'):
            stats = cache.get_stats()
            assert 'hits' in stats
            assert 'misses' in stats
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, cache_config):
        """Test concurrent access to cache"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        # Set value
        await cache.set("concurrent_key", {"data": "test"})
        
        # Concurrent reads
        tasks = [cache.get("concurrent_key") for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result is not None for result in results)
    
    @pytest.mark.asyncio
    async def test_cache_namespace_isolation(self, cache_config):
        """Test that different cache keys don't interfere"""
        cache = InMemoryCache(cache_config)
        await cache.initialize()
        
        await cache.set("namespace1:key1", {"data": "value1"})
        await cache.set("namespace2:key1", {"data": "value2"})
        
        result1 = await cache.get("namespace1:key1")
        result2 = await cache.get("namespace2:key1")
        
        assert result1["data"] == "value1"
        assert result2["data"] == "value2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
