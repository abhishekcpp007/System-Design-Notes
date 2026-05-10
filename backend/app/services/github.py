"""
GitHub integration service.
Fetches repos, languages, contribution data for portfolio display.
"""
import httpx
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubService:
    """Fetches GitHub data for portfolio display."""

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.username = settings.GITHUB_USERNAME
        self._cache: dict = {}
        self._cache_ttl = timedelta(hours=1)
        self._cache_timestamps: dict = {}

    @property
    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Portfolio-App",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache_timestamps:
            return False
        return datetime.utcnow() - self._cache_timestamps[key] < self._cache_ttl

    def _set_cache(self, key: str, data):
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.utcnow()

    async def get_repos(self, limit: int = 10, sort: str = "updated") -> list[dict]:
        """Fetch user's public repositories."""
        cache_key = f"repos_{limit}_{sort}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        if not self.username:
            logger.warning("GitHub username not configured")
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GITHUB_API}/users/{self.username}/repos",
                    headers=self._headers,
                    params={
                        "sort": sort,
                        "direction": "desc",
                        "per_page": limit,
                        "type": "owner",
                    },
                )
                response.raise_for_status()

            repos = []
            for repo in response.json():
                if repo.get("fork"):
                    continue
                repos.append({
                    "name": repo["name"],
                    "description": repo.get("description", ""),
                    "url": repo["html_url"],
                    "homepage": repo.get("homepage", ""),
                    "language": repo.get("language", ""),
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "topics": repo.get("topics", []),
                    "updated_at": repo["updated_at"],
                    "created_at": repo["created_at"],
                })

            self._set_cache(cache_key, repos)
            return repos

        except httpx.HTTPError as e:
            logger.error(f"GitHub API error: {e}")
            return self._cache.get(cache_key, [])

    async def get_languages(self) -> dict[str, int]:
        """Get aggregated language statistics across all repos."""
        cache_key = "languages"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        if not self.username:
            return {}

        try:
            repos = await self.get_repos(limit=30)
            languages: dict[str, int] = {}

            async with httpx.AsyncClient() as client:
                for repo in repos[:15]:  # Limit API calls
                    response = await client.get(
                        f"{GITHUB_API}/repos/{self.username}/{repo['name']}/languages",
                        headers=self._headers,
                    )
                    if response.status_code == 200:
                        for lang, bytes_count in response.json().items():
                            languages[lang] = languages.get(lang, 0) + bytes_count

            # Sort by bytes and convert to percentages
            total = sum(languages.values()) or 1
            result = {
                lang: round((count / total) * 100, 1)
                for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)
            }

            self._set_cache(cache_key, result)
            return result

        except httpx.HTTPError as e:
            logger.error(f"GitHub languages error: {e}")
            return self._cache.get(cache_key, {})

    async def get_profile(self) -> Optional[dict]:
        """Get GitHub profile info."""
        cache_key = "profile"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        if not self.username:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GITHUB_API}/users/{self.username}",
                    headers=self._headers,
                )
                response.raise_for_status()

            data = response.json()
            profile = {
                "username": data["login"],
                "name": data.get("name", ""),
                "bio": data.get("bio", ""),
                "avatar_url": data["avatar_url"],
                "public_repos": data["public_repos"],
                "followers": data["followers"],
                "following": data["following"],
                "created_at": data["created_at"],
            }

            self._set_cache(cache_key, profile)
            return profile

        except httpx.HTTPError as e:
            logger.error(f"GitHub profile error: {e}")
            return self._cache.get(cache_key)

    async def get_contribution_stats(self) -> Optional[dict]:
        """Get contribution activity (commits, PRs, issues)."""
        cache_key = "contributions"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        if not self.username:
            return None

        try:
            async with httpx.AsyncClient() as client:
                # Get recent events for activity summary
                response = await client.get(
                    f"{GITHUB_API}/users/{self.username}/events",
                    headers=self._headers,
                    params={"per_page": 100},
                )
                response.raise_for_status()

            events = response.json()
            stats = {
                "push_events": 0,
                "pr_events": 0,
                "issue_events": 0,
                "total_events": len(events),
                "recent_activity": [],
            }

            for event in events[:50]:
                event_type = event.get("type", "")
                if event_type == "PushEvent":
                    stats["push_events"] += 1
                elif event_type == "PullRequestEvent":
                    stats["pr_events"] += 1
                elif event_type == "IssuesEvent":
                    stats["issue_events"] += 1

            # Get 5 most recent meaningful activities
            for event in events[:20]:
                repo_name = event.get("repo", {}).get("name", "")
                event_type = event.get("type", "")
                created_at = event.get("created_at", "")

                if event_type in ("PushEvent", "PullRequestEvent", "CreateEvent"):
                    stats["recent_activity"].append({
                        "type": event_type,
                        "repo": repo_name,
                        "date": created_at,
                    })
                    if len(stats["recent_activity"]) >= 5:
                        break

            self._set_cache(cache_key, stats)
            return stats

        except httpx.HTTPError as e:
            logger.error(f"GitHub contributions error: {e}")
            return self._cache.get(cache_key)


# Singleton instance
github_service = GitHubService()
