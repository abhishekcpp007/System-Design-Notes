"""
Blog post revision API routes.

Provides version history, diffs, and rollback for blog posts.
Admin-only endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_admin
from app.services.versioning import versioning_service
from app.utils.exceptions import NotFoundException

router = APIRouter()


@router.get("/{post_id}/revisions")
async def get_revisions(
    post_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get revision history for a blog post.
    Returns list of revisions with metadata (newest first).
    """
    revisions = await versioning_service.get_revisions(db, post_id, limit=limit)
    return {"post_id": post_id, "revisions": revisions, "count": len(revisions)}


@router.get("/{post_id}/revisions/{revision_number}")
async def get_revision(
    post_id: int,
    revision_number: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get full content of a specific revision."""
    revision = await versioning_service.get_revision(db, post_id, revision_number)
    if not revision:
        raise NotFoundException(f"Revision {revision_number} not found for post {post_id}")

    return {
        "post_id": post_id,
        "revision_number": revision.revision_number,
        "title": revision.title,
        "content": revision.content,
        "excerpt": revision.excerpt,
        "tags": revision.tags,
        "author_id": revision.author_id,
        "change_summary": revision.change_summary,
        "word_count": revision.word_count,
        "created_at": revision.created_at.isoformat() if revision.created_at else None,
    }


@router.get("/{post_id}/revisions/{from_rev}/diff/{to_rev}")
async def diff_revisions(
    post_id: int,
    from_rev: int,
    to_rev: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Get unified diff between two revisions.
    Useful for reviewing what changed between versions.
    """
    diff = await versioning_service.diff_revisions(db, post_id, from_rev, to_rev)
    if "error" in diff:
        raise NotFoundException(diff["error"])
    return diff


@router.post("/{post_id}/revisions/{revision_number}/rollback")
async def rollback_to_revision(
    post_id: int,
    revision_number: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Rollback a blog post to a previous revision.
    Creates new revisions for audit trail (non-destructive).
    """
    result = await versioning_service.rollback(
        db, post_id, revision_number, current_admin.id
    )
    if not result:
        raise NotFoundException(f"Cannot rollback: revision {revision_number} not found")

    await db.commit()
    return {
        "message": f"Post rolled back to revision {revision_number}",
        **result,
    }
