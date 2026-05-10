"""GitHub integration API routes - public endpoints for portfolio data."""
from fastapi import APIRouter

from app.services.github import github_service

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.get("/repos")
async def get_repos(limit: int = 10):
    """Get public GitHub repositories for portfolio display."""
    repos = await github_service.get_repos(limit=limit)
    return {"repos": repos, "count": len(repos)}


@router.get("/languages")
async def get_languages():
    """Get aggregated language statistics across all repos."""
    languages = await github_service.get_languages()
    return {"languages": languages}


@router.get("/profile")
async def get_profile():
    """Get GitHub profile information."""
    profile = await github_service.get_profile()
    return {"profile": profile}


@router.get("/activity")
async def get_activity():
    """Get recent GitHub contribution activity."""
    stats = await github_service.get_contribution_stats()
    return {"activity": stats}
