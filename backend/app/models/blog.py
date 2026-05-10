from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, Text, ForeignKey, ARRAY, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Content
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # MDX content
    excerpt: Mapped[str] = mapped_column(String(500), nullable=False)  # Preview text
    
    # Metadata
    tags: Mapped[list] = mapped_column(ARRAY(String), default=[], nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reading_time: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # In minutes
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    author = relationship("User", back_populates="blog_posts")

    def __repr__(self) -> str:
        return f"<BlogPost(id={self.id}, title={self.title}, published={self.published})>"
