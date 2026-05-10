"""
Background Job Queue using ARQ (Async Redis Queue).

Provides async task execution for:
- Email sending (contact notifications, auto-replies)
- GitHub data sync
- Analytics aggregation
- Sitemap generation
- Cache warming

Architecture:
- Jobs are defined as async functions
- Worker runs as a separate process (`arq app.services.worker.WorkerSettings`)
- Enqueue via `await enqueue_job("function_name", arg1, arg2)`
"""
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

from app.config import get_settings

settings = get_settings()

# ARQ pool (lazy)
_arq_pool: ArqRedis | None = None


def get_redis_settings() -> RedisSettings:
    """Parse Redis URL into ARQ RedisSettings."""
    url = settings.redis_url
    # Handle rediss:// (TLS) and redis:// schemes
    if url.startswith("rediss://"):
        # Upstash-style with TLS
        parts = url.replace("rediss://", "").split("@")
        if len(parts) == 2:
            auth = parts[0]
            host_port = parts[1]
        else:
            auth = ""
            host_port = parts[0]

        password = auth.split(":")[1] if ":" in auth else auth
        host = host_port.split(":")[0]
        port = int(host_port.split(":")[1]) if ":" in host_port else 6379

        return RedisSettings(host=host, port=port, password=password, ssl=True)
    else:
        # Standard redis://
        parts = url.replace("redis://", "").split("@")
        if len(parts) == 2:
            auth = parts[0]
            host_port = parts[1]
        else:
            auth = ""
            host_port = parts[0]

        password = auth.split(":")[1] if ":" in auth else (auth if auth else None)
        host = host_port.split(":")[0] if host_port else "localhost"
        port = int(host_port.split(":")[1]) if ":" in host_port else 6379

        return RedisSettings(host=host, port=port, password=password)


async def get_arq_pool() -> ArqRedis:
    """Get or create ARQ connection pool."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(get_redis_settings())
    return _arq_pool


async def enqueue_job(function_name: str, *args: Any, **kwargs: Any) -> str | None:
    """
    Enqueue a background job.

    Args:
        function_name: Name of the job function (must be registered in WorkerSettings)
        *args: Positional arguments for the job
        **kwargs: Keyword arguments for the job

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        pool = await get_arq_pool()
        job = await pool.enqueue_job(function_name, *args, **kwargs)
        return job.job_id if job else None
    except Exception:
        # If queue is unavailable, log and continue (non-critical)
        return None


# ============================================================
# Job Definitions
# ============================================================


async def send_contact_email(ctx: dict, name: str, email: str, subject: str, message: str):
    """Send contact form notification to admin and auto-reply to sender."""
    from app.services.email import email_service
    await email_service.send_contact_notification(name, email, subject, message)
    await email_service.send_auto_reply(name, email, subject)


async def sync_github_repos(ctx: dict):
    """Sync GitHub repositories and profile data to cache."""
    from app.services.github import github_service
    from app.services.cache import cache_service

    repos = await github_service.get_repos()
    profile = await github_service.get_profile()
    languages = await github_service.get_languages()

    # Cache for 1 hour
    await cache_service.set("github:repos", repos, ttl=3600)
    await cache_service.set("github:profile", profile, ttl=3600)
    await cache_service.set("github:languages", languages, ttl=3600)


async def aggregate_analytics(ctx: dict, date_str: str | None = None):
    """Aggregate raw page views into daily statistics."""
    from sqlalchemy import func, select, cast, Date
    from app.database import async_session_factory
    from app.models.analytics import PageView

    target_date = (
        datetime.fromisoformat(date_str).date()
        if date_str
        else datetime.now(timezone.utc).date()
    )

    async with async_session_factory() as session:
        # Count unique visitors and total views for the date
        result = await session.execute(
            select(
                func.count(func.distinct(PageView.visitor_hash)).label("visitors"),
                func.count(PageView.id).label("views"),
            ).where(cast(PageView.created_at, Date) == target_date)
        )
        row = result.one()
        # Store aggregated stats in cache
        from app.services.cache import cache_service
        await cache_service.set(
            f"analytics:daily:{target_date.isoformat()}",
            {"date": target_date.isoformat(), "visitors": row.visitors, "views": row.views},
            ttl=86400,  # Cache for 24 hours
        )


async def generate_sitemap(ctx: dict, base_url: str):
    """Generate sitemap.xml from published content."""
    from app.database import async_session_factory
    from app.models.project import Project
    from app.models.blog import BlogPost
    from sqlalchemy import select

    async with async_session_factory() as session:
        # Get published projects
        projects = (await session.execute(
            select(Project).where(Project.published == True)
        )).scalars().all()

        # Get published blog posts
        posts = (await session.execute(
            select(BlogPost).where(BlogPost.published == True)
        )).scalars().all()

    urls = [
        f"{base_url}/",
        f"{base_url}/projects",
        f"{base_url}/blog",
        f"{base_url}/contact",
    ]
    for p in projects:
        urls.append(f"{base_url}/projects/{p.slug}")
    for post in posts:
        urls.append(f"{base_url}/blog/{post.slug}")

    # Build sitemap XML
    xml_entries = []
    for url in urls:
        xml_entries.append(
            f"  <url><loc>{url}</loc><changefreq>weekly</changefreq></url>"
        )

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(xml_entries)
        + "\n</urlset>"
    )

    from app.services.cache import cache_service
    await cache_service.set("sitemap:xml", sitemap, ttl=86400)


async def warm_cache(ctx: dict):
    """Pre-warm frequently accessed cache keys."""
    from app.services.cache import cache_service
    from app.database import async_session_factory
    from app.models.project import Project
    from app.models.blog import BlogPost
    from sqlalchemy import select

    async with async_session_factory() as session:
        # Cache featured projects
        projects = (await session.execute(
            select(Project).where(Project.published == True, Project.featured == True)
        )).scalars().all()
        await cache_service.set(
            "projects:featured",
            [{"id": p.id, "title": p.title, "slug": p.slug, "description": p.description,
              "tech_stack": p.tech_stack, "thumbnail_url": p.thumbnail_url}
             for p in projects],
            ttl=600,
        )

        # Cache recent blog posts
        posts = (await session.execute(
            select(BlogPost)
            .where(BlogPost.published == True)
            .order_by(BlogPost.created_at.desc())
            .limit(10)
        )).scalars().all()
        await cache_service.set(
            "blog:recent",
            [{"id": p.id, "title": p.title, "slug": p.slug, "excerpt": p.excerpt,
              "tags": p.tags, "reading_time": p.reading_time, "created_at": str(p.created_at)}
             for p in posts],
            ttl=600,
        )
