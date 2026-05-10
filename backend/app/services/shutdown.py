"""
Graceful Shutdown Manager.

Ensures clean application termination without:
- Dropping active HTTP requests
- Orphaning WebSocket connections
- Losing in-flight background jobs
- Corrupting database transactions

Shutdown sequence:
1. Stop accepting new connections (health check returns unhealthy)
2. Wait for in-flight requests to complete (with timeout)
3. Drain WebSocket connections (send close frame)
4. Signal background workers to finish current task
5. Close database pools and Redis connections
6. Exit

Used by:
- Kubernetes pod termination (SIGTERM)
- Railway zero-downtime deploys
- Docker container stop
"""
import asyncio
import signal
import time
from typing import Optional, Callable, Awaitable
from contextlib import asynccontextmanager

from app.services.observability import get_logger

logger = get_logger(__name__)


class GracefulShutdown:
    """
    Coordinates graceful application shutdown.
    
    Tracks:
    - Active HTTP requests (in-flight counter)
    - WebSocket connections
    - Background tasks
    - Registered shutdown hooks
    """

    def __init__(self, drain_timeout: float = 30.0):
        """
        Args:
            drain_timeout: Maximum seconds to wait for in-flight work to complete
        """
        self.drain_timeout = drain_timeout
        self._shutting_down = False
        self._active_requests: int = 0
        self._active_websockets: int = 0
        self._active_tasks: set[asyncio.Task] = set()
        self._shutdown_hooks: list[tuple[int, Callable[[], Awaitable]]] = []
        self._request_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._started_at: float = time.time()

    @property
    def is_shutting_down(self) -> bool:
        """Check if application is in shutdown mode."""
        return self._shutting_down

    @property
    def is_healthy(self) -> bool:
        """Health check — returns False during shutdown (tells LB to stop routing)."""
        return not self._shutting_down

    @property
    def uptime_seconds(self) -> float:
        """Application uptime in seconds."""
        return time.time() - self._started_at

    @property
    def active_connections(self) -> dict:
        """Current connection counts for monitoring."""
        return {
            "http_requests": self._active_requests,
            "websockets": self._active_websockets,
            "background_tasks": len(self._active_tasks),
        }

    def register_hook(self, hook: Callable[[], Awaitable], priority: int = 0):
        """
        Register a shutdown hook. Lower priority runs first.
        
        Example:
            shutdown_manager.register_hook(close_db_pool, priority=10)
            shutdown_manager.register_hook(close_redis, priority=20)
        """
        self._shutdown_hooks.append((priority, hook))
        self._shutdown_hooks.sort(key=lambda x: x[0])

    @asynccontextmanager
    async def track_request(self):
        """
        Context manager to track an HTTP request lifecycle.
        
        Usage in middleware:
            async with shutdown_manager.track_request():
                response = await call_next(request)
        """
        if self._shutting_down:
            # Don't track new requests during shutdown — they'll be rejected
            yield
            return

        async with self._request_lock:
            self._active_requests += 1
        try:
            yield
        finally:
            async with self._request_lock:
                self._active_requests -= 1

    def track_websocket_connect(self):
        """Record a new WebSocket connection."""
        self._active_websockets += 1

    def track_websocket_disconnect(self):
        """Record a WebSocket disconnection."""
        self._active_websockets = max(0, self._active_websockets - 1)

    def track_task(self, task: asyncio.Task):
        """Track a background task for graceful drain."""
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)

    async def shutdown(self):
        """
        Execute graceful shutdown sequence.
        
        Called from lifespan or signal handler.
        """
        if self._shutting_down:
            return  # Already shutting down
        
        self._shutting_down = True
        start = time.time()

        logger.warning(
            "graceful_shutdown_initiated",
            active_requests=self._active_requests,
            active_websockets=self._active_websockets,
            active_tasks=len(self._active_tasks),
            drain_timeout=self.drain_timeout,
        )

        # Phase 1: Stop accepting new work (health check now returns unhealthy)
        # Load balancers will stop routing new requests

        # Phase 2: Wait for in-flight HTTP requests to complete
        await self._drain_requests()

        # Phase 3: Close WebSocket connections
        await self._drain_websockets()

        # Phase 4: Wait for background tasks
        await self._drain_tasks()

        # Phase 5: Execute shutdown hooks (DB, Redis, etc.)
        await self._execute_hooks()

        elapsed = time.time() - start
        logger.warning(
            "graceful_shutdown_complete",
            duration_seconds=round(elapsed, 2),
            remaining_requests=self._active_requests,
            remaining_websockets=self._active_websockets,
        )

        self._shutdown_event.set()

    async def _drain_requests(self):
        """Wait for active HTTP requests to complete."""
        if self._active_requests == 0:
            return

        logger.info(
            "draining_http_requests",
            count=self._active_requests,
        )

        deadline = time.time() + self.drain_timeout * 0.5  # Use half timeout for requests
        while self._active_requests > 0 and time.time() < deadline:
            await asyncio.sleep(0.1)

        if self._active_requests > 0:
            logger.warning(
                "http_drain_timeout",
                remaining=self._active_requests,
            )

    async def _drain_websockets(self):
        """Close WebSocket connections gracefully."""
        if self._active_websockets == 0:
            return

        logger.info(
            "closing_websocket_connections",
            count=self._active_websockets,
        )

        try:
            from app.services.websocket import manager
            # Send close frame to all connected clients
            await manager.broadcast(
                "admin",
                {"type": "server_shutdown", "message": "Server is restarting"},
            )
            await manager.disconnect_all()
        except Exception as e:
            logger.error("websocket_drain_error", error=str(e))

        # Brief wait for close frames to be sent
        await asyncio.sleep(1.0)

    async def _drain_tasks(self):
        """Wait for background tasks to complete."""
        if not self._active_tasks:
            return

        logger.info(
            "waiting_for_background_tasks",
            count=len(self._active_tasks),
        )

        remaining_timeout = self.drain_timeout * 0.3  # Use 30% of timeout for tasks
        try:
            # Wait for tasks with timeout
            done, pending = await asyncio.wait(
                self._active_tasks,
                timeout=remaining_timeout,
            )

            if pending:
                logger.warning(
                    "cancelling_remaining_tasks",
                    count=len(pending),
                )
                for task in pending:
                    task.cancel()
                # Wait briefly for cancellation
                await asyncio.wait(pending, timeout=5.0)
        except Exception as e:
            logger.error("task_drain_error", error=str(e))

    async def _execute_hooks(self):
        """Run registered shutdown hooks in priority order."""
        for priority, hook in self._shutdown_hooks:
            hook_name = hook.__qualname__ if hasattr(hook, '__qualname__') else str(hook)
            try:
                logger.info("executing_shutdown_hook", hook=hook_name, priority=priority)
                await asyncio.wait_for(hook(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.error("shutdown_hook_timeout", hook=hook_name)
            except Exception as e:
                logger.error("shutdown_hook_error", hook=hook_name, error=str(e))

    async def wait_for_shutdown(self):
        """Block until shutdown is complete (useful for tests)."""
        await self._shutdown_event.wait()


# ─── Singleton ──────────────────────────────────────────────────────────────

shutdown_manager = GracefulShutdown(drain_timeout=30.0)


def setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    """
    Register OS signal handlers for graceful shutdown.
    
    SIGTERM: Kubernetes/Docker sends this before killing the process
    SIGINT: Ctrl+C in terminal (development)
    """
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(_handle_signal(s)),
        )


async def _handle_signal(sig: signal.Signals):
    """Handle termination signal."""
    logger.warning("received_signal", signal=sig.name)
    await shutdown_manager.shutdown()
