from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, close_db
from app.api.v1.router import api_router
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.token_bucket import TokenBucketRateLimiter
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.cors import get_cors_config
from app.services.observability import RequestLoggingMiddleware, configure_logging
from app.services.cache import close_redis
from app.services.shutdown import shutdown_manager, setup_signal_handlers
from app.services.event_bus import event_bus  # noqa: F401 - registers handlers on import

settings = get_settings()


# OpenAPI Tags Metadata - used for Swagger UI grouping and descriptions
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, login, JWT refresh token rotation, OAuth2 (GitHub/Google), session management.",
    },
    {
        "name": "Projects",
        "description": "Portfolio project CRUD. Supports filtering, cursor pagination, slug-based lookup, drag-and-drop reordering.",
    },
    {
        "name": "Blog",
        "description": "Blog post management with Markdown support, full-text search, tag filtering, reading time estimation, view tracking.",
    },
    {
        "name": "Contact",
        "description": "Contact form submissions with honeypot bot detection, HTML sanitization, admin management.",
    },
    {
        "name": "Analytics",
        "description": "Privacy-first analytics with visitor hashing (no cookies), page view tracking, dashboard with trends.",
    },
    {
        "name": "GitHub",
        "description": "GitHub profile integration — repositories, languages, contribution stats with circuit breaker resilience.",
    },
    {
        "name": "WebSocket",
        "description": "Real-time connections for live analytics dashboard and notification streaming.",
    },
    {
        "name": "Search",
        "description": "Full-text search across projects and blog posts using PostgreSQL tsvector/tsquery with ranking and autocomplete.",
    },
    {
        "name": "Feature Flags",
        "description": "Runtime feature toggles with Redis backing, percentage rollouts, user targeting, and A/B testing.",
    },
    {
        "name": "Events",
        "description": "Domain event bus metrics, dead letter queue inspection for debugging.",
    },
    {
        "name": "System",
        "description": "Health checks, metrics, circuit breaker status, system info. Used by monitoring and load balancers.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    - Startup: Initialize database, configure logging, register shutdown hooks
    - Shutdown: Graceful drain of connections, tasks, and external connections
    """
    # Startup
    configure_logging()

    # Register shutdown hooks (priority order: lower = runs first)
    shutdown_manager.register_hook(close_db, priority=100)
    shutdown_manager.register_hook(close_redis, priority=90)

    # Setup signal handlers for graceful shutdown
    try:
        loop = asyncio.get_running_loop()
        setup_signal_handlers(loop)
    except Exception:
        pass  # Signal handlers may not work in all environments (e.g., Windows)

    if settings.debug:
        await init_db()

    yield

    # Shutdown — coordinated by shutdown manager
    await shutdown_manager.shutdown()


# Create FastAPI application with comprehensive OpenAPI configuration
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Portfolio Backend API

Enterprise-grade backend for a developer portfolio, showcasing production-ready patterns:

### Architecture Highlights
- **Async-first**: Built on FastAPI with async SQLAlchemy + asyncpg
- **Security**: JWT with refresh token rotation, reuse detection, token bucket rate limiting, CSP headers
- **Resilience**: Circuit breakers on external services, graceful shutdown, idempotency keys
- **Observability**: Structured logging, OpenTelemetry tracing, Prometheus metrics
- **Caching**: Redis cache-aside with ETags and conditional requests
- **Search**: PostgreSQL full-text search with ranking, autocomplete, trigram fuzzy matching
- **Real-time**: WebSocket connections for live analytics and notifications
- **Background Jobs**: ARQ (async Redis queue) for email, sync, aggregation
- **Feature Flags**: Runtime toggles with percentage rollouts and user targeting
- **Event-Driven**: Internal domain event bus with dead letter queue
- **Pagination**: Cursor-based (keyset) pagination for O(1) deep page performance

### Authentication
All protected endpoints require a Bearer token in the `Authorization` header.
Tokens are obtained via `/api/v1/auth/login` and refreshed via `/api/v1/auth/refresh`.

### Rate Limiting (Token Bucket)
- General: 60 requests/minute per IP (burst capacity: 60)
- Login: 5 attempts/minute (burst: 5)
- Contact: 3 submissions/hour (burst: 3)

### Idempotency
POST/PUT/DELETE requests support `X-Idempotency-Key` header for safe retries.

### Circuit Breakers
External services (GitHub API, SMTP) use circuit breakers:
- CLOSED → normal operation
- OPEN → fast-fail with fallback (after 3-5 failures)
- HALF_OPEN → testing recovery (limited probe requests)
""",
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    contact={
        "name": "Abhishek Verma",
        "url": "https://github.com/abhishek-verma-github/portfolio",
        "email": "abhishek1pw@gmail.com",
    },
    lifespan=lifespan,
    responses={
        401: {"description": "Not authenticated - missing or invalid token"},
        403: {"description": "Forbidden - insufficient permissions"},
        409: {"description": "Conflict - duplicate idempotency key in flight"},
        429: {"description": "Rate limit exceeded - check Retry-After header"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable - circuit breaker open"},
    },
)

# ─── Middleware Stack ───────────────────────────────────────────────────────
# Order matters: first added = outermost = runs first on request, last on response

# 1. Request logging & tracing (outermost - captures everything including errors)
app.add_middleware(RequestLoggingMiddleware)

# 2. Security headers (always add, regardless of other middleware)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Idempotency (before rate limiting — cached responses bypass rate limit)
app.add_middleware(IdempotencyMiddleware)

# 4. Token bucket rate limiting (Redis-backed with Lua atomics)
app.add_middleware(TokenBucketRateLimiter)

# 5. CORS
cors_config = get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Include API routes
app.include_router(api_router)


# ─── System Endpoints ───────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health Check")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns unhealthy during graceful shutdown (signals LB to stop routing).
    Used by Railway/Docker health checks and uptime monitors.
    """
    if not shutdown_manager.is_healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "shutting_down",
                "message": "Server is draining connections",
            },
        )

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(shutdown_manager.uptime_seconds, 1),
        "connections": shutdown_manager.active_connections,
    }


@app.get("/", tags=["System"], summary="API Info")
async def root():
    """Root endpoint — returns API metadata and links to documentation."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/api/openapi.json",
        "health": "/health",
    }


@app.get("/system/circuit-breakers", tags=["System"], summary="Circuit Breaker Status")
async def circuit_breaker_status():
    """
    Get status of all circuit breakers.
    Useful for monitoring external service health.
    """
    from app.services.circuit_breaker import get_all_breakers
    return {
        "breakers": [b.to_dict() for b in get_all_breakers()],
    }


@app.get("/system/events", tags=["Events"], summary="Event Bus Metrics")
async def event_bus_metrics():
    """Get event bus metrics and dead letter queue status."""
    return {
        "metrics": event_bus.get_metrics(),
        "dead_letter_queue": event_bus.get_dead_letter_queue(limit=10),
    }
