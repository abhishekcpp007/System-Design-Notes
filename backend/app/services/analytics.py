"""
Analytics service for processing and aggregating page view data.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import PageView


class AnalyticsService:
    """Processes analytics data for dashboard display."""

    async def get_dashboard_stats(self, db: AsyncSession, days: int = 30) -> dict:
        """Get comprehensive analytics dashboard data."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Total page views in period
        total_views = await db.scalar(
            select(func.count(PageView.id)).where(PageView.viewed_at >= cutoff)
        )

        # Unique visitors (by visitor_hash)
        unique_visitors = await db.scalar(
            select(func.count(distinct(PageView.visitor_hash))).where(
                PageView.viewed_at >= cutoff
            )
        )

        # Views per day
        daily_views = await self._get_daily_views(db, cutoff, days)

        # Top pages
        top_pages = await self._get_top_pages(db, cutoff, limit=10)

        # Top referrers
        top_referrers = await self._get_top_referrers(db, cutoff, limit=10)

        # Device breakdown
        devices = await self._get_device_breakdown(db, cutoff)

        # Bounce rate estimate (single page sessions)
        bounce_rate = await self._estimate_bounce_rate(db, cutoff)

        return {
            "period_days": days,
            "total_views": total_views or 0,
            "unique_visitors": unique_visitors or 0,
            "avg_views_per_day": round((total_views or 0) / max(days, 1), 1),
            "daily_views": daily_views,
            "top_pages": top_pages,
            "top_referrers": top_referrers,
            "devices": devices,
            "bounce_rate": bounce_rate,
        }

    async def _get_daily_views(self, db: AsyncSession, cutoff: datetime, days: int) -> list[dict]:
        """Get views grouped by day."""
        result = await db.execute(
            select(
                func.date(PageView.viewed_at).label("date"),
                func.count(PageView.id).label("views"),
                func.count(distinct(PageView.visitor_hash)).label("visitors"),
            )
            .where(PageView.viewed_at >= cutoff)
            .group_by(func.date(PageView.viewed_at))
            .order_by(func.date(PageView.viewed_at))
        )

        rows = result.all()
        return [
            {"date": str(row.date), "views": row.views, "visitors": row.visitors}
            for row in rows
        ]

    async def _get_top_pages(self, db: AsyncSession, cutoff: datetime, limit: int = 10) -> list[dict]:
        """Get most viewed pages."""
        result = await db.execute(
            select(
                PageView.page_path,
                func.count(PageView.id).label("views"),
                func.count(distinct(PageView.visitor_hash)).label("unique_views"),
            )
            .where(PageView.viewed_at >= cutoff)
            .group_by(PageView.page_path)
            .order_by(func.count(PageView.id).desc())
            .limit(limit)
        )

        rows = result.all()
        return [
            {"path": row.page_path, "views": row.views, "unique_views": row.unique_views}
            for row in rows
        ]

    async def _get_top_referrers(self, db: AsyncSession, cutoff: datetime, limit: int = 10) -> list[dict]:
        """Get top traffic sources."""
        result = await db.execute(
            select(
                PageView.referrer,
                func.count(PageView.id).label("count"),
            )
            .where(PageView.viewed_at >= cutoff, PageView.referrer.isnot(None), PageView.referrer != "")
            .group_by(PageView.referrer)
            .order_by(func.count(PageView.id).desc())
            .limit(limit)
        )

        rows = result.all()
        return [{"referrer": row.referrer, "count": row.count} for row in rows]

    async def _get_device_breakdown(self, db: AsyncSession, cutoff: datetime) -> dict:
        """Get device type distribution."""
        result = await db.execute(
            select(
                PageView.device_type,
                func.count(PageView.id).label("count"),
            )
            .where(PageView.viewed_at >= cutoff)
            .group_by(PageView.device_type)
        )

        rows = result.all()
        total = sum(row.count for row in rows) or 1
        return {
            row.device_type or "unknown": round((row.count / total) * 100, 1)
            for row in rows
        }

    async def _estimate_bounce_rate(self, db: AsyncSession, cutoff: datetime) -> float:
        """Estimate bounce rate based on single-page visitors."""
        # Count visitors with only 1 page view
        subquery = (
            select(
                PageView.visitor_hash,
                func.count(PageView.id).label("page_count"),
            )
            .where(PageView.viewed_at >= cutoff)
            .group_by(PageView.visitor_hash)
            .subquery()
        )

        total_visitors = await db.scalar(select(func.count()).select_from(subquery))
        single_page_visitors = await db.scalar(
            select(func.count()).select_from(subquery).where(subquery.c.page_count == 1)
        )

        if not total_visitors:
            return 0.0
        return round((single_page_visitors or 0) / total_visitors * 100, 1)

    async def get_realtime_visitors(self, db: AsyncSession, minutes: int = 5) -> int:
        """Get count of visitors active in the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        result = await db.scalar(
            select(func.count(distinct(PageView.visitor_hash))).where(
                PageView.viewed_at >= cutoff
            )
        )
        return result or 0


# Singleton instance
analytics_service = AnalyticsService()
