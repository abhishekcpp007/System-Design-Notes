"""
Search API — Full-text search across projects and blog posts.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.search import search_service

router = APIRouter()


@router.get(
    "/",
    summary="Full-Text Search",
    description="""
    Search across all published projects and blog posts using PostgreSQL full-text search.

    **Features:**
    - Weighted ranking (title > description > content)
    - Prefix matching for partial words
    - Highlighted snippets in results
    - Content type filtering

    **Example:** `/api/v1/search?q=react+typescript&type=project`
    """,
    response_description="Ranked search results with snippets",
)
async def search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    type: str | None = Query(None, regex="^(project|blog)$", description="Filter by content type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """Perform full-text search with ranking and snippets."""
    return await search_service.search(db, q, content_type=type, page=page, per_page=per_page)


@router.get(
    "/autocomplete",
    summary="Autocomplete Suggestions",
    description="Get title suggestions based on prefix matching. Minimum 2 characters.",
)
async def autocomplete(
    q: str = Query(..., min_length=2, max_length=100, description="Search prefix"),
    limit: int = Query(10, ge=1, le=20, description="Max suggestions"),
    db: AsyncSession = Depends(get_db),
):
    """Get autocomplete suggestions for search input."""
    return await search_service.autocomplete(db, q, limit=limit)


@router.get(
    "/suggestions",
    summary="Fuzzy Search Suggestions",
    description="Get 'did you mean?' suggestions using trigram similarity. Useful when full-text search returns no results.",
)
async def suggestions(
    q: str = Query(..., min_length=3, max_length=100, description="Query to find suggestions for"),
    limit: int = Query(5, ge=1, le=10, description="Max suggestions"),
    db: AsyncSession = Depends(get_db),
):
    """Get fuzzy search suggestions (did you mean?)."""
    return await search_service.get_suggestions(db, q, limit=limit)
