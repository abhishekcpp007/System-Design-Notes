"""Add full-text search indexes and trigram extension

Revision ID: 002_search_indexes
Revises: 001_initial
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "002_search_indexes"
down_revision = None  # Set to actual initial migration revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for fuzzy/similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # GIN indexes for full-text search on projects
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_projects_fts
        ON projects
        USING GIN (
            (
                setweight(to_tsvector('english', title), 'A') ||
                setweight(to_tsvector('english', description), 'B') ||
                setweight(to_tsvector('english', COALESCE(long_description, '')), 'C')
            )
        )
    """)

    # GIN indexes for full-text search on blog_posts
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_blog_posts_fts
        ON blog_posts
        USING GIN (
            (
                setweight(to_tsvector('english', title), 'A') ||
                setweight(to_tsvector('english', excerpt), 'B') ||
                setweight(to_tsvector('english', content), 'C')
            )
        )
    """)

    # Trigram indexes for autocomplete/fuzzy matching
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_projects_title_trgm
        ON projects
        USING GIN (title gin_trgm_ops)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_blog_posts_title_trgm
        ON blog_posts
        USING GIN (title gin_trgm_ops)
    """)

    # Composite indexes for common query patterns
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_projects_published_featured
        ON projects (published, featured, display_order)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_blog_posts_published_date
        ON blog_posts (published, created_at DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_page_views_date
        ON page_views (created_at)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_page_views_visitor_date
        ON page_views (visitor_hash, created_at)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash
        ON refresh_tokens (token_hash)
        WHERE is_revoked = false
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_projects_fts")
    op.execute("DROP INDEX IF EXISTS idx_blog_posts_fts")
    op.execute("DROP INDEX IF EXISTS idx_projects_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_blog_posts_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_projects_published_featured")
    op.execute("DROP INDEX IF EXISTS idx_blog_posts_published_date")
    op.execute("DROP INDEX IF EXISTS idx_page_views_date")
    op.execute("DROP INDEX IF EXISTS idx_page_views_visitor_date")
    op.execute("DROP INDEX IF EXISTS idx_refresh_tokens_hash")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
