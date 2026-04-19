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
        """Legacy route should not be mounted in V1 runtime."""
        response = client.get("/api/search-areas")
        assert response.status_code == 404

    def test_create_search_area(self, test_search_area):
        """Legacy route should not be mounted in V1 runtime."""
        response = client.post("/api/search-areas", json=test_search_area)
        assert response.status_code == 404

    def test_invalid_coordinates(self):
        """Legacy route should not be mounted in V1 runtime."""
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
        assert response.status_code == 404


class TestProspectEndpoints:
    """Test prospect API endpoints."""

    def test_list_prospects(self):
        """Legacy route should not be mounted in V1 runtime."""
        response = client.get("/api/prospects")
        assert response.status_code == 404

    def test_list_prospects_with_filter(self, test_search_area):
        """Legacy route should not be mounted in V1 runtime."""
        response = client.get(
            "/api/prospects",
            params={"search_area_id": "550e8400-e29b-41d4-a716-446655440000"}
        )
        assert response.status_code == 404


class TestV1SearchEndpoints:
    """Test active V1 real search routes."""

    def test_search_requires_required_context(self):
        response = client.post(
            "/api/search",
            json={
                "country": "South Africa",
                "province": "Western Cape",
                "city": "Cape Town",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 0
        assert "required" in payload["message"].lower()
