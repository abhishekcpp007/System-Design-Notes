"""
Full-Text Search using PostgreSQL tsvector/tsquery.

Provides:
- Search across projects and blog posts
- Ranking with ts_rank_cd
- Autocomplete with prefix matching
- Fuzzy matching with trigram similarity
- Search suggestions

Architecture:
- Uses GIN indexes on tsvector columns (created via migration)
- Supports weighted search (title > description > content)
- Returns ranked results with highlighted snippets
"""
from typing import Optional

from sqlalchemy import text, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.blog import BlogPost


class SearchService:
    """
    PostgreSQL Full-Text Search with ranking and autocomplete.

    Usage:
        results = await search_service.search("react typescript", page=1)
        suggestions = await search_service.autocomplete("rea")
    """

    async def search(
        self,
        db: AsyncSession,
        query: str,
        content_type: Optional[str] = None,  # "project", "blog", or None for all
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """
        Full-text search across projects and blog posts.

        Uses PostgreSQL to_tsvector/to_tsquery with ranking.
        """
        if not query.strip():
            return {"results": [], "total": 0, "query": query}

        # Build tsquery - handle multiple words with & (AND)
        words = query.strip().split()
        tsquery_str = " & ".join(f"{word}:*" for word in words)  # Prefix matching

        results = []
        total = 0

        # Search projects
        if content_type in (None, "project"):
            project_results = await self._search_projects(db, tsquery_str, query)
            results.extend(project_results)

        # Search blog posts
        if content_type in (None, "blog"):
            blog_results = await self._search_blog(db, tsquery_str, query)
            results.extend(blog_results)

        # Sort by rank (descending)
        results.sort(key=lambda x: x["rank"], reverse=True)
        total = len(results)

        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated = results[start:end]

        return {
            "results": paginated,
            "total": total,
            "page": page,
            "pages": (total + per_page - 1) // per_page,
            "query": query,
        }

    async def _search_projects(
        self, db: AsyncSession, tsquery_str: str, raw_query: str
    ) -> list:
        """Search projects using title + description + tech_stack."""
        query = text("""
            SELECT
                id, title, slug, description, tech_stack, category,
                ts_rank_cd(
                    setweight(to_tsvector('english', title), 'A') ||
                    setweight(to_tsvector('english', description), 'B') ||
                    setweight(to_tsvector('english', COALESCE(long_description, '')), 'C'),
                    to_tsquery('english', :tsquery)
                ) AS rank,
                ts_headline('english', description, to_tsquery('english', :tsquery),
                    'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=20'
                ) AS snippet
            FROM projects
            WHERE published = true
            AND (
                to_tsvector('english', title) ||
                to_tsvector('english', description) ||
                to_tsvector('english', COALESCE(long_description, ''))
            ) @@ to_tsquery('english', :tsquery)
            ORDER BY rank DESC
            LIMIT 50
        """)

        result = await db.execute(query, {"tsquery": tsquery_str})
        rows = result.fetchall()

        return [
            {
                "type": "project",
                "id": row.id,
                "title": row.title,
                "slug": row.slug,
                "description": row.description,
                "snippet": row.snippet,
                "category": row.category,
                "rank": float(row.rank),
                "url": f"/projects/{row.slug}",
            }
            for row in rows
        ]

    async def _search_blog(
        self, db: AsyncSession, tsquery_str: str, raw_query: str
    ) -> list:
        """Search blog posts using title + excerpt + content."""
        query = text("""
            SELECT
                id, title, slug, excerpt, tags, reading_time,
                ts_rank_cd(
                    setweight(to_tsvector('english', title), 'A') ||
                    setweight(to_tsvector('english', excerpt), 'B') ||
                    setweight(to_tsvector('english', content), 'C'),
                    to_tsquery('english', :tsquery)
                ) AS rank,
                ts_headline('english', content, to_tsquery('english', :tsquery),
                    'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=20'
                ) AS snippet
            FROM blog_posts
            WHERE published = true
            AND (
                to_tsvector('english', title) ||
                to_tsvector('english', excerpt) ||
                to_tsvector('english', content)
            ) @@ to_tsquery('english', :tsquery)
            ORDER BY rank DESC
            LIMIT 50
        """)

        result = await db.execute(query, {"tsquery": tsquery_str})
        rows = result.fetchall()

        return [
            {
                "type": "blog",
                "id": row.id,
                "title": row.title,
                "slug": row.slug,
                "excerpt": row.excerpt,
                "snippet": row.snippet,
                "tags": row.tags,
                "reading_time": row.reading_time,
                "rank": float(row.rank),
                "url": f"/blog/{row.slug}",
            }
            for row in rows
        ]

    async def autocomplete(
        self, db: AsyncSession, prefix: str, limit: int = 10
    ) -> list:
        """
        Autocomplete suggestions based on prefix matching.
        Searches titles of projects and blog posts.
        """
        if not prefix or len(prefix) < 2:
            return []

        # Use ILIKE for prefix matching (fast with trigram GIN index)
        pattern = f"{prefix}%"

        query = text("""
            (
                SELECT title, slug, 'project' AS type
                FROM projects
                WHERE published = true AND title ILIKE :pattern
                LIMIT :limit
            )
            UNION ALL
            (
                SELECT title, slug, 'blog' AS type
                FROM blog_posts
                WHERE published = true AND title ILIKE :pattern
                LIMIT :limit
            )
            ORDER BY title
            LIMIT :total_limit
        """)

        result = await db.execute(
            query, {"pattern": pattern, "limit": limit, "total_limit": limit}
        )
        rows = result.fetchall()

        return [
            {"title": row.title, "slug": row.slug, "type": row.type}
            for row in rows
        ]

    async def get_suggestions(
        self, db: AsyncSession, query: str, limit: int = 5
    ) -> list:
        """
        Get search suggestions using trigram similarity.
        Useful when FTS returns no results (fuzzy fallback).
        """
        if not query or len(query) < 3:
            return []

        sql = text("""
            SELECT title, similarity(title, :query) AS sim
            FROM (
                SELECT title FROM projects WHERE published = true
                UNION ALL
                SELECT title FROM blog_posts WHERE published = true
            ) AS all_titles
            WHERE similarity(title, :query) > 0.2
            ORDER BY sim DESC
            LIMIT :limit
        """)

        result = await db.execute(sql, {"query": query, "limit": limit})
        rows = result.fetchall()

        return [row.title for row in rows]


# Singleton
search_service = SearchService()
