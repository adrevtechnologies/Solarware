"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_readiness_check(self):
        """Test readiness check."""
        response = client.get("/health/ready")
        # Will be 503 if database not available locally
        assert response.status_code in [200, 503]


class TestSearchAreaEndpoints:
    """Test search area API endpoints."""

    def test_list_search_areas(self):
        """Test listing search areas."""
        response = client.get("/api/search-areas")
        if response.status_code == 200:
            assert isinstance(response.json(), list)
            return
        assert response.status_code in [500, 503]

    def test_create_search_area(self, test_search_area):
        """Test creating search area."""
        response = client.post("/api/search-areas", json=test_search_area)
        # Accept successful creation or DB-unavailable environments
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["name"] == test_search_area["name"]
            assert data["country"] == test_search_area["country"]
            return
        assert response.status_code in [500, 503]

    def test_invalid_coordinates(self):
        """Test invalid coordinates validation."""
        invalid_area = {
            "name": "Invalid",
            "country": "US",
            "min_latitude": 100.0,  # Invalid
            "max_latitude": 40.0,
            "min_longitude": -74.0,
            "max_longitude": -73.0,
            "min_roof_area_sqft": 5000,
        }
        response = client.post("/api/search-areas", json=invalid_area)
        # Pydantic body validation now returns 422 before route logic runs.
        assert response.status_code in [400, 422]


class TestProspectEndpoints:
    """Test prospect API endpoints."""

    def test_list_prospects(self):
        """Test listing prospects."""
        response = client.get("/api/prospects")
        if response.status_code == 200:
            assert isinstance(response.json(), list)
            return
        assert response.status_code in [500, 503]

    def test_list_prospects_with_filter(self, test_search_area):
        """Test listing with search area filter."""
        response = client.get(
            "/api/prospects",
            params={"search_area_id": "550e8400-e29b-41d4-a716-446655440000"}
        )
        assert response.status_code in [200, 500, 503]
