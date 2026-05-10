"""
Internal Event Bus — Domain Event-Driven Architecture.

Implements pub/sub pattern for decoupling business logic from side effects.
Events are fire-and-forget with optional async handlers.

Architecture:
    Route Handler → emits DomainEvent
    Event Bus → dispatches to registered handlers
    Handlers → execute side effects (email, cache invalidation, WebSocket push, analytics)

This pattern enables:
- Decoupled business logic (handlers don't know about each other)
- Easy testing (mock the event bus)
- Auditability (all events are logged)
- Extensibility (add handlers without modifying core logic)

Usage:
    # Define events
    class ContactSubmitted(DomainEvent):
        name: str
        email: str
        message: str
    
    # Register handler
    @event_bus.on(ContactSubmitted)
    async def handle_contact(event: ContactSubmitted):
        await send_notification_email(event)
    
    # Emit event (fire-and-forget)
    await event_bus.emit(ContactSubmitted(name="John", email="j@x.com", message="Hi"))
"""
import asyncio
import time
import traceback
from typing import Any, Callable, Type, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timezone

from app.services.observability import get_logger

logger = get_logger(__name__)


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    
    # Auto-populated metadata
    event_id: str = field(default_factory=lambda: f"{time.time_ns()}")
    timestamp: float = field(default_factory=time.time)
    
    @property
    def event_type(self) -> str:
        return self.__class__.__name__
    
    def to_dict(self) -> dict:
        """Serialize event for logging/storage."""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            else:
                data[key] = value
        data["event_type"] = self.event_type
        return data


# ─── Domain Events ──────────────────────────────────────────────────────────

@dataclass
class UserCreated(DomainEvent):
    user_id: int = 0
    email: str = ""
    full_name: str = ""


@dataclass
class UserLoggedIn(DomainEvent):
    user_id: int = 0
    email: str = ""
    ip_address: str = ""


@dataclass
class ContactSubmitted(DomainEvent):
    contact_id: int = 0
    name: str = ""
    email: str = ""
    subject: str = ""
    message: str = ""


@dataclass
class ProjectCreated(DomainEvent):
    project_id: int = 0
    title: str = ""
    slug: str = ""
    author_id: int = 0


@dataclass
class ProjectUpdated(DomainEvent):
    project_id: int = 0
    title: str = ""
    slug: str = ""
    changed_fields: list = field(default_factory=list)


@dataclass
class ProjectDeleted(DomainEvent):
    project_id: int = 0
    title: str = ""


@dataclass
class BlogPostCreated(DomainEvent):
    post_id: int = 0
    title: str = ""
    slug: str = ""
    author_id: int = 0
    published: bool = False


@dataclass
class BlogPostUpdated(DomainEvent):
    post_id: int = 0
    title: str = ""
    slug: str = ""
    changed_fields: list = field(default_factory=list)


@dataclass
class BlogPostPublished(DomainEvent):
    post_id: int = 0
    title: str = ""
    slug: str = ""


@dataclass
class BlogPostDeleted(DomainEvent):
    post_id: int = 0
    title: str = ""


@dataclass
class CacheInvalidated(DomainEvent):
    pattern: str = ""
    reason: str = ""


@dataclass
class FeatureFlagChanged(DomainEvent):
    flag_name: str = ""
    enabled: bool = False
    changed_by: int = 0


# ─── Event Bus ──────────────────────────────────────────────────────────────

class EventBus:
    """
    Async event bus with:
    - Multiple handlers per event type
    - Fire-and-forget execution (non-blocking)
    - Error isolation (one handler failure doesn't affect others)
    - Dead letter queue for failed events
    - Metrics and observability
    - Priority ordering for handlers
    """

    def __init__(self):
        self._handlers: dict[Type[DomainEvent], list[tuple[int, Callable]]] = defaultdict(list)
        self._dead_letter_queue: list[dict] = []
        self._metrics = {
            "events_emitted": 0,
            "events_handled": 0,
            "events_failed": 0,
        }
        self._max_dlq_size = 100

    def on(self, event_type: Type[DomainEvent], priority: int = 0):
        """
        Decorator to register an event handler.
        
        Args:
            event_type: The domain event class to handle
            priority: Lower number = higher priority (default 0)
        
        Usage:
            @event_bus.on(ContactSubmitted)
            async def notify_admin(event: ContactSubmitted):
                await send_email(event.email, event.message)
        """
        def decorator(func: Callable):
            self._handlers[event_type].append((priority, func))
            # Sort by priority (lower = first)
            self._handlers[event_type].sort(key=lambda x: x[0])
            return func
        return decorator

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable, priority: int = 0):
        """Programmatic handler registration (non-decorator form)."""
        self._handlers[event_type].append((priority, handler))
        self._handlers[event_type].sort(key=lambda x: x[0])

    async def emit(self, event: DomainEvent, wait: bool = False):
        """
        Emit a domain event to all registered handlers.
        
        Args:
            event: The domain event instance
            wait: If True, await all handlers (useful for testing)
                  If False, fire-and-forget (production default)
        """
        self._metrics["events_emitted"] += 1
        handlers = self._handlers.get(type(event), [])

        logger.info(
            "domain_event_emitted",
            event_type=event.event_type,
            event_id=event.event_id,
            handler_count=len(handlers),
        )

        if not handlers:
            return

        if wait:
            # Synchronous execution (for testing)
            for priority, handler in handlers:
                await self._execute_handler(handler, event)
        else:
            # Fire-and-forget (production)
            for priority, handler in handlers:
                asyncio.create_task(
                    self._execute_handler(handler, event)
                )

    async def _execute_handler(self, handler: Callable, event: DomainEvent):
        """Execute a single handler with error isolation."""
        handler_name = f"{handler.__module__}.{handler.__qualname__}"
        try:
            await handler(event)
            self._metrics["events_handled"] += 1
            logger.debug(
                "event_handler_success",
                handler=handler_name,
                event_type=event.event_type,
            )
        except Exception as e:
            self._metrics["events_failed"] += 1
            error_info = {
                "event": event.to_dict(),
                "handler": handler_name,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": time.time(),
            }
            self._dead_letter_queue.append(error_info)

            # Trim DLQ
            if len(self._dead_letter_queue) > self._max_dlq_size:
                self._dead_letter_queue = self._dead_letter_queue[-self._max_dlq_size:]

            logger.error(
                "event_handler_failed",
                handler=handler_name,
                event_type=event.event_type,
                event_id=event.event_id,
                error=str(e),
            )

    def get_metrics(self) -> dict:
        """Get event bus metrics for monitoring."""
        return {
            **self._metrics,
            "registered_events": len(self._handlers),
            "total_handlers": sum(len(h) for h in self._handlers.values()),
            "dead_letter_queue_size": len(self._dead_letter_queue),
        }

    def get_dead_letter_queue(self, limit: int = 20) -> list[dict]:
        """Get recent failed events for debugging."""
        return self._dead_letter_queue[-limit:]

    def clear_dead_letter_queue(self):
        """Clear the DLQ after investigation."""
        self._dead_letter_queue.clear()


