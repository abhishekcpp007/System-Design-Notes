"""
Content Versioning — Blog post revision history with diff and rollback.

Every edit creates a new revision, preserving the full history.
Enables:
- View any previous version of a post
- Diff between any two revisions
- Rollback to a previous version
- Audit trail of who changed what and when

Pattern used by: WordPress, Notion, Confluence, Wikipedia
"""
import difflib
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, select, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.services.observability import get_logger

logger = get_logger(__name__)


class BlogPostRevision(Base):
    """
    Stores a snapshot of a blog post at a point in time.
    Each edit creates a new revision.
    """
    __tablename__ = "blog_post_revisions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)  # Auto-incrementing per post
    
    # Content snapshot
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    
    # Metadata
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_summary = Column(String(500), nullable=True)  # Optional description of changes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # What changed (for quick inspection without full diff)
    changed_fields = Column(JSON, default=list)  # ["title", "content", "tags"]
    
    # Word count at this revision (for analytics)
    word_count = Column(Integer, default=0)


class ContentVersioningService:
    """
    Manages blog post revision history.
    
    Usage:
        versioning = ContentVersioningService()
        
        # Create revision before updating post
        await versioning.create_revision(db, post, author_id, "Updated introduction")
        
        # Get revision history
        revisions = await versioning.get_revisions(db, post_id)
        
        # Diff two revisions
        diff = await versioning.diff_revisions(db, post_id, rev_1, rev_2)
        
        # Rollback to revision
        await versioning.rollback(db, post_id, revision_number, author_id)
    """

    async def create_revision(
        self,
        db: AsyncSession,
        post_id: int,
        title: str,
        content: str,
        excerpt: Optional[str],
        tags: list[str],
        author_id: int,
        change_summary: Optional[str] = None,
        changed_fields: Optional[list[str]] = None,
    ) -> BlogPostRevision:
        """
        Create a new revision snapshot of the current post state.
        Call this BEFORE applying updates to the post.
        """
        # Get next revision number
        result = await db.execute(
            select(BlogPostRevision.revision_number)
            .where(BlogPostRevision.post_id == post_id)
            .order_by(desc(BlogPostRevision.revision_number))
            .limit(1)
        )
        last_rev = result.scalar_one_or_none()
        next_rev = (last_rev or 0) + 1

        revision = BlogPostRevision(
            post_id=post_id,
            revision_number=next_rev,
            title=title,
            content=content,
            excerpt=excerpt,
            tags=tags,
            author_id=author_id,
            change_summary=change_summary,
            changed_fields=changed_fields or [],
            word_count=len(content.split()),
        )
        db.add(revision)
        await db.flush()

        logger.info(
            "revision_created",
            post_id=post_id,
            revision_number=next_rev,
            author_id=author_id,
        )

        return revision

    async def get_revisions(
        self,
        db: AsyncSession,
        post_id: int,
        limit: int = 50,
    ) -> list[dict]:
        """Get revision history for a post (newest first)."""
        result = await db.execute(
            select(BlogPostRevision)
            .where(BlogPostRevision.post_id == post_id)
            .order_by(desc(BlogPostRevision.revision_number))
            .limit(limit)
        )
        revisions = result.scalars().all()

        return [
            {
                "revision_number": rev.revision_number,
                "title": rev.title,
                "author_id": rev.author_id,
                "change_summary": rev.change_summary,
                "changed_fields": rev.changed_fields,
                "word_count": rev.word_count,
                "created_at": rev.created_at.isoformat() if rev.created_at else None,
            }
            for rev in revisions
        ]

    async def get_revision(
        self,
        db: AsyncSession,
        post_id: int,
        revision_number: int,
    ) -> Optional[BlogPostRevision]:
        """Get a specific revision."""
        result = await db.execute(
            select(BlogPostRevision).where(
                BlogPostRevision.post_id == post_id,
                BlogPostRevision.revision_number == revision_number,
            )
        )
        return result.scalar_one_or_none()

    async def diff_revisions(
        self,
        db: AsyncSession,
        post_id: int,
        from_rev: int,
        to_rev: int,
    ) -> dict:
        """
        Generate a unified diff between two revisions.
        
        Returns:
            {
                "from_revision": 3,
                "to_revision": 5,
                "title_changed": bool,
                "tags_changed": bool,
                "content_diff": "unified diff string",
                "stats": {"additions": 12, "deletions": 5}
            }
        """
        rev_from = await self.get_revision(db, post_id, from_rev)
        rev_to = await self.get_revision(db, post_id, to_rev)

        if not rev_from or not rev_to:
            return {"error": "Revision not found"}

        # Generate unified diff of content
        from_lines = rev_from.content.splitlines(keepends=True)
        to_lines = rev_to.content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"Revision {from_rev}",
            tofile=f"Revision {to_rev}",
            lineterm="",
        ))

        # Count additions and deletions
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return {
            "from_revision": from_rev,
            "to_revision": to_rev,
            "title_changed": rev_from.title != rev_to.title,
            "tags_changed": rev_from.tags != rev_to.tags,
            "content_diff": "".join(diff),
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "from_word_count": rev_from.word_count,
                "to_word_count": rev_to.word_count,
            },
        }

    async def rollback(
        self,
        db: AsyncSession,
        post_id: int,
        to_revision: int,
        author_id: int,
    ) -> Optional[dict]:
        """
        Rollback a post to a previous revision.
        Creates a NEW revision with the old content (preserves history).
        
        Returns the new post state.
        """
        from app.models.blog import BlogPost

        # Get the target revision
        target = await self.get_revision(db, post_id, to_revision)
        if not target:
            return None

        # Get current post
        result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            return None

        # Save current state as a revision before rollback
        await self.create_revision(
            db=db,
            post_id=post_id,
            title=post.title,
            content=post.content,
            excerpt=post.excerpt,
            tags=post.tags,
            author_id=author_id,
            change_summary=f"Pre-rollback snapshot (before reverting to revision {to_revision})",
            changed_fields=["rollback"],
        )

        # Apply the rollback
        post.title = target.title
        post.content = target.content
        post.excerpt = target.excerpt
        post.tags = target.tags

        # Create a revision for the rollback itself
        await self.create_revision(
            db=db,
            post_id=post_id,
            title=target.title,
            content=target.content,
            excerpt=target.excerpt,
            tags=target.tags,
            author_id=author_id,
            change_summary=f"Rolled back to revision {to_revision}",
            changed_fields=["title", "content", "excerpt", "tags"],
        )

        logger.info(
            "post_rolled_back",
            post_id=post_id,
            to_revision=to_revision,
            author_id=author_id,
        )

        return {
            "post_id": post_id,
            "title": post.title,
            "content": post.content,
            "rolled_back_to": to_revision,
        }


# Singleton
versioning_service = ContentVersioningService()
