"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


class TestSignup:
    """Test POST /api/v1/auth/signup"""

    async def test_signup_success(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert data["user"]["role"] == "user"
        # Refresh token should be set as cookie
        assert "refresh_token" in response.cookies

    async def test_signup_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "testuser@example.com",
            "password": "AnotherPass123!",
            "full_name": "Another User",
        })
        assert response.status_code == 409

    async def test_signup_weak_password_no_uppercase(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "weakpass123!",
            "full_name": "Some User",
        })
        assert response.status_code == 422

    async def test_signup_weak_password_no_digit(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "WeakPassword!",
            "full_name": "Some User",
        })
        assert response.status_code == 422

    async def test_signup_weak_password_no_special(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "WeakPassword123",
            "full_name": "Some User",
        })
        assert response.status_code == 422

    async def test_signup_short_password(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "Sh1!",
            "full_name": "Some User",
        })
        assert response.status_code == 422

    async def test_signup_invalid_email(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "not-an-email",
            "password": "SecurePass123!",
            "full_name": "Some User",
        })
        assert response.status_code == 422

    async def test_signup_invalid_name_with_numbers(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "User123",
        })
        assert response.status_code == 422

    async def test_signup_name_too_short(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "A",
        })
        assert response.status_code == 422


class TestLogin:
    """Test POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "testuser@example.com"
        assert "refresh_token" in response.cookies

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "WrongPass123!",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePass123!",
        })
        assert response.status_code == 401

    async def test_login_empty_password(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "",
        })
        assert response.status_code == 422


class TestMe:
    """Test GET/PUT /api/v1/auth/me"""

    async def test_get_me_authenticated(self, client: AsyncClient, test_user, auth_headers):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["full_name"] == "Test User"

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    async def test_update_me(self, client: AsyncClient, test_user, auth_headers):
        response = await client.put("/api/v1/auth/me", json={
            "full_name": "Updated Name",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_update_me_avatar(self, client: AsyncClient, test_user, auth_headers):
        response = await client.put("/api/v1/auth/me", json={
            "avatar_url": "https://example.com/avatar.jpg",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["avatar_url"] == "https://example.com/avatar.jpg"


class TestRefresh:
    """Test POST /api/v1/auth/refresh"""

    async def test_refresh_no_cookie(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_invalid_token(self, client: AsyncClient):
        client.cookies.set("refresh_token", "invalid-token")
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


class TestLogout:
    """Test POST /api/v1/auth/logout"""

    async def test_logout_success(self, client: AsyncClient, test_user, auth_headers):
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    async def test_logout_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401
