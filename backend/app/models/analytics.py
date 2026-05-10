from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PageView(Base):
    __tablename__ = "page_views"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Page info
    page_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    
    # Visitor info (privacy-first - no PII stored)
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO country code
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # mobile/desktop/tablet
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<PageView(id={self.id}, path={self.page_path})>"
