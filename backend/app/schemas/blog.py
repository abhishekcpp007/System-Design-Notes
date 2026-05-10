from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BlogCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    content: str = Field(..., min_length=50)
    excerpt: str = Field(..., min_length=10, max_length=500)
    tags: List[str] = Field(default_factory=list)
    published: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Getting Started with FastAPI",
                "content": "# FastAPI\n\nFastAPI is a modern Python framework...",
                "excerpt": "Learn how to build APIs with FastAPI",
                "tags": ["python", "fastapi", "backend"],
                "published": True,
            }
        }


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    content: Optional[str] = Field(None, min_length=50)
    excerpt: Optional[str] = Field(None, min_length=10, max_length=500)
    tags: Optional[List[str]] = None
    published: Optional[bool] = None


class BlogResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str
    tags: List[str]
    published: bool
    views_count: int
    reading_time: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlogListResponse(BaseModel):
    posts: List[BlogResponse]
    total: int
    page: int
    pages: int


class BlogTagsResponse(BaseModel):
    tags: List[str]
