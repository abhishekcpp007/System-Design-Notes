from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from app.database import get_db
from app.models.blog import BlogPost
from app.models.user import User
from app.schemas.blog import (
    BlogCreate,
    BlogUpdate,
    BlogResponse,
    BlogListResponse,
    BlogTagsResponse,
)
from app.api.deps import get_current_admin, get_optional_user
from app.utils.exceptions import NotFoundException
from app.utils.validators import generate_slug, calculate_reading_time

router = APIRouter()


@router.get("/", response_model=BlogListResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all published blog posts."""
    query = select(BlogPost).where(BlogPost.published == True)

    # Apply filters
    if tag:
        query = query.where(BlogPost.tags.any(tag))
    if search:
        query = query.where(
            BlogPost.title.ilike(f"%{search}%") | BlogPost.excerpt.ilike(f"%{search}%")
        )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Order and paginate
    query = query.order_by(BlogPost.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    posts = result.scalars().all()

    return BlogListResponse(
        posts=[BlogResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        pages=ceil(total / limit) if total > 0 else 1,
    )


@router.get("/tags", response_model=BlogTagsResponse)
async def get_tags(db: AsyncSession = Depends(get_db)):
    """Get all unique tags from published posts."""
    result = await db.execute(
        select(func.unnest(BlogPost.tags)).where(BlogPost.published == True).distinct()
    )
    tags = [row[0] for row in result.all()]
    return BlogTagsResponse(tags=sorted(tags))


@router.get("/{slug}", response_model=BlogResponse)
async def get_post(
    slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get a single blog post by slug. Increments view count."""
    query = select(BlogPost).where(BlogPost.slug == slug)
    
    # Non-admin can only see published posts
    if not current_user or current_user.role != "admin":
        query = query.where(BlogPost.published == True)

    result = await db.execute(query)
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException("Blog post not found")

    # Increment view count in background (don't slow down response)
    background_tasks.add_task(_increment_views, post.id)

    return BlogResponse.model_validate(post)


@router.post("/", response_model=BlogResponse, status_code=201)
async def create_post(
    data: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Create a new blog post (Admin only)."""
    slug = generate_slug(data.title)
    
    # Ensure unique slug
    existing = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{await _get_next_slug_suffix(db, slug)}"

    post = BlogPost(
        author_id=current_admin.id,
        title=data.title,
        slug=slug,
        content=data.content,
        excerpt=data.excerpt,
        tags=data.tags,
        published=data.published,
        reading_time=calculate_reading_time(data.content),
    )
    db.add(post)
    await db.flush()

    return BlogResponse.model_validate(post)


@router.put("/{post_id}", response_model=BlogResponse)
async def update_post(
    post_id: int,
    data: BlogUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update a blog post (Admin only)."""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException("Blog post not found")

    update_data = data.model_dump(exclude_unset=True)
    if "title" in update_data:
        post.title = update_data["title"]
        post.slug = generate_slug(update_data["title"])
    if "content" in update_data:
        post.content = update_data["content"]
        post.reading_time = calculate_reading_time(update_data["content"])
    for field, value in update_data.items():
        if field not in ("title", "content") and hasattr(post, field):
            setattr(post, field, value)

    return BlogResponse.model_validate(post)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete a blog post (Admin only)."""
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException("Blog post not found")

    await db.delete(post)


async def _increment_views(post_id: int):
    """Background task to increment view count."""
    from app.database import async_session_maker
    
    async with async_session_maker() as session:
        result = await session.execute(select(BlogPost).where(BlogPost.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.views_count += 1
            await session.commit()


async def _get_next_slug_suffix(db: AsyncSession, base_slug: str) -> int:
    """Get the next available suffix for a duplicate slug."""
    result = await db.execute(
        select(func.count()).where(BlogPost.slug.like(f"{base_slug}%"))
    )
    count = result.scalar() or 0
    return count + 1
