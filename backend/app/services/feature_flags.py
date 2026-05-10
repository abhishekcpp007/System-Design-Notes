"""
Feature Flags System with Redis backing.

Provides:
- Runtime feature toggles without deploys
- Percentage-based rollouts
- User targeting (by ID, role, or custom attributes)
- Flag evaluation with fallback defaults
- Admin API for flag management

Architecture:
- Flags stored in Redis as JSON
- Evaluated per-request with user context
- Cached locally with short TTL for performance
"""
import json
import hashlib
import time
from typing import Any, Optional
from datetime import datetime, timezone

from app.services.cache import get_redis
from app.config import get_settings

settings = get_settings()

# Redis key prefix for feature flags
FLAGS_PREFIX = "ff:"
FLAGS_INDEX_KEY = "ff:__index__"


class FeatureFlag:
    """Represents a single feature flag configuration."""

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        rollout_percentage: int = 100,  # 0-100
        target_users: list[int] | None = None,
        target_roles: list[str] | None = None,
        metadata: dict | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ):
        self.name = name
        self.enabled = enabled
        self.description = description
        self.rollout_percentage = rollout_percentage
        self.target_users = target_users or []
        self.target_roles = target_roles or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "rollout_percentage": self.rollout_percentage,
            "target_users": self.target_users,
            "target_roles": self.target_roles,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlag":
        return cls(**data)


class FeatureFlagService:
    """
    Feature flag evaluation and management.

    Usage:
        # Check if feature is enabled for a user
        if await ff_service.is_enabled("dark_mode", user_id=123, role="admin"):
            ...

        # Create/update flag
        await ff_service.create_flag("new_feature", enabled=True, rollout_percentage=50)
    """

    def _flag_key(self, name: str) -> str:
        return f"{FLAGS_PREFIX}{name}"

    def _hash_user_for_rollout(self, flag_name: str, user_id: int) -> int:
        """
        Deterministic hash for consistent percentage rollout.
        Same user always gets same result for same flag.
        """
        hash_input = f"{flag_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        return hash_value % 100

    async def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        default: bool = False,
    ) -> bool:
        """
        Evaluate if a feature flag is enabled for the given context.

        Evaluation order:
        1. Flag exists? No → return default
        2. Flag.enabled? No → return False
        3. User in target_users? Yes → return True
        4. Role in target_roles? Yes → return True
        5. Rollout percentage check (deterministic hash)
        """
        flag = await self.get_flag(flag_name)
        if flag is None:
            return default

        if not flag.enabled:
            return False

        # User targeting
        if user_id and flag.target_users and user_id in flag.target_users:
            return True

        # Role targeting
        if role and flag.target_roles and role in flag.target_roles:
            return True

        # If there are specific targets but user doesn't match, check rollout
        if flag.target_users or flag.target_roles:
            # Has targets but user didn't match — only proceed if 100% rollout
            if flag.rollout_percentage < 100:
                if user_id:
                    return self._hash_user_for_rollout(flag_name, user_id) < flag.rollout_percentage
                return False

        # Percentage rollout
        if flag.rollout_percentage >= 100:
            return True
        if flag.rollout_percentage <= 0:
            return False

        if user_id:
            return self._hash_user_for_rollout(flag_name, user_id) < flag.rollout_percentage

        # No user context — use random-ish evaluation
        return False

    async def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        r = await get_redis()
        data = await r.get(self._flag_key(name))
        if data is None:
            return None
        return FeatureFlag.from_dict(json.loads(data))

    async def create_flag(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        rollout_percentage: int = 100,
        target_users: list[int] | None = None,
        target_roles: list[str] | None = None,
        metadata: dict | None = None,
    ) -> FeatureFlag:
        """Create or update a feature flag."""
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            description=description,
            rollout_percentage=rollout_percentage,
            target_users=target_users,
            target_roles=target_roles,
            metadata=metadata,
        )

        r = await get_redis()
        await r.set(self._flag_key(name), json.dumps(flag.to_dict()))

        # Add to index
        await r.sadd(FLAGS_INDEX_KEY, name)

        return flag

    async def update_flag(self, name: str, **kwargs) -> Optional[FeatureFlag]:
        """Update specific fields of a feature flag."""
        flag = await self.get_flag(name)
        if flag is None:
            return None

        for key, value in kwargs.items():
            if hasattr(flag, key):
                setattr(flag, key, value)

        flag.updated_at = datetime.now(timezone.utc).isoformat()

        r = await get_redis()
        await r.set(self._flag_key(name), json.dumps(flag.to_dict()))
        return flag

    async def delete_flag(self, name: str) -> bool:
        """Delete a feature flag."""
        r = await get_redis()
        deleted = await r.delete(self._flag_key(name))
        await r.srem(FLAGS_INDEX_KEY, name)
        return deleted > 0

    async def list_flags(self) -> list[FeatureFlag]:
        """List all feature flags."""
        r = await get_redis()
        flag_names = await r.smembers(FLAGS_INDEX_KEY)

        flags = []
        for name in flag_names:
            flag = await self.get_flag(name)
            if flag:
                flags.append(flag)

        return sorted(flags, key=lambda f: f.name)

    async def get_all_flags_for_user(
        self, user_id: Optional[int] = None, role: Optional[str] = None
    ) -> dict[str, bool]:
        """Evaluate all flags for a user — useful for frontend flag bootstrap."""
        flags = await self.list_flags()
        return {
            flag.name: await self.is_enabled(flag.name, user_id=user_id, role=role)
            for flag in flags
        }


# Singleton
ff_service = FeatureFlagService()
