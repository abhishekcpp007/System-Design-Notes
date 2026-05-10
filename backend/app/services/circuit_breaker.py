"""
Circuit Breaker pattern implementation.

Prevents cascading failures when external services (GitHub API, SMTP, etc.) are down.
States: CLOSED (normal) → OPEN (failing, reject fast) → HALF_OPEN (testing recovery)

Usage:
    breaker = CircuitBreaker("github_api", failure_threshold=5, recovery_timeout=60)
    
    async with breaker:
        result = await call_github_api()
"""
import asyncio
import time
from enum import Enum
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from functools import wraps

from app.services.observability import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal operation - requests pass through
    OPEN = "open"  # Failing - reject immediately with fallback
    HALF_OPEN = "half_open"  # Testing - allow limited requests


@dataclass
class CircuitBreakerMetrics:
    """Tracks circuit breaker statistics for monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    state_changes: list = field(default_factory=list)


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open and request is rejected."""
    def __init__(self, breaker_name: str, retry_after: float):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. "
            f"Service unavailable. Retry after {retry_after:.1f}s"
        )


class CircuitBreaker:
    """
    Production-grade circuit breaker with:
    - Configurable failure thresholds
    - Exponential backoff on recovery timeout
    - Half-open state with limited probe requests
    - Metrics for observability
    - Optional fallback function
    - Thread-safe with asyncio locks
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        excluded_exceptions: tuple = (),
        fallback: Optional[Callable] = None,
    ):
        """
        Args:
            name: Identifier for this breaker (e.g., "github_api", "smtp")
            failure_threshold: Consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery (half-open)
            half_open_max_calls: Max concurrent calls allowed in half-open state
            success_threshold: Consecutive successes in half-open before closing
            excluded_exceptions: Exceptions that don't count as failures (e.g., 404s)
            fallback: Optional fallback function when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions
        self.fallback = fallback

        self._state = CircuitState.CLOSED
        self._last_failure_time: float = 0
        self._last_state_change: float = time.time()
        self._half_open_calls: int = 0
        self._lock = asyncio.Lock()
        self._metrics = CircuitBreakerMetrics()
        self._backoff_multiplier: int = 1  # Exponential backoff factor

    @property
    def state(self) -> CircuitState:
        """Get current state, auto-transitioning OPEN → HALF_OPEN if timeout elapsed."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            timeout = self.recovery_timeout * self._backoff_multiplier
            if elapsed >= timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        return self._metrics

    @property
    def time_until_recovery(self) -> float:
        """Seconds until circuit transitions from OPEN to HALF_OPEN."""
        if self._state != CircuitState.OPEN:
            return 0
        timeout = self.recovery_timeout * self._backoff_multiplier
        elapsed = time.time() - self._last_failure_time
        return max(0, timeout - elapsed)

    async def _transition_to(self, new_state: CircuitState):
        """Transition state with logging and metrics."""
        old_state = self._state
        if old_state == new_state:
            return

        self._state = new_state
        self._last_state_change = time.time()
        self._metrics.state_changes.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": time.time(),
        })

        # Keep only last 50 state changes
        if len(self._metrics.state_changes) > 50:
            self._metrics.state_changes = self._metrics.state_changes[-50:]

        logger.warning(
            "circuit_breaker_state_change",
            breaker=self.name,
            old_state=old_state.value,
            new_state=new_state.value,
            consecutive_failures=self._metrics.consecutive_failures,
            backoff_multiplier=self._backoff_multiplier,
        )

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
        elif new_state == CircuitState.CLOSED:
            self._backoff_multiplier = 1  # Reset backoff on full recovery

    async def _record_success(self):
        """Record a successful call."""
        self._metrics.total_requests += 1
        self._metrics.successful_requests += 1
        self._metrics.last_success_time = time.time()
        self._metrics.consecutive_failures = 0
        self._metrics.consecutive_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            if self._metrics.consecutive_successes >= self.success_threshold:
                await self._transition_to(CircuitState.CLOSED)

    async def _record_failure(self, exc: Exception):
        """Record a failed call."""
        # Don't count excluded exceptions as failures
        if isinstance(exc, self.excluded_exceptions):
            self._metrics.total_requests += 1
            return

        self._metrics.total_requests += 1
        self._metrics.failed_requests += 1
        self._metrics.last_failure_time = time.time()
        self._metrics.consecutive_failures += 1
        self._metrics.consecutive_successes = 0
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open → back to open with increased backoff
            self._backoff_multiplier = min(self._backoff_multiplier * 2, 16)
            await self._transition_to(CircuitState.OPEN)
        elif self._metrics.consecutive_failures >= self.failure_threshold:
            await self._transition_to(CircuitState.OPEN)

    async def __aenter__(self):
        """Context manager entry — check if request is allowed."""
        async with self._lock:
            current_state = self.state  # Property checks timeout transition

            if current_state == CircuitState.OPEN:
                self._metrics.rejected_requests += 1
                raise CircuitBreakerOpen(
                    self.name,
                    retry_after=self.time_until_recovery,
                )

            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._metrics.rejected_requests += 1
                    raise CircuitBreakerOpen(
                        self.name,
                        retry_after=self.recovery_timeout,
                    )
                self._half_open_calls += 1
                if self._state != CircuitState.HALF_OPEN:
                    await self._transition_to(CircuitState.HALF_OPEN)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit — record success or failure."""
        async with self._lock:
            if exc_type is None:
                await self._record_success()
            elif exc_val is not None:
                await self._record_failure(exc_val)

        # Don't suppress the exception
        return False

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker with optional fallback.
        
        If circuit is open and fallback exists, returns fallback result.
        """
        try:
            async with self:
                return await func(*args, **kwargs)
        except CircuitBreakerOpen:
            if self.fallback:
                logger.info(
                    "circuit_breaker_fallback",
                    breaker=self.name,
                    fallback=self.fallback.__name__,
                )
                if asyncio.iscoroutinefunction(self.fallback):
                    return await self.fallback(*args, **kwargs)
                return self.fallback(*args, **kwargs)
            raise

    def to_dict(self) -> dict:
        """Serialize state for monitoring endpoints."""
        return {
            "name": self.name,
            "state": self.state.value,
            "metrics": {
                "total_requests": self._metrics.total_requests,
                "successful": self._metrics.successful_requests,
                "failed": self._metrics.failed_requests,
                "rejected": self._metrics.rejected_requests,
                "consecutive_failures": self._metrics.consecutive_failures,
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "backoff_multiplier": self._backoff_multiplier,
            },
            "time_until_recovery": self.time_until_recovery,
        }


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    fallback: Optional[Callable] = None,
    excluded_exceptions: tuple = (),
):
    """
    Decorator version of circuit breaker.
    
    Usage:
        @circuit_breaker("github_api", failure_threshold=3, recovery_timeout=60)
        async def fetch_github_repos():
            ...
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        fallback=fallback,
        excluded_exceptions=excluded_exceptions,
    )

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        # Attach breaker instance for inspection
        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator


# Pre-configured breakers for known external services
github_breaker = CircuitBreaker(
    name="github_api",
    failure_threshold=3,
    recovery_timeout=60.0,
    half_open_max_calls=2,
    excluded_exceptions=(ValueError,),  # 404s etc aren't service failures
)

smtp_breaker = CircuitBreaker(
    name="smtp",
    failure_threshold=3,
    recovery_timeout=120.0,  # Email services take longer to recover
    half_open_max_calls=1,
)


def get_all_breakers() -> list[CircuitBreaker]:
    """Get all registered circuit breakers for monitoring."""
    return [github_breaker, smtp_breaker]
