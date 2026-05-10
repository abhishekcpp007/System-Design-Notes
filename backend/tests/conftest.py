"""
Test configuration and fixtures.
Uses an in-memory SQLite database for speed and isolation.
Each test gets a fresh database and app client.
"""
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

# Override settings BEFORE importing app modules
import os
os.environ.update({
    "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379/1",
    "SECRET_KEY": "test-secret-key-not-for-production",
    "ENVIRONMENT": "testing",
    "DEBUG": "true",
    "CORS_ORIGINS": "http://localhost:3000",
    "SMTP_HOST": "",
    "SMTP_PORT": "587",
    "SMTP_USER": "",
    "SMTP_PASSWORD": "",
    "FROM_EMAIL": "test@example.com",
    "ADMIN_EMAIL": "admin@example.com",
    "GITHUB_USERNAME": "testuser",
    "GITHUB_TOKEN": "",
})

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.security import hash_password, create_access_token


# Test database engine (SQLite async)
test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=False,
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the database dependency for tests."""
    async with test_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct database session for test setup/assertions."""
    async with test_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a regular test user."""
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Test User",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user."""
    user = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(test_user: User) -> str:
    """Generate a valid access token for the test user."""
    return create_access_token({"user_id": test_user.id, "role": test_user.role})


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    """Generate a valid access token for the admin user."""
    return create_access_token({"user_id": admin_user.id, "role": admin_user.role})


@pytest_asyncio.fixture
def auth_headers(user_token: str) -> dict:
    """Authorization headers for a regular user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest_asyncio.fixture
def admin_headers(admin_token: str) -> dict:
    """Authorization headers for an admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
