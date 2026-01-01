"""Tests for rate limiting functionality"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from backend.utils.rate_limiter import (
    RateLimiter,
    InMemoryRateLimiter,
    RedisRateLimiter,
    get_rate_limiter
)


@pytest.fixture
def rate_limit_config():
    """Test rate limiting configuration"""
    return {
        'default': {
            'requests_per_minute': 10,
            'requests_per_hour': 100,
            'burst_size': 5,
            'block_duration': 300
        },
        'search': {
            'requests_per_minute': 5,
            'requests_per_hour': 50,
            'burst_size': 3,
            'block_duration': 300
        }
    }


@pytest.mark.asyncio
class TestInMemoryRateLimiter:
    """Tests for in-memory rate limiter"""
    
    async def test_initialization(self, rate_limit_config):
        """Test rate limiter initialization"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        assert limiter.config == rate_limit_config
    
    async def test_check_rate_limit_within_limits(self, rate_limit_config):
        """Test rate check when within limits"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        # Mock request
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # First request should succeed
        is_allowed, limit_info = await limiter.check_rate_limit(request, "/api/search/username")
        
        assert is_allowed is True
        assert 'X-RateLimit-Limit-Minute' in limit_info
        assert 'X-RateLimit-Remaining-Minute' in limit_info
    
    async def test_check_rate_limit_exceeded(self, rate_limit_config):
        """Test rate check when limits are exceeded"""
        # Set very low limits for testing
        test_config = {
            'default': {
                'requests_per_minute': 2,
                'requests_per_hour': 10,
                'burst_size': 1,
                'block_duration': 60
            }
        }
        
        limiter = InMemoryRateLimiter(test_config)
        await limiter.initialize()
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Make requests until limit is exceeded
        for _ in range(3):
            is_allowed, limit_info = await limiter.check_rate_limit(request, "/api/test")
        
        # Third request should be blocked
        assert is_allowed is False
        assert 'Retry-After' in limit_info
    
    async def test_endpoint_specific_limits(self, rate_limit_config):
        """Test that endpoint-specific limits are applied"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Test default endpoint
        is_allowed, _ = await limiter.check_rate_limit(request, "/api/test")
        assert is_allowed is True
        
        # Test search endpoint (lower limits)
        is_allowed, info = await limiter.check_rate_limit(request, "/api/search/username")
        assert is_allowed is True
        # Search endpoint should have lower remaining count
        assert info['X-RateLimit-Limit-Minute'] == "5"  # From search config
    
    async def test_different_ips_separate_limits(self, rate_limit_config):
        """Test that different IPs have separate rate limits"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        request1 = Mock()
        request1.client = Mock()
        request1.client.host = "192.168.1.1"
        
        request2 = Mock()
        request2.client = Mock()
        request2.client.host = "192.168.1.2"
        
        # Both requests should be allowed
        is_allowed1, _ = await limiter.check_rate_limit(request1, "/api/test")
        is_allowed2, _ = await limiter.check_rate_limit(request2, "/api/test")
        
        assert is_allowed1 is True
        assert is_allowed2 is True
    
    async def test_burst_handling(self, rate_limit_config):
        """Test burst size handling"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Make burst-sized requests rapidly
        burst_size = rate_limit_config['default']['burst_size']
        for _ in range(burst_size):
            is_allowed, _ = await limiter.check_rate_limit(request, "/api/test")
            assert is_allowed is True
    
    async def test_hourly_limit_reset(self, rate_limit_config):
        """Test that hourly limits reset after an hour"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Simulate time passing
        with patch('backend.utils.rate_limiter.datetime') as mock_datetime:
            # Set time to now
            mock_datetime.utcnow.return_value = datetime.utcnow()
            
            # Make requests up to limit
            for _ in range(rate_limit_config['default']['requests_per_minute']):
                await limiter.check_rate_limit(request, "/api/test")
            
            # Advance time by 1 hour
            mock_datetime.utcnow.return_value = datetime.utcnow() + timedelta(hours=1)
            
            # Request should be allowed again
            is_allowed, _ = await limiter.check_rate_limit(request, "/api/test")
            assert is_allowed is True


@pytest.mark.asyncio
class TestRedisRateLimiter:
    """Tests for Redis-based rate limiter"""
    
    async def test_initialization(self):
        """Test Redis rate limiter initialization"""
        config = {
            'default': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
                'burst_size': 5,
                'block_duration': 300
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            }
        }
        
        with patch('redis.asyncio.from_url') as mock_redis:
            limiter = RedisRateLimiter(config)
            await limiter.initialize()
            
            assert limiter.client is not None
    
    async def test_check_rate_limit_redis(self):
        """Test rate check with Redis backend"""
        config = {
            'default': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
                'burst_size': 5,
                'block_duration': 300
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            }
        }
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            limiter = RedisRateLimiter(config)
            await limiter.initialize()
            
            request = Mock()
            request.client = Mock()
            request.client.host = "127.0.0.1"
            
            is_allowed, limit_info = await limiter.check_rate_limit(request, "/api/test")
            
            assert is_allowed is True
            mock_client.incr.assert_called()


class TestRateLimiterFactory:
    """Tests for rate limiter factory"""
    
    def test_get_in_memory_rate_limiter(self):
        """Test getting in-memory rate limiter"""
        limiter = get_rate_limiter(use_redis=False)
        
        assert isinstance(limiter, InMemoryRateLimiter)
    
    def test_get_redis_rate_limiter(self):
        """Test getting Redis rate limiter"""
        limiter = get_rate_limiter(use_redis=True)
        
        assert isinstance(limiter, RedisRateLimiter)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns same instance"""
        limiter1 = get_rate_limiter(use_redis=False)
        limiter2 = get_rate_limiter(use_redis=False)
        
        assert limiter1 is limiter2


class TestRateLimitIntegration:
    """Integration tests for rate limiting"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limit_config):
        """Test rate limiting with concurrent requests"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Make concurrent requests
        tasks = [
            limiter.check_rate_limit(request, "/api/test")
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All requests should be allowed
        allowed_count = sum(1 for is_allowed, _ in results if is_allowed)
        assert allowed_count == 5
    
    @pytest.mark.asyncio
    async def test_different_endpoints_independent_limits(self, rate_limit_config):
        """Test that different endpoints have independent limits"""
        limiter = InMemoryRateLimiter(rate_limit_config)
        await limiter.initialize()
        
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Exhaust limit for endpoint1
        for _ in range(10):
            await limiter.check_rate_limit(request, "/api/endpoint1")
        
        # endpoint2 should still be allowed
        is_allowed, _ = await limiter.check_rate_limit(request, "/api/endpoint2")
        assert is_allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
