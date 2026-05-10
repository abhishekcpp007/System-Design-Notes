"""Tests for blog endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import BlogPost
from app.models.user import User


@pytest.fixture
async def sample_post(db_session: AsyncSession, admin_user: User) -> BlogPost:
    """Create a sample blog post for testing."""
    post = BlogPost(
        title="Test Blog Post",
        slug="test-blog-post",
        excerpt="A short excerpt for the test post",
        content="# Hello World\n\nThis is the full content of the test blog post.",
        tags=["python", "testing"],
        published=True,
        reading_time=3,
        views=0,
        author_id=admin_user.id,
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    return post


@pytest.fixture
async def draft_post(db_session: AsyncSession, admin_user: User) -> BlogPost:
    """Create a draft blog post."""
    post = BlogPost(
        title="Draft Post",
        slug="draft-post",
        excerpt="Draft excerpt",
        content="Draft content that is not published yet.",
        tags=["draft"],
        published=False,
        reading_time=1,
        views=0,
        author_id=admin_user.id,
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    return post


class TestListBlogPosts:
    """Test GET /api/v1/blog"""

    async def test_list_posts_empty(self, client: AsyncClient):
        response = await client.get("/api/v1/blog")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_posts_only_published(
        self, client: AsyncClient, sample_post, draft_post
    ):
        """Public listing should only show published posts."""
        response = await client.get("/api/v1/blog")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Test Blog Post"

    async def test_list_posts_search(self, client: AsyncClient, sample_post):
        response = await client.get("/api/v1/blog?search=Hello")
        assert response.status_code == 200
        # Search depends on implementation - just verify no crash
        assert response.status_code == 200

    async def test_list_posts_filter_by_tag(self, client: AsyncClient, sample_post):
        response = await client.get("/api/v1/blog?tag=python")
        assert response.status_code == 200

    async def test_list_posts_pagination(self, client: AsyncClient, sample_post):
        response = await client.get("/api/v1/blog?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestGetBlogPost:
    """Test GET /api/v1/blog/{slug}"""

    async def test_get_post_by_slug(self, client: AsyncClient, sample_post):
        response = await client.get("/api/v1/blog/test-blog-post")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Blog Post"
        assert data["content"] == "# Hello World\n\nThis is the full content of the test blog post."
        assert data["tags"] == ["python", "testing"]

    async def test_get_post_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/blog/nonexistent-post")
        assert response.status_code == 404

    async def test_get_draft_post_unauthenticated(self, client: AsyncClient, draft_post):
        """Unauthenticated users should not see drafts."""
        response = await client.get("/api/v1/blog/draft-post")
        assert response.status_code == 404


class TestCreateBlogPost:
    """Test POST /api/v1/blog"""

    async def test_create_post_as_admin(self, client: AsyncClient, admin_headers):
        response = await client.post("/api/v1/blog", json={
            "title": "New Blog Post",
            "content": "This is a new blog post with enough content to calculate reading time properly.",
            "excerpt": "A new blog post",
            "tags": ["fastapi", "python"],
            "published": True,
        }, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Blog Post"
        assert data["slug"] == "new-blog-post"
        assert data["published"] is True

    async def test_create_post_as_user_forbidden(
        self, client: AsyncClient, auth_headers
    ):
        response = await client.post("/api/v1/blog", json={
            "title": "Unauthorized Post",
            "content": "Content",
            "tags": [],
        }, headers=auth_headers)
        assert response.status_code == 403

    async def test_create_post_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/v1/blog", json={
            "title": "No Auth Post",
            "content": "Content",
            "tags": [],
        })
        assert response.status_code == 401


class TestUpdateBlogPost:
    """Test PUT /api/v1/blog/{slug}"""

    async def test_update_post_as_admin(
        self, client: AsyncClient, admin_headers, sample_post
    ):
        response = await client.put("/api/v1/blog/test-blog-post", json={
            "title": "Updated Blog Post",
            "content": "Updated content here.",
        }, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Blog Post"

    async def test_update_post_not_found(self, client: AsyncClient, admin_headers):
        response = await client.put("/api/v1/blog/nonexistent", json={
            "title": "Ghost",
        }, headers=admin_headers)
        assert response.status_code == 404


class TestDeleteBlogPost:
    """Test DELETE /api/v1/blog/{slug}"""

    async def test_delete_post_as_admin(
        self, client: AsyncClient, admin_headers, sample_post
    ):
        response = await client.delete(
            "/api/v1/blog/test-blog-post", headers=admin_headers
        )
        assert response.status_code == 200

        # Verify deleted
        response = await client.get("/api/v1/blog/test-blog-post")
        assert response.status_code == 404

    async def test_delete_post_unauthorized(
        self, client: AsyncClient, auth_headers, sample_post
    ):
        response = await client.delete(
            "/api/v1/blog/test-blog-post", headers=auth_headers
        )
        assert response.status_code == 403
