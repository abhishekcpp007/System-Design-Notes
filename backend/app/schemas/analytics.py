from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class PageViewCreate(BaseModel):
    page_path: str = Field(..., max_length=500)
    referrer: Optional[str] = Field(None, max_length=500)


class AnalyticsSummary(BaseModel):
    total_visitors_today: int
    total_page_views_today: int
    total_visitors_week: int
    total_page_views_week: int
    total_visitors_month: int
    total_page_views_month: int


class PopularPage(BaseModel):
    page_path: str
    views: int


class DailyStats(BaseModel):
    date: date
    visitors: int
    page_views: int


class AnalyticsDashboard(BaseModel):
    summary: AnalyticsSummary
    popular_pages: List[PopularPage]
    daily_stats: List[DailyStats]
    top_countries: List[dict]
    device_breakdown: List[dict]
