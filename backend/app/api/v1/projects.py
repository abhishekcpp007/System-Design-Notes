from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectReorderRequest,
)
from app.api.deps import get_current_admin
from app.utils.exceptions import NotFoundException
from app.utils.validators import generate_slug

router = APIRouter()


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    tech: Optional[str] = None,
    featured: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all published projects with optional filters."""
    query = select(Project).where(Project.published == True)

    # Apply filters
    if category:
        query = query.where(Project.category == category)
    if tech:
        query = query.where(Project.tech_stack.any(tech))
    if featured is not None:
        query = query.where(Project.featured == featured)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    query = query.order_by(Project.display_order.asc(), Project.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        pages=ceil(total / limit) if total > 0 else 1,
    )


@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single project by slug."""
    result = await db.execute(
        select(Project).where(Project.slug == slug, Project.published == True)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException("Project not found")
    return ProjectResponse.model_validate(project)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Create a new project (Admin only)."""
    # Generate unique slug
    slug = generate_slug(data.title)
    existing = await db.execute(select(Project).where(Project.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{await _get_next_slug_suffix(db, slug)}"

    # Get next display order
    max_order_result = await db.execute(select(func.max(Project.display_order)))
    max_order = max_order_result.scalar() or 0

    project = Project(
        author_id=current_admin.id,
        title=data.title,
        slug=slug,
        description=data.description,
        long_description=data.long_description,
        tech_stack=data.tech_stack,
        github_url=data.github_url,
        live_url=data.live_url,
        thumbnail_url=data.thumbnail_url,
        category=data.category,
        featured=data.featured,
        published=data.published,
        display_order=max_order + 1,
    )
    db.add(project)
    await db.flush()

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Update a project (Admin only)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException("Project not found")

    # Update fields that are provided
    update_data = data.model_dump(exclude_unset=True)
    if "title" in update_data:
        project.title = update_data["title"]
        project.slug = generate_slug(update_data["title"])
    for field, value in update_data.items():
        if field != "title" and hasattr(project, field):
            setattr(project, field, value)

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete a project (Admin only)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException("Project not found")

    await db.delete(project)


@router.put("/reorder", status_code=200)
async def reorder_projects(
    data: ProjectReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Reorder projects by providing ordered list of IDs (Admin only)."""
    for index, project_id in enumerate(data.project_ids):
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            project.display_order = index

    return {"message": "Projects reordered successfully"}


async def _get_next_slug_suffix(db: AsyncSession, base_slug: str) -> int:
    """Get the next available suffix for a duplicate slug."""
    result = await db.execute(
        select(func.count()).where(Project.slug.like(f"{base_slug}%"))
    )
    count = result.scalar() or 0
    return count + 1
