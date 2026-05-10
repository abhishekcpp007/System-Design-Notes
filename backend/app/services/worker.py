"""
ARQ Worker Configuration.

Run with: arq app.services.worker.WorkerSettings
"""
from arq.connections import RedisSettings

from app.services.jobs import (
    get_redis_settings,
    send_contact_email,
    sync_github_repos,
    aggregate_analytics,
    generate_sitemap,
    warm_cache,
)


class WorkerSettings:
    """ARQ worker settings — defines available jobs and schedule."""

    redis_settings: RedisSettings = get_redis_settings()

    # Register all job functions
    functions = [
        send_contact_email,
        sync_github_repos,
        aggregate_analytics,
        generate_sitemap,
        warm_cache,
    ]

    # Cron jobs — periodic background tasks
    cron_jobs = [
        # Sync GitHub data every hour
        {"coroutine": sync_github_repos, "hour": None, "minute": 0},
        # Aggregate yesterday's analytics at 1 AM
        {"coroutine": aggregate_analytics, "hour": 1, "minute": 0},
        # Regenerate sitemap daily at 2 AM
        {"coroutine": generate_sitemap, "hour": 2, "minute": 0},
        # Warm cache every 10 minutes
        {"coroutine": warm_cache, "hour": None, "minute": {0, 10, 20, 30, 40, 50}},
    ]

    # Worker configuration
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
    retry_jobs = True
    max_tries = 3
