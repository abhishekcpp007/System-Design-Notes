from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10, max_length=500)
    long_description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    github_url: Optional[str] = Field(None, max_length=500)
    live_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    category: str = Field(default="fullstack", max_length=50)
    featured: bool = False
    published: bool = False

    @field_validator("github_url", "live_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if not re.match(r"^https?://", v):
                raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("tech_stack")
    @classmethod
    def validate_tech_stack(cls, v: List[str]) -> List[str]:
        return [tech.strip() for tech in v if tech.strip()]


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    long_description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    github_url: Optional[str] = Field(None, max_length=500)
    live_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    featured: Optional[bool] = None
    published: Optional[bool] = None
    display_order: Optional[int] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    long_description: Optional[str] = None
    tech_stack: List[str]
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: str
    featured: bool
    display_order: int
    published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    pages: int


class ProjectReorderRequest(BaseModel):
    project_ids: List[int] = Field(..., min_length=1)
