from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)
    honeypot: Optional[str] = Field(None, exclude=True)  # Bot trap - should always be empty

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError("Name can only contain letters, spaces, hyphens, apostrophes, and dots")
        return v.strip()


class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    is_read: bool
    is_replied: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    messages: List[ContactResponse]
    total: int
    unread_count: int
