from datetime import datetime, timedelta, timezone, date

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.database import get_db
from app.models.analytics import PageView
from app.models.user import User
from app.schemas.analytics import (
    PageViewCreate,
    AnalyticsDashboard,
    AnalyticsSummary,
    PopularPage,
    DailyStats,
)
from app.api.deps import get_current_admin
from app.utils.security import generate_visitor_hash
from app.utils.validators import parse_user_agent

router = APIRouter()


@router.post("/pageview", status_code=204)
async def record_pageview(
    data: PageViewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Record a page view (called by frontend on every page load)."""
    # Get visitor info from request
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Generate anonymous visitor hash
    visitor_hash = generate_visitor_hash(client_ip, user_agent)

    # Parse user agent for device/browser info
    ua_info = parse_user_agent(user_agent)

    # Create page view record
    pageview = PageView(
        page_path=data.page_path,
        visitor_hash=visitor_hash,
        device_type=ua_info["device_type"],
        browser=ua_info["browser"],
        referrer=data.referrer,
    )
    db.add(pageview)


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get analytics dashboard data (Admin only)."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Summary stats
    summary = AnalyticsSummary(
        total_visitors_today=await _count_unique_visitors(db, today_start, now),
        total_page_views_today=await _count_page_views(db, today_start, now),
        total_visitors_week=await _count_unique_visitors(db, week_start, now),
        total_page_views_week=await _count_page_views(db, week_start, now),
        total_visitors_month=await _count_unique_visitors(db, month_start, now),
        total_page_views_month=await _count_page_views(db, month_start, now),
    )

    # Popular pages (last 30 days)
    popular_result = await db.execute(
        select(PageView.page_path, func.count(PageView.id).label("views"))
        .where(PageView.created_at >= month_start)
        .group_by(PageView.page_path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    popular_pages = [
        PopularPage(page_path=row[0], views=row[1])
        for row in popular_result.all()
    ]

    # Daily stats (last 7 days)
    daily_stats = []
    for i in range(7):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        visitors = await _count_unique_visitors(db, day_start, day_end)
        views = await _count_page_views(db, day_start, day_end)
        daily_stats.append(DailyStats(
            date=day_start.date(),
            visitors=visitors,
            page_views=views,
        ))
    daily_stats.reverse()

    # Top countries
    country_result = await db.execute(
        select(PageView.country, func.count(PageView.id).label("count"))
        .where(PageView.created_at >= month_start, PageView.country.isnot(None))
        .group_by(PageView.country)
        .order_by(func.count(PageView.id).desc())
        .limit(5)
    )
    top_countries = [
        {"country": row[0], "count": row[1]}
        for row in country_result.all()
    ]

    # Device breakdown
    device_result = await db.execute(
        select(PageView.device_type, func.count(PageView.id).label("count"))
        .where(PageView.created_at >= month_start, PageView.device_type.isnot(None))
        .group_by(PageView.device_type)
    )
    device_breakdown = [
        {"device": row[0], "count": row[1]}
        for row in device_result.all()
    ]

    return AnalyticsDashboard(
        summary=summary,
        popular_pages=popular_pages,
        daily_stats=daily_stats,
        top_countries=top_countries,
        device_breakdown=device_breakdown,
    )


async def _count_unique_visitors(
    db: AsyncSession, start: datetime, end: datetime
) -> int:
    """Count unique visitors in time range."""
    result = await db.execute(
        select(func.count(func.distinct(PageView.visitor_hash)))
        .where(PageView.created_at >= start, PageView.created_at < end)
    )
    return result.scalar() or 0


async def _count_page_views(
    db: AsyncSession, start: datetime, end: datetime
) -> int:
    """Count total page views in time range."""
    result = await db.execute(
        select(func.count(PageView.id))
        .where(PageView.created_at >= start, PageView.created_at < end)
    )
    return result.scalar() or 0
