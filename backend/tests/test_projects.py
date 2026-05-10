"""Tests for project endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User


@pytest.fixture
async def sample_project(db_session: AsyncSession, admin_user: User) -> Project:
    """Create a sample project for testing."""
    project = Project(
        title="Test Project",
        slug="test-project",
        description="A test project description",
        long_description="Detailed description of the test project",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        github_url="https://github.com/testuser/test-project",
        live_url="https://test-project.com",
        status="completed",
        featured=True,
        display_order=1,
        author_id=admin_user.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


class TestListProjects:
    """Test GET /api/v1/projects"""

    async def test_list_projects_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_projects_with_data(self, client: AsyncClient, sample_project):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Test Project"
        assert data["items"][0]["slug"] == "test-project"

    async def test_list_projects_filter_by_status(
        self, client: AsyncClient, sample_project
    ):
        response = await client.get("/api/v1/projects?status=completed")
        assert response.status_code == 200
        assert response.json()["total"] == 1

        response = await client.get("/api/v1/projects?status=in_progress")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_list_projects_filter_featured(
        self, client: AsyncClient, sample_project
    ):
        response = await client.get("/api/v1/projects?featured=true")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    async def test_list_projects_pagination(self, client: AsyncClient, sample_project):
        response = await client.get("/api/v1/projects?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data


class TestGetProject:
    """Test GET /api/v1/projects/{slug}"""

    async def test_get_project_by_slug(self, client: AsyncClient, sample_project):
        response = await client.get("/api/v1/projects/test-project")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Project"
        assert data["tech_stack"] == ["Python", "FastAPI", "PostgreSQL"]

    async def test_get_project_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/projects/nonexistent-project")
        assert response.status_code == 404


class TestCreateProject:
    """Test POST /api/v1/projects"""

    async def test_create_project_as_admin(self, client: AsyncClient, admin_headers):
        response = await client.post("/api/v1/projects", json={
            "title": "New Project",
            "description": "A brand new project",
            "tech_stack": ["React", "TypeScript"],
            "status": "in_progress",
            "featured": False,
        }, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Project"
        assert data["slug"] == "new-project"
        assert data["tech_stack"] == ["React", "TypeScript"]

    async def test_create_project_as_user_forbidden(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.post("/api/v1/projects", json={
            "title": "Unauthorized Project",
            "description": "Should fail",
            "tech_stack": ["Python"],
        }, headers=auth_headers)
        assert response.status_code == 403

    async def test_create_project_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/v1/projects", json={
            "title": "No Auth Project",
            "description": "Should fail",
            "tech_stack": ["Python"],
        })
        assert response.status_code == 401


class TestUpdateProject:
    """Test PUT /api/v1/projects/{slug}"""

    async def test_update_project_as_admin(
        self, client: AsyncClient, admin_headers, sample_project
    ):
        response = await client.put("/api/v1/projects/test-project", json={
            "title": "Updated Project",
            "description": "Updated description",
        }, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Project"

    async def test_update_project_not_found(self, client: AsyncClient, admin_headers):
        response = await client.put("/api/v1/projects/nonexistent", json={
            "title": "Ghost",
        }, headers=admin_headers)
        assert response.status_code == 404

    async def test_update_project_unauthorized(
        self, client: AsyncClient, auth_headers, sample_project
    ):
        response = await client.put("/api/v1/projects/test-project", json={
            "title": "Hacked",
        }, headers=auth_headers)
        assert response.status_code == 403


class TestDeleteProject:
    """Test DELETE /api/v1/projects/{slug}"""

    async def test_delete_project_as_admin(
        self, client: AsyncClient, admin_headers, sample_project
    ):
        response = await client.delete(
            "/api/v1/projects/test-project", headers=admin_headers
        )
        assert response.status_code == 200

        # Verify deleted
        response = await client.get("/api/v1/projects/test-project")
        assert response.status_code == 404

    async def test_delete_project_unauthorized(
        self, client: AsyncClient, auth_headers, sample_project
    ):
        response = await client.delete(
            "/api/v1/projects/test-project", headers=auth_headers
        )
        assert response.status_code == 403
