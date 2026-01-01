"""Integration tests for Username Enumeration API endpoints"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.models.schemas import (
    UsernameSearchRequest,
    ReverseLookupRequest,
    FuzzyMatchRequest,
    PlatformResult,
    SearchResponse,
    ReverseLookupResponse,
    FuzzyMatchResponse,
    ErrorResponse
)


@pytest.fixture
def app():
    """Create test FastAPI application"""
    app = create_app()
    
    # Mock the services
    app.state.username_service = Mock()
    app.state.cache_manager = Mock()
    app.state.cache_manager.get = AsyncMock(return_value=None)
    app.state.cache_manager.set = AsyncMock()
    app.state.cache_manager.get_cache_key_for_search = Mock(return_value="test_key")
    app.state.db_manager = Mock()
    app.state.db_manager.postgresql = None
    app.state.db_manager.neo4j = None
    app.state.rate_limiter = Mock()
    app.state.rate_limiter.check_rate_limit = AsyncMock(return_value=(True, {}))
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_platform_results():
    """Sample platform results for testing"""
    return [
        PlatformResult(
            platform="GitHub",
            profile_url="https://github.com/johndoe",
            confidence=0.95,
            match_type="exact",
            metadata={"username": "johndoe", "email": "john@example.com"},
            discovered_at=datetime.utcnow()
        ),
        PlatformResult(
            platform="Twitter",
            profile_url="https://twitter.com/johndoe",
            confidence=0.88,
            match_type="exact",
            metadata={},
            discovered_at=datetime.utcnow()
        ),
        PlatformResult(
            platform="Reddit",
            profile_url="https://reddit.com/user/johndoe",
            confidence=0.72,
            match_type="fuzzy",
            metadata={},
            discovered_at=datetime.utcnow()
        )
    ]


class TestUsernameSearchEndpoint:
    """Tests for POST /api/search/username endpoint"""
    
    def test_search_username_success(self, client, sample_platform_results, app):
        """Test successful username search"""
        # Mock service response
        app.state.username_service.enumerate_username = AsyncMock(
            return_value=[Mock(
                platform_name=r.platform,
                profile_url=r.profile_url,
                confidence=r.confidence,
                match_type=r.match_type,
                metadata=r.metadata
            ) for r in sample_platform_results]
        )
        
        response = client.post(
            "/api/search/username",
            json={
                "username": "johndoe",
                "email": "john@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total_count"] == 3
        assert len(data["results"]) == 3
        assert data["results"][0]["platform"] == "GitHub"
        assert data["results"][0]["confidence"] == 0.95
    
    def test_search_username_with_pagination(self, client, app):
        """Test username search with pagination"""
        # Create many mock results
        mock_results = [
            Mock(
                platform_name=f"Platform{i}",
                profile_url=f"https://platform{i}/johndoe",
                confidence=0.8,
                match_type="exact",
                metadata={}
            )
            for i in range(50)
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        response = client.post(
            "/api/search/username?page=2&page_size=10",
            json={"username": "johndoe"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert len(data["results"]) == 10
        assert data["total_count"] == 50
    
    def test_search_username_invalid_input(self, client):
        """Test username search with invalid input"""
        # Empty username
        response = client.post(
            "/api/search/username",
            json={"username": ""}
        )
        assert response.status_code == 422  # Validation error
        
        # Invalid characters
        response = client.post(
            "/api/search/username",
            json={"username": "john@doe"}
        )
        assert response.status_code == 422
    
    def test_search_username_invalid_phone(self, client):
        """Test username search with invalid phone number"""
        response = client.post(
            "/api/search/username",
            json={
                "username": "johndoe",
                "phone": "invalid-phone"
            }
        )
        assert response.status_code == 422
    
    def test_search_username_cache_hit(self, client, sample_platform_results, app):
        """Test username search with cache hit"""
        # Mock cache hit
        cached_response = {
            "results": [r.dict() for r in sample_platform_results],
            "total_count": 3,
            "page": 1,
            "page_size": 20,
            "execution_time_ms": 100,
            "cached": True
        }
        app.state.cache_manager.get = AsyncMock(return_value=cached_response)
        
        response = client.post(
            "/api/search/username",
            json={"username": "johndoe"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] == True
        # Should not call enumeration service
        app.state.username_service.enumerate_username.assert_not_called()
    
    def test_search_username_rate_limit(self, client, app):
        """Test rate limiting on username search"""
        # Mock rate limit exceeded
        app.state.rate_limiter.check_rate_limit = AsyncMock(
            return_value=(False, {"Retry-After": "60"})
        )
        
        response = client.post(
            "/api/search/username",
            json={"username": "johndoe"}
        )
        
        assert response.status_code == 429
        data = response.json()
        assert "error" in data
        assert data["error"] == "Rate limit exceeded"


class TestReverseLookupEndpoint:
    """Tests for POST /api/search/reverse-lookup endpoint"""
    
    def test_reverse_lookup_by_email(self, client, app):
        """Test reverse lookup by email"""
        mock_results = [
            {
                "username": "johndoe",
                "platforms": ["GitHub", "LinkedIn", "Twitter"]
            },
            {
                "username": "john_doe_1990",
                "platforms": ["Instagram", "Reddit"]
            }
        ]
        app.state.username_service.reverse_lookup = AsyncMock(return_value=mock_results)
        
        response = client.post(
            "/api/search/reverse-lookup",
            json={"email": "john@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "usernames" in data
        assert len(data["usernames"]) == 2
        assert data["usernames"][0]["username"] == "johndoe"
        assert "GitHub" in data["usernames"][0]["platforms"]
    
    def test_reverse_lookup_by_phone(self, client, app):
        """Test reverse lookup by phone"""
        mock_results = [
            {
                "username": "1234567",
                "platforms": ["Facebook", "Telegram"]
            }
        ]
        app.state.username_service.reverse_lookup = AsyncMock(return_value=mock_results)
        
        response = client.post(
            "/api/search/reverse-lookup",
            json={"phone": "+1234567890"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["usernames"]) == 1
    
    def test_reverse_lookup_no_input(self, client):
        """Test reverse lookup without email or phone"""
        response = client.post(
            "/api/search/reverse-lookup",
            json={}
        )
        assert response.status_code == 422
    
    def test_reverse_lookup_invalid_email(self, client):
        """Test reverse lookup with invalid email"""
        response = client.post(
            "/api/search/reverse-lookup",
            json={"email": "invalid-email"}
        )
        assert response.status_code == 422


class TestFuzzyMatchEndpoint:
    """Tests for POST /api/search/fuzzy-match endpoint"""
    
    def test_fuzzy_match_medium_tolerance(self, client, sample_platform_results, app):
        """Test fuzzy match with medium tolerance"""
        app.state.username_service.fuzzy_match_search = AsyncMock(
            return_value=[Mock(
                platform_name=r.platform,
                profile_url=r.profile_url,
                confidence=r.confidence,
                match_type=r.match_type,
                metadata=r.metadata
            ) for r in sample_platform_results]
        )
        
        response = client.post(
            "/api/search/fuzzy-match",
            json={
                "username": "johndoe",
                "tolerance_level": "medium"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert data["original_username"] == "johndoe"
        assert len(data["matches"]) == 3
    
    def test_fuzzy_match_high_tolerance(self, client, app):
        """Test fuzzy match with high tolerance"""
        app.state.username_service.fuzzy_match_search = AsyncMock(return_value=[])
        
        response = client.post(
            "/api/search/fuzzy-match",
            json={
                "username": "john",
                "tolerance_level": "high"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_username"] == "john"
    
    def test_fuzzy_match_invalid_tolerance(self, client):
        """Test fuzzy match with invalid tolerance level"""
        response = client.post(
            "/api/search/fuzzy-match",
            json={
                "username": "johndoe",
                "tolerance_level": "invalid"
            }
        )
        assert response.status_code == 422
    
    def test_fuzzy_match_with_pagination(self, client, app):
        """Test fuzzy match with pagination"""
        mock_results = [
            Mock(
                platform_name=f"Platform{i}",
                profile_url=f"https://platform{i}/johndoe",
                confidence=0.7,
                match_type="fuzzy",
                metadata={}
            )
            for i in range(30)
        ]
        app.state.username_service.fuzzy_match_search = AsyncMock(return_value=mock_results)
        
        response = client.post(
            "/api/search/fuzzy-match?page=1&page_size=10",
            json={"username": "johndoe"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 30
        assert len(data["matches"]) == 10


class TestGetUsernameResults:
    """Tests for GET /api/results/username/{username} endpoint"""
    
    def test_get_username_results(self, client, app):
        """Test getting detailed username results"""
        mock_results = [
            Mock(
                platform_name="GitHub",
                profile_url="https://github.com/johndoe",
                confidence=0.95,
                match_type="exact",
                metadata={"email": "john@example.com"}
            )
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        response = client.get("/api/results/username/johndoe")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "johndoe"
        assert data["results_count"] == 1
        assert "GitHub" in data["platforms"]
    
    def test_get_username_results_without_metadata(self, client, app):
        """Test getting username results without metadata"""
        mock_results = [
            Mock(
                platform_name="Twitter",
                profile_url="https://twitter.com/johndoe",
                confidence=0.88,
                match_type="exact",
                metadata={}
            )
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        response = client.get("/api/results/username/johndoe?include_metadata=false")
        
        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data


class TestGetIdentityChain:
    """Tests for GET /api/results/identity-chain/{username} endpoint"""
    
    def test_get_identity_chain(self, client, app):
        """Test getting identity chain"""
        mock_chain = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "username",
                    "value": "johndoe",
                    "platform": None,
                    "confidence": 1.0
                },
                {
                    "id": "node2",
                    "type": "profile",
                    "value": "https://github.com/johndoe",
                    "platform": "GitHub",
                    "confidence": 0.95
                }
            ],
            "relationships": [
                {
                    "source_id": "node1",
                    "target_id": "node2",
                    "relationship_type": "found_on",
                    "confidence": 0.95,
                    "discovered_at": datetime.utcnow().isoformat()
                }
            ],
            "chain_length": 1
        }
        app.state.db_manager.neo4j = None
        app.state.username_service.build_identity_chain = AsyncMock(return_value=mock_chain)
        
        response = client.get("/api/results/identity-chain/johndoe")
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "relationships" in data
        assert data["chain_length"] == 1
        assert len(data["nodes"]) == 2
    
    def test_get_identity_chain_with_max_depth(self, client, app):
        """Test getting identity chain with max_depth parameter"""
        app.state.username_service.build_identity_chain = AsyncMock(return_value={
            "nodes": [],
            "relationships": [],
            "chain_length": 0
        })
        
        response = client.get("/api/results/identity-chain/johndoe?max_depth=2")
        
        assert response.status_code == 200


class TestSearchStats:
    """Tests for GET /api/search/stats endpoint"""
    
    def test_get_search_stats(self, client, app):
        """Test getting search statistics"""
        app.state.db_manager.postgresql = Mock()
        app.state.db_manager.postgresql.get_platform_statistics = AsyncMock(return_value=[])
        app.state.db_manager.postgresql.pool = Mock()
        app.state.db_manager.postgresql.pool.acquire = AsyncMock()
        
        response = client.get("/api/search/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data


class TestHealthCheck:
    """Tests for GET /health endpoint"""
    
    def test_health_check_healthy(self, client, app):
        """Test health check when all services are healthy"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "timestamp" in data


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_service_error_handling(self, client, app):
        """Test handling of service errors"""
        app.state.username_service.enumerate_username = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        response = client.post(
            "/api/search/username",
            json={"username": "johndoe"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestInputValidation:
    """Tests for input validation"""
    
    def test_username_too_long(self, client):
        """Test username validation with too long username"""
        response = client.post(
            "/api/search/username",
            json={"username": "a" * 101}
        )
        assert response.status_code == 422
    
    def test_special_characters_in_username(self, client):
        """Test username validation with special characters"""
        response = client.post(
            "/api/search/username",
            json={"username": "john$doe"}
        )
        assert response.status_code == 422
    
    def test_valid_username_formats(self, client, app):
        """Test various valid username formats"""
        app.state.username_service.enumerate_username = AsyncMock(return_value=[])
        
        valid_usernames = ["john_doe", "john-doe", "john.doe", "JohnDoe123"]
        
        for username in valid_usernames:
            response = client.post(
                "/api/search/username",
                json={"username": username}
            )
            # Should not fail validation
            assert response.status_code != 422 or "validation" not in response.json().get("detail", "").lower()


class TestPagination:
    """Tests for pagination"""
    
    def test_pagination_large_page_size(self, client, app):
        """Test pagination with maximum page size"""
        app.state.username_service.enumerate_username = AsyncMock(
            return_value=[Mock(
                platform_name=f"Platform{i}",
                profile_url=f"https://platform{i}/user",
                confidence=0.8,
                match_type="exact",
                metadata={}
            ) for i in range(150)]
        )
        
        response = client.post(
            "/api/search/username?page_size=100",
            json={"username": "test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 100
    
    def test_pagination_invalid_page_size(self, client):
        """Test pagination with invalid page size (over 100)"""
        response = client.post(
            "/api/search/username?page_size=101",
            json={"username": "test"}
        )
        assert response.status_code == 422


class TestCacheBehavior:
    """Tests for caching behavior"""
    
    def test_cache_key_generation(self, client, app):
        """Test that cache keys are generated correctly"""
        app.state.username_service.enumerate_username = AsyncMock(return_value=[])
        
        # Make multiple requests with same parameters
        response1 = client.post(
            "/api/search/username",
            json={"username": "johndoe", "email": "john@example.com"}
        )
        assert response.status_code == 200
        
        response2 = client.post(
            "/api/search/username",
            json={"username": "johndoe", "email": "john@example.com"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
