"""
Feature Flags API — Runtime feature toggle management.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_admin, get_optional_user
from app.services.feature_flags import ff_service

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class FlagCreateRequest(BaseModel):
    """Request to create/update a feature flag."""
    name: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$",
                      description="Flag name (lowercase, underscores)")
    enabled: bool = Field(False, description="Is the flag globally enabled?")
    description: str = Field("", max_length=500, description="Human-readable description")
    rollout_percentage: int = Field(100, ge=0, le=100, description="Percentage of users to enable for (0-100)")
    target_users: list[int] = Field(default_factory=list, description="Specific user IDs to always enable for")
    target_roles: list[str] = Field(default_factory=list, description="Roles to always enable for")
    metadata: dict = Field(default_factory=dict, description="Arbitrary metadata (e.g., ticket URL)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "dark_mode_v2",
                "enabled": True,
                "description": "New dark mode implementation with improved contrast",
                "rollout_percentage": 50,
                "target_users": [1, 2],
                "target_roles": ["admin"],
                "metadata": {"ticket": "FEAT-123", "owner": "frontend-team"},
            }
        }


class FlagUpdateRequest(BaseModel):
    """Request to partially update a feature flag."""
    enabled: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    target_users: Optional[list[int]] = None
    target_roles: Optional[list[str]] = None
    metadata: Optional[dict] = None


class FlagResponse(BaseModel):
    """Feature flag response."""
    name: str
    enabled: bool
    description: str
    rollout_percentage: int
    target_users: list[int]
    target_roles: list[str]
    metadata: dict
    created_at: str
    updated_at: str


# ============================================================
# Public Endpoints
# ============================================================


@router.get(
    "/evaluate",
    summary="Evaluate All Flags",
    description="""
    Evaluate all feature flags for the current user context.
    Returns a map of flag_name → boolean.

    **Use case:** Frontend flag bootstrap on page load.
    If unauthenticated, evaluates flags without user context (only globally-enabled flags).
    """,
)
async def evaluate_flags(
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Evaluate all flags for the current user."""
    user_id = current_user.id if current_user else None
    role = current_user.role if current_user else None
    return await ff_service.get_all_flags_for_user(user_id=user_id, role=role)


@router.get(
    "/evaluate/{flag_name}",
    summary="Evaluate Single Flag",
    description="Check if a specific feature flag is enabled for the current user.",
)
async def evaluate_single_flag(
    flag_name: str,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Evaluate a single flag."""
    user_id = current_user.id if current_user else None
    role = current_user.role if current_user else None
    enabled = await ff_service.is_enabled(flag_name, user_id=user_id, role=role)
    return {"flag": flag_name, "enabled": enabled}


# ============================================================
# Admin Endpoints
# ============================================================


@router.get(
    "/",
    summary="List All Flags (Admin)",
    description="List all registered feature flags with their configuration.",
    response_model=list[FlagResponse],
)
async def list_flags(current_user: User = Depends(get_current_admin)):
    """List all feature flags."""
    flags = await ff_service.list_flags()
    return [FlagResponse(**f.to_dict()) for f in flags]


@router.post(
    "/",
    summary="Create Feature Flag (Admin)",
    description="Create a new feature flag or overwrite an existing one.",
    response_model=FlagResponse,
    status_code=201,
)
async def create_flag(
    data: FlagCreateRequest,
    current_user: User = Depends(get_current_admin),
):
    """Create a new feature flag."""
    flag = await ff_service.create_flag(
        name=data.name,
        enabled=data.enabled,
        description=data.description,
        rollout_percentage=data.rollout_percentage,
        target_users=data.target_users,
        target_roles=data.target_roles,
        metadata=data.metadata,
    )
    return FlagResponse(**flag.to_dict())


@router.patch(
    "/{flag_name}",
    summary="Update Feature Flag (Admin)",
    description="Partially update a feature flag's configuration.",
    response_model=FlagResponse,
)
async def update_flag(
    flag_name: str,
    data: FlagUpdateRequest,
    current_user: User = Depends(get_current_admin),
):
    """Update an existing feature flag."""
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    flag = await ff_service.update_flag(flag_name, **update_data)
    if flag is None:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")

    return FlagResponse(**flag.to_dict())


@router.delete(
    "/{flag_name}",
    summary="Delete Feature Flag (Admin)",
    description="Permanently remove a feature flag.",
    status_code=204,
)
async def delete_flag(
    flag_name: str,
    current_user: User = Depends(get_current_admin),
):
    """Delete a feature flag."""
    deleted = await ff_service.delete_flag(flag_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")
