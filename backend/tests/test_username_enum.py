"""
Unit tests for Username Enumeration Module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.modules.username_enum import (
    UsernameEnumerator,
    UsernameMatch,
    ConfidenceLevel,
    PlatformStatus,
    UserAgentRotator,
)


class TestUserAgentRotator:
    """Tests for UserAgentRotator"""
    
    def test_get_random_returns_string(self):
        """Test that get_random returns a valid user agent string"""
        ua = UserAgentRotator.get_random()
        assert isinstance(ua, str)
        assert len(ua) > 0
        assert "Mozilla" in ua
    
    def test_get_random_uses_pool(self):
        """Test that user agents are drawn from the pool"""
        ua1 = UserAgentRotator.get_random()
        ua2 = UserAgentRotator.get_random()
        # Should be from the pool
        assert ua1 in UserAgentRotator.USER_AGENTS
        assert ua2 in UserAgentRotator.USER_AGENTS


class TestUsernameEnumerator:
    """Tests for UsernameEnumerator"""
    
    @pytest.fixture
    async def enumerator(self):
        """Fixture for UsernameEnumerator instance"""
        enum = UsernameEnumerator(
            max_concurrent=10,
            timeout=5.0,
            enable_cache=False,  # Disable cache for tests
        )
        await enum.start()
        yield enum
        await enum.close()
    
    @pytest.mark.asyncio
    async def test_initialization(self, enumerator):
        """Test enumerator initialization"""
        assert enumerator.max_concurrent == 10
        assert enumerator.timeout == 5.0
        assert enumerator.session is not None
        assert len(enumerator.platforms) > 0
    
    @pytest.mark.asyncio
    async def test_empty_username_raises_error(self, enumerator):
        """Test that empty username raises ValueError"""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            await enumerator.search("")
    
    @pytest.mark.asyncio
    async def test_search_uses_cache(self, enumerator):
        """Test that search uses cache when enabled"""
        enumerator.enable_cache = True
        username = "test_user"
        
        # Mock the actual search to avoid real HTTP requests
        with patch.object(enumerator, '_check_platform') as mock_check:
            mock_check.return_value = {
                "platform": "test_platform",
                "username": username,
                "url": "https://example.com",
                "status": PlatformStatus.FOUND,
                "confidence": ConfidenceLevel.HIGH,
                "is_variant": False,
            }
            
            # First search
            await enumerator.search(username)
            
            # Second search should use cache
            await enumerator.search(username)
            
            # Should only be called once due to caching
            assert mock_check.call_count == len(enumerator.platforms)
    
    @pytest.mark.asyncio
    async def test_check_platform_status_code_found(self, enumerator):
        """Test checking platform with status code method - found"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "status_code",
            "found_status": [200],
            "not_found_status": [404],
            "timeout": 5,
        }
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.FOUND
        assert result["confidence"] == ConfidenceLevel.HIGH
        assert result["response_code"] == 200
    
    @pytest.mark.asyncio
    async def test_check_platform_status_code_not_found(self, enumerator):
        """Test checking platform with status code method - not found"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "status_code",
            "found_status": [200],
            "not_found_status": [404],
            "timeout": 5,
        }
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.NOT_FOUND
        assert result["confidence"] == ConfidenceLevel.NONE
        assert result["response_code"] == 404
    
    @pytest.mark.asyncio
    async def test_check_platform_html_content_found(self, enumerator):
        """Test checking platform with HTML content method - found"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "html_content",
            "found_patterns": ["followers", "posts"],
            "not_found_patterns": ["not found", "error"],
            "timeout": 5,
        }
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html>This user has 100 followers and 50 posts</html>")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.FOUND
        assert result["confidence"] == ConfidenceLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_check_platform_html_content_not_found(self, enumerator):
        """Test checking platform with HTML content method - not found"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "html_content",
            "found_patterns": ["followers", "posts"],
            "not_found_patterns": ["not found", "error"],
            "timeout": 5,
        }
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="<html>User not found</html>")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.NOT_FOUND
        assert result["confidence"] == ConfidenceLevel.NONE
    
    @pytest.mark.asyncio
    async def test_check_platform_timeout(self, enumerator):
        """Test platform check with timeout"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "status_code",
            "timeout": 0.001,  # Very short timeout
        }
        
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.TIMEOUT
        assert "timeout" in result["error_message"].lower()
    
    @pytest.mark.asyncio
    async def test_check_platform_error(self, enumerator):
        """Test platform check with generic error"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "status_code",
            "timeout": 5,
        }
        
        with patch('aiohttp.ClientSession.get', side_effect=Exception("Network error")):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.ERROR
        assert result["error_message"] is not None
    
    @pytest.mark.asyncio
    async def test_check_platform_rate_limited(self, enumerator):
        """Test platform check with rate limiting"""
        platform_config = {
            "name": "TestPlatform",
            "url_template": "https://example.com/{username}",
            "method": "status_code",
            "timeout": 5,
        }
        
        # Mock 429 response
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value="")
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await enumerator._check_platform(platform_config, "test_user")
        
        assert result["status"] == PlatformStatus.BLOCKED
    
    @pytest.mark.asyncio
    async def test_search_with_fuzzy_matching(self, enumerator):
        """Test search with fuzzy matching enabled"""
        username = "john_smith"
        
        # Mock platform checks
        with patch.object(enumerator, '_check_platform') as mock_check:
            mock_check.return_value = {
                "platform": "test",
                "username": username,
                "url": "https://example.com",
                "status": PlatformStatus.FOUND,
                "confidence": ConfidenceLevel.HIGH,
                "is_variant": False,
            }
            
            results = await enumerator.search(username, fuzzy_match=True)
            
            # Should have checked multiple variations
            assert mock_check.call_count > len(enumerator.platforms)
    
    @pytest.mark.asyncio
    async def test_search_specific_platforms(self, enumerator):
        """Test searching only specific platforms"""
        username = "test_user"
        platforms = ["twitter", "github"]
        
        # Mock platform checks
        with patch.object(enumerator, '_check_platform') as mock_check:
            mock_check.return_value = {
                "platform": "test",
                "username": username,
                "url": "https://example.com",
                "status": PlatformStatus.FOUND,
                "confidence": ConfidenceLevel.HIGH,
                "is_variant": False,
            }
            
            results = await enumerator.search(username, platforms=platforms)
            
            # Should only check specified platforms
            assert mock_check.call_count == len(platforms)
    
    @pytest.mark.asyncio
    async def test_search_multiple_usernames(self, enumerator):
        """Test searching multiple usernames"""
        usernames = ["user1", "user2", "user3"]
        
        # Mock platform checks
        with patch.object(enumerator, '_check_platform') as mock_check:
            mock_check.return_value = {
                "platform": "test",
                "username": "test",
                "url": "https://example.com",
                "status": PlatformStatus.NOT_FOUND,
                "confidence": ConfidenceLevel.NONE,
                "is_variant": False,
            }
            
            results = await enumerator.search_multiple(usernames)
            
            # Should return results for all usernames
            assert len(results) == len(usernames)
            assert all(username in results for username in usernames)
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, enumerator):
        """Test cache clearing"""
        enumerator.enable_cache = True
        enumerator.cache["test_key"] = "test_value"
        
        enumerator.clear_cache()
        
        assert len(enumerator.cache) == 0
    
    def test_get_platform_stats(self, enumerator):
        """Test getting platform statistics"""
        stats = enumerator.get_platform_stats()
        
        assert "total_platforms" in stats
        assert "categories" in stats
        assert "max_concurrent" in stats
        assert "timeout" in stats
        assert stats["total_platforms"] > 0


class TestUsernameMatch:
    """Tests for UsernameMatch dataclass"""
    
    def test_username_match_creation(self):
        """Test creating a UsernameMatch"""
        match = UsernameMatch(
            username="test_user",
            platform="twitter",
            profile_url="https://twitter.com/test_user",
            confidence=ConfidenceLevel.HIGH,
            is_verified=True,
        )
        
        assert match.username == "test_user"
        assert match.platform == "twitter"
        assert match.confidence == ConfidenceLevel.HIGH
        assert match.is_verified is True
        assert match.discovery_method == "direct"
    
    def test_username_match_with_additional_info(self):
        """Test UsernameMatch with additional info"""
        additional_info = {
            "response_code": 200,
            "response_time": 1.5,
            "profile_data": {"followers": 100},
        }
        
        match = UsernameMatch(
            username="test_user",
            platform="github",
            profile_url="https://github.com/test_user",
            confidence=ConfidenceLevel.MEDIUM,
            additional_info=additional_info,
        )
        
        assert match.additional_info == additional_info


@pytest.mark.asyncio
async def test_enumerate_username_convenience_function():
    """Test the convenience function enumerate_username"""
    with patch('backend.modules.username_enum.UsernameEnumerator.search') as mock_search:
        mock_search.return_value = [
            UsernameMatch(
                username="test",
                platform="twitter",
                profile_url="https://twitter.com/test",
                confidence=ConfidenceLevel.HIGH,
            )
        ]
        
        matches = await enumerate_username("test_user", max_concurrent=20)
        
        assert len(matches) == 1
        assert matches[0].username == "test"
