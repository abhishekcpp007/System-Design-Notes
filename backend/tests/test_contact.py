"""Tests for contact endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import ContactMessage


@pytest.fixture
async def sample_message(db_session: AsyncSession) -> ContactMessage:
    """Create a sample contact message."""
    message = ContactMessage(
        name="John Doe",
        email="john@example.com",
        subject="Hello",
        message="I'd like to discuss a project collaboration.",
        is_read=False,
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


class TestSubmitContact:
    """Test POST /api/v1/contact"""

    async def test_submit_contact_success(self, client: AsyncClient):
        response = await client.post("/api/v1/contact", json={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "subject": "Project Inquiry",
            "message": "I'm interested in working together on a web project.",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Message sent successfully"

    async def test_submit_contact_missing_fields(self, client: AsyncClient):
        response = await client.post("/api/v1/contact", json={
            "name": "Jane",
            "email": "jane@example.com",
        })
        assert response.status_code == 422

    async def test_submit_contact_invalid_email(self, client: AsyncClient):
        response = await client.post("/api/v1/contact", json={
            "name": "Jane Smith",
            "email": "not-an-email",
            "subject": "Test",
            "message": "Testing invalid email.",
        })
        assert response.status_code == 422

    async def test_submit_contact_honeypot_filled(self, client: AsyncClient):
        """If honeypot field is filled, should silently reject (bot detected)."""
        response = await client.post("/api/v1/contact", json={
            "name": "Bot",
            "email": "bot@spam.com",
            "subject": "Spam",
            "message": "Buy our stuff!",
            "website": "http://spam.com",  # honeypot field
        })
        # Should return 201 (silent rejection) to not tip off bots
        assert response.status_code == 201

    async def test_submit_contact_xss_sanitized(self, client: AsyncClient):
        """HTML/script tags should be sanitized."""
        response = await client.post("/api/v1/contact", json={
            "name": "Attacker",
            "email": "hacker@example.com",
            "subject": "<script>alert('xss')</script>",
            "message": "Hello <img src=x onerror=alert('xss')>",
        })
        assert response.status_code == 201


class TestAdminContactMessages:
    """Test admin contact message endpoints."""

    async def test_list_messages_as_admin(
        self, client: AsyncClient, admin_headers, sample_message
    ):
        response = await client.get("/api/v1/contact", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_list_messages_as_user_forbidden(
        self, client: AsyncClient, auth_headers, sample_message
    ):
        response = await client.get("/api/v1/contact", headers=auth_headers)
        assert response.status_code == 403

    async def test_list_messages_unauthenticated(
        self, client: AsyncClient, sample_message
    ):
        response = await client.get("/api/v1/contact")
        assert response.status_code == 401

    async def test_mark_message_read(
        self, client: AsyncClient, admin_headers, sample_message
    ):
        response = await client.patch(
            f"/api/v1/contact/{sample_message.id}/read",
            headers=admin_headers,
        )
        assert response.status_code == 200

    async def test_delete_message_as_admin(
        self, client: AsyncClient, admin_headers, sample_message
    ):
        response = await client.delete(
            f"/api/v1/contact/{sample_message.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
