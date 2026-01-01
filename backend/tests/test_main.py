import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "OSINT Intelligence Platform API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "api" in data["services"]
    assert data["services"]["api"] == "operational"


def test_api_docs():
    """Test API documentation is accessible"""
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_search_endpoint_exists():
    """Test search endpoint is accessible"""
    response = client.post(
        "/api/search/",
        json={
            "query": "test@example.com",
            "deep_search": False,
            "include_adult_sites": True,
            "include_personals": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "search_id" in data
    assert "query" in data
    assert data["query"] == "test@example.com"


def test_invalid_search_request():
    """Test search endpoint with invalid data"""
    response = client.post(
        "/api/search/",
        json={}
    )
    assert response.status_code == 422  # Validation error
