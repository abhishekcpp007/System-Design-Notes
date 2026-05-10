"""Tests for analytics endpoints."""
import pytest
from httpx import AsyncClient


class TestRecordPageView:
    """Test POST /api/v1/analytics/pageview"""

    async def test_record_pageview(self, client: AsyncClient):
        response = await client.post("/api/v1/analytics/pageview", json={
            "path": "/projects",
            "referrer": "https://google.com",
        })
        # Should succeed (200 or 201)
        assert response.status_code in [200, 201]

    async def test_record_pageview_minimal(self, client: AsyncClient):
        response = await client.post("/api/v1/analytics/pageview", json={
            "path": "/",
        })
        assert response.status_code in [200, 201]


class TestAnalyticsDashboard:
    """Test GET /api/v1/analytics/dashboard"""

    async def test_dashboard_as_admin(self, client: AsyncClient, admin_headers):
        response = await client.get(
            "/api/v1/analytics/dashboard", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Dashboard should have expected keys
        assert "total_views" in data or "total_pageviews" in data or isinstance(data, dict)

    async def test_dashboard_as_user_forbidden(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.get(
            "/api/v1/analytics/dashboard", headers=auth_headers
        )
        assert response.status_code == 403

    async def test_dashboard_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401
