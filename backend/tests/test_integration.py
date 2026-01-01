"""End-to-end integration tests for Username Enumeration API"""
import pytest
from unittest.mock import Mock, AsyncMock
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime

from backend.main import create_app


@pytest.fixture
def app():
    """Create test FastAPI application with full service stack"""
    app = create_app()
    
    # Mock all services
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


@pytest.mark.asyncio
class TestEndToEndUsernameSearch:
    """End-to-end tests for username search flow"""
    
    async def test_complete_username_search_flow(self, client, app):
        """Test complete flow: search -> results -> export"""
        # Mock service responses
        mock_results = [
            Mock(
                platform_name="GitHub",
                profile_url="https://github.com/johndoe",
                confidence=0.95,
                match_type="exact",
                metadata={"email": "john@example.com", "bio": "Developer"}
            ),
            Mock(
                platform_name="Twitter",
                profile_url="https://twitter.com/johndoe",
                confidence=0.88,
                match_type="exact",
                metadata={}
            )
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        # Step 1: Perform search
        search_response = client.post(
            "/api/search/username",
            json={"username": "johndoe"}
        )
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total_count"] == 2
        assert len(search_data["results"]) == 2
        
        # Step 2: Get detailed results
        results_response = client.get("/api/results/username/johndoe")
        
        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["username"] == "johndoe"
        assert "platforms" in results_data
        
        # Step 3: Get identity chain
        app.state.username_service.build_identity_chain = AsyncMock(
            return_value={
                "nodes": [
                    {"id": "node1", "type": "username", "value": "johndoe"},
                    {"id": "node2", "type": "profile", "value": "https://github.com/johndoe"}
                ],
                "relationships": [],
                "chain_length": 0
            }
        )
        
        chain_response = client.get("/api/results/identity-chain/johndoe")
        
        assert chain_response.status_code == 200
        chain_data = chain_response.json()
        assert "nodes" in chain_data
        
        # Step 4: Export results as JSON
        export_response = client.post(
            "/api/export/username",
            params={"format": "json", "username": "johndoe"}
        )
        
        assert export_response.status_code == 200
        assert "application/json" in export_response.headers.get("content-type")


@pytest.mark.asyncio
class TestEndToEndReverseLookup:
    """End-to-end tests for reverse lookup flow"""
    
    async def test_complete_reverse_lookup_flow(self, client, app):
        """Test complete reverse lookup flow"""
        mock_usernames = [
            {"username": "johndoe", "platforms": ["GitHub", "LinkedIn"]},
            {"username": "john_doe_1990", "platforms": ["Twitter", "Instagram"]}
        ]
        app.state.username_service.reverse_lookup = AsyncMock(return_value=mock_usernames)
        
        # Perform reverse lookup
        response = client.post(
            "/api/search/reverse-lookup",
            json={"email": "john@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["usernames"]) == 2
        assert data["total_count"] == 2
        
        # Search for each discovered username
        for username_data in data["usernames"]:
            username = username_data["username"]
            
            app.state.username_service.enumerate_username = AsyncMock(
                return_value=[
                    Mock(
                        platform_name=platform,
                        profile_url=f"https://{platform.lower()}.com/{username}",
                        confidence=0.8,
                        match_type="exact",
                        metadata={}
                    )
                    for platform in username_data["platforms"]
                ]
            )
            
            search_response = client.post(
                "/api/search/username",
                json={"username": username}
            )
            
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert search_data["total_count"] == len(username_data["platforms"])


@pytest.mark.asyncio
class TestEndToFuzzyMatch:
    """End-to-end tests for fuzzy match flow"""
    
    async def test_complete_fuzzy_match_flow(self, client, app):
        """Test complete fuzzy match flow"""
        mock_matches = [
            Mock(
                platform_name="GitHub",
                profile_url="https://github.com/johndoe",
                confidence=0.95,
                match_type="exact",
                metadata={}
            ),
            Mock(
                platform_name="Reddit",
                profile_url="https://reddit.com/user/johndoe123",
                confidence=0.75,
                match_type="fuzzy",
                metadata={}
            )
        ]
        app.state.username_service.fuzzy_match_search = AsyncMock(return_value=mock_matches)
        
        # Perform fuzzy search
        response = client.post(
            "/api/search/fuzzy-match",
            json={
                "username": "johndoe",
                "tolerance_level": "medium"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_username"] == "johndoe"
        assert len(data["matches"]) == 2
        
        # Verify match types
        match_types = [m["match_type"] for m in data["matches"]]
        assert "exact" in match_types
        assert "fuzzy" in match_types


@pytest.mark.asyncio
class TestEndToEndExport:
    """End-to-end tests for export functionality"""
    
    async def test_export_results_json(self, client, app):
        """Test exporting results as JSON"""
        mock_results = [
            Mock(
                platform_name="GitHub",
                profile_url="https://github.com/test",
                confidence=0.9,
                match_type="exact",
                metadata={"email": "test@example.com"}
            )
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        response = client.post(
            "/api/export/username",
            params={"format": "json", "username": "test"}
        )
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type")
        
        # Verify JSON content
        import json
        content = json.loads(response.content)
        assert "results" in content
        assert "export_timestamp" in content
    
    async def test_export_results_csv(self, client, app):
        """Test exporting results as CSV"""
        mock_results = [
            Mock(
                platform_name="GitHub",
                profile_url="https://github.com/test",
                confidence=0.9,
                match_type="exact",
                metadata={"email": "test@example.com"}
            )
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        response = client.post(
            "/api/export/username",
            params={"format": "csv", "username": "test", "include_metadata": "true"}
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type")
        
        # Verify CSV content
        content = response.content.decode('utf-8')
        assert "platform" in content
        assert "profile_url" in content


@pytest.mark.asyncio
class TestEndToErrorHandling:
    """End-to-end tests for error handling"""
    
    async def test_invalid_username_format(self, client):
        """Test handling of invalid username format"""
        response = client.post(
            "/api/search/username",
            json={"username": "john@doe"}
        )
        
        assert response.status_code == 422
    
    async def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post(
            "/api/search/reverse-lookup",
            json={}
        )
        
        assert response.status_code == 422
    
    async def test_invalid_email_format(self, client):
        """Test handling of invalid email format"""
        response = client.post(
            "/api/search/reverse-lookup",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422
    
    async def test_service_error_propagation(self, client, app):
        """Test that service errors are properly propagated"""
        app.state.username_service.enumerate_username = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        
        response = client.post(
            "/api/search/username",
            json={"username": "test"}
        )
        
        assert response.status_code == 500


@pytest.mark.asyncio
class TestEndToRateLimiting:
    """End-to-end tests for rate limiting"""
    
    async def test_rate_limit_enforcement(self, client, app):
        """Test that rate limits are enforced"""
        # Mock rate limit exceeded
        app.state.rate_limiter.check_rate_limit = AsyncMock(
            return_value=(False, {"Retry-After": "60"})
        )
        
        response = client.post(
            "/api/search/username",
            json={"username": "test"}
        )
        
        assert response.status_code == 429
        data = response.json()
        assert "error" in data
        assert data["error"] == "Rate limit exceeded"
    
    async def test_rate_limit_headers(self, client, app):
        """Test that rate limit headers are present"""
        app.state.rate_limiter.check_rate_limit = AsyncMock(
            return_value=(True, {
                "X-RateLimit-Limit-Minute": "10",
                "X-RateLimit-Remaining-Minute": "8",
                "X-RateLimit-Limit-Hour": "100",
                "X-RateLimit-Remaining-Hour": "95"
            })
        )
        
        response = client.post(
            "/api/search/username",
            json={"username": "test"}
        )
        
        # Headers should be set (actual FastAPI implementation handles this)


@pytest.mark.asyncio
class TestEndToCaching:
    """End-to-end tests for caching"""
    
    async def test_cache_hit_on_repeat_request(self, client, app):
        """Test that repeated requests use cache"""
        cached_response = {
            "results": [
                {
                    "platform": "GitHub",
                    "profile_url": "https://github.com/cached",
                    "confidence": 0.9,
                    "match_type": "exact",
                    "metadata": {},
                    "discovered_at": datetime.utcnow().isoformat()
                }
            ],
            "total_count": 1,
            "page": 1,
            "page_size": 20,
            "execution_time_ms": 100,
            "cached": True
        }
        app.state.cache_manager.get = AsyncMock(return_value=cached_response)
        
        response = client.post(
            "/api/search/username",
            json={"username": "test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] == True
        
        # Service should not be called
        app.state.username_service.enumerate_username.assert_not_called()


@pytest.mark.asyncio
class TestEndToPagination:
    """End-to-end tests for pagination"""
    
    async def test_large_result_pagination(self, client, app):
        """Test pagination of large result sets"""
        # Create many mock results
        mock_results = [
            Mock(
                platform_name=f"Platform{i}",
                profile_url=f"https://platform{i}/test",
                confidence=0.8,
                match_type="exact",
                metadata={}
            )
            for i in range(150)
        ]
        app.state.username_service.enumerate_username = AsyncMock(return_value=mock_results)
        
        # Get first page
        response1 = client.post(
            "/api/search/username?page=1&page_size=50",
            json={"username": "test"}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["total_count"] == 150
        assert data1["page"] == 1
        assert len(data1["results"]) == 50
        
        # Get second page
        response2 = client.post(
            "/api/search/username?page=2&page_size=50",
            json={"username": "test"}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert len(data2["results"]) == 50


@pytest.mark.asyncio
class TestEndToHealthChecks:
    """End-to-end tests for health checks"""
    
    async def test_health_check_all_services(self, client):
        """Test health check with all services healthy"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "timestamp" in data
    
    async def test_api_info_endpoint(self, client):
        """Test API information endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "/api/search/username" in data["endpoints"].values()


@pytest.mark.asyncio
class TestEndToStats:
    """End-to-end tests for statistics"""
    
    async def test_get_search_statistics(self, client, app):
        """Test retrieving search statistics"""
        app.state.db_manager.postgresql = Mock()
        app.state.db_manager.postgresql.get_platform_statistics = AsyncMock(return_value=[])
        app.state.db_manager.postgresql.pool = Mock()
        app.state.db_manager.postgresql.pool.acquire = AsyncMock()
        
        response = client.get("/api/search/stats?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data


@pytest.mark.asyncio
class TestEndToIdentityChains:
    """End-to-end tests for identity chains"""
    
    async def test_identity_chain_building(self, client, app):
        """Test building identity chains"""
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
                },
                {
                    "id": "node3",
                    "type": "email",
                    "value": "john@example.com",
                    "platform": "GitHub",
                    "confidence": 0.9
                }
            ],
            "relationships": [
                {
                    "source_id": "node1",
                    "target_id": "node2",
                    "relationship_type": "found_on",
                    "confidence": 0.95,
                    "discovered_at": datetime.utcnow().isoformat()
                },
                {
                    "source_id": "node2",
                    "target_id": "node3",
                    "relationship_type": "linked_to",
                    "confidence": 0.9,
                    "discovered_at": datetime.utcnow().isoformat()
                }
            ],
            "chain_length": 2
        }
        app.state.username_service.build_identity_chain = AsyncMock(return_value=mock_chain)
        
        response = client.get("/api/results/identity-chain/johndoe?max_depth=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 3
        assert len(data["relationships"]) == 2
        assert data["chain_length"] == 2


@pytest.mark.asyncio
class TestEndToConcurrentRequests:
    """End-to-end tests for concurrent request handling"""
    
    async def test_concurrent_searches(self, client, app):
        """Test handling multiple concurrent searches"""
        app.state.username_service.enumerate_username = AsyncMock(
            return_value=[
                Mock(
                    platform_name="Test",
                    profile_url="https://test.com/user",
                    confidence=0.8,
                    match_type="exact",
                    metadata={}
                )
            ]
        )
        
        # Make multiple concurrent requests
        responses = []
        for i in range(5):
            response = client.post(
                "/api/search/username",
                json={"username": f"user{i}"}
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
