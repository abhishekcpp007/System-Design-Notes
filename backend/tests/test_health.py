"""Tests for health check and root endpoints."""
import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Test health and root endpoints."""

    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Portfolio API"
        assert "version" in data
