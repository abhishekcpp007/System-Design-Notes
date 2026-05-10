from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.blog import router as blog_router
from app.api.v1.contact import router as contact_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.github import router as github_router
from app.api.v1.search import router as search_router
from app.api.v1.feature_flags import router as feature_flags_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.revisions import router as revisions_router
from app.services.websocket import router as websocket_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(blog_router, prefix="/blog", tags=["Blog"])
api_router.include_router(contact_router, prefix="/contact", tags=["Contact"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(github_router, prefix="/github", tags=["GitHub"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(feature_flags_router, prefix="/flags", tags=["Feature Flags"])
api_router.include_router(metrics_router, prefix="/metrics", tags=["System"])
api_router.include_router(websocket_router, tags=["WebSocket"])
api_router.include_router(revisions_router, prefix="/blog", tags=["Blog"])