# ─── Singleton ──────────────────────────────────────────────────────────────

event_bus = EventBus()


# ─── Built-in Handlers ──────────────────────────────────────────────────────

@event_bus.on(ContactSubmitted, priority=0)
async def handle_contact_email(event: ContactSubmitted):
    """Send notification email when contact form is submitted."""
    try:
        from app.services.jobs import enqueue_job
        await enqueue_job(
            "send_contact_email",
            name=event.name,
            email=event.email,
            subject=event.subject,
            message=event.message,
        )
    except Exception:
        # Fallback to direct send if job queue unavailable
        from app.services.email import email_service
        email_service.send_contact_notification(
            event.name, event.email, event.subject, event.message
        )


@event_bus.on(ProjectCreated, priority=0)
async def handle_project_cache_invalidation(event: ProjectCreated):
    """Invalidate project list caches when new project is created."""
    try:
        from app.services.cache import cache_service
        await cache_service.invalidate_pattern("projects:*")
    except Exception as e:
        logger.warning("cache_invalidation_failed", error=str(e))


@event_bus.on(ProjectUpdated, priority=0)
async def handle_project_update_cache(event: ProjectUpdated):
    """Invalidate specific project and list caches."""
    try:
        from app.services.cache import cache_service
        await cache_service.invalidate_pattern("projects:*")
        await cache_service.delete(f"project:{event.slug}")
    except Exception as e:
        logger.warning("cache_invalidation_failed", error=str(e))


@event_bus.on(ProjectDeleted, priority=0)
async def handle_project_delete_cache(event: ProjectDeleted):
    """Invalidate all project caches on delete."""
    try:
        from app.services.cache import cache_service
        await cache_service.invalidate_pattern("projects:*")
    except Exception as e:
        logger.warning("cache_invalidation_failed", error=str(e))


@event_bus.on(BlogPostCreated, priority=0)
async def handle_blog_cache_invalidation(event: BlogPostCreated):
    """Invalidate blog caches when new post is created."""
    try:
        from app.services.cache import cache_service
        await cache_service.invalidate_pattern("blog:*")
    except Exception as e:
        logger.warning("cache_invalidation_failed", error=str(e))


@event_bus.on(BlogPostPublished, priority=0)
async def handle_blog_publish_notification(event: BlogPostPublished):
    """Notify via WebSocket when new post is published."""
    try:
        from app.services.websocket import manager
        await manager.broadcast(
            "notifications",
            {
                "type": "blog_published",
                "title": event.title,
                "slug": event.slug,
                "timestamp": event.timestamp,
            },
        )
    except Exception as e:
        logger.warning("websocket_notification_failed", error=str(e))


@event_bus.on(BlogPostUpdated, priority=0)
async def handle_blog_update_cache(event: BlogPostUpdated):
    """Invalidate blog caches on update."""
    try:
        from app.services.cache import cache_service
        await cache_service.invalidate_pattern("blog:*")
        await cache_service.delete(f"blog:{event.slug}")
    except Exception as e:
        logger.warning("cache_invalidation_failed", error=str(e))


@event_bus.on(FeatureFlagChanged, priority=0)
async def handle_flag_change_notification(event: FeatureFlagChanged):
    """Broadcast feature flag changes to connected admin clients."""
    try:
        from app.services.websocket import manager
        await manager.broadcast(
            "admin",
            {
                "type": "feature_flag_changed",
                "flag": event.flag_name,
                "enabled": event.enabled,
            },
        )
    except Exception as e:
        logger.warning("websocket_notification_failed", error=str(e))
