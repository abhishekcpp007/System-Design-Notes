from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


def get_cors_config() -> dict:
    """Get CORS configuration based on settings."""
    return {
        "allow_origins": settings.cors_origins_list,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
        "expose_headers": [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ],
        "max_age": 600,  # Cache preflight for 10 minutes
    }
