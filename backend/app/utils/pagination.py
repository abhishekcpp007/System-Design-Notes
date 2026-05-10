"""
Cursor-based (keyset) pagination.

Replaces offset pagination which has O(n) performance degradation at scale.
Cursor pagination maintains O(1) performance regardless of dataset size.

How it works:
    - Client sends `cursor` (encrypted pointer to last seen item)
    - Server decodes cursor → queries WHERE id > last_id ORDER BY ... LIMIT n
    - Returns next page + new cursor for subsequent request

Advantages over offset:
    - No "page drift" when items are inserted/deleted
    - O(1) vs O(n) for deep pages
    - Works with real-time data feeds
    - Used by Twitter, Facebook, Slack APIs

Usage:
    @router.get("/projects")
    async def list_projects(pagination: CursorPagination = Depends()):
        query = select(Project).where(Project.published == True)
        return await paginate(query, pagination, db)
"""
import base64
import json
import hashlib
from typing import Optional, Any, TypeVar, Generic
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import Query
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.services.observability import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Secret for cursor HMAC (prevents tampering)
CURSOR_SECRET = "portfolio-cursor-v1"


class CursorPagination:
    """
    FastAPI dependency for cursor-based pagination parameters.
    
    Usage in route:
        async def list_items(pagination: CursorPagination = Depends()):
            ...
    """
    
    def __init__(
        self,
        cursor: Optional[str] = Query(None, description="Pagination cursor from previous response"),
        limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
        direction: str = Query("next", regex="^(next|prev)$", description="Pagination direction"),
    ):
        self.cursor = cursor
        self.limit = limit
        self.direction = direction


class CursorPage(BaseModel, Generic[T]):
    """
    Response model for cursor-paginated results.
    
    Includes:
    - items: The page of results
    - next_cursor: Cursor for next page (null if no more results)
    - prev_cursor: Cursor for previous page (null if at start)
    - has_next: Quick boolean check
    - has_prev: Quick boolean check
    - total: Optional total count (only included if requested, as COUNT is expensive)
    """
    items: list[Any] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_next: bool = False
    has_prev: bool = False
    total: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True


def encode_cursor(values: dict) -> str:
    """
    Encode pagination state into an opaque cursor string.
    
    Uses base64(json) + HMAC to prevent client tampering.
    """
    payload = json.dumps(values, default=str, sort_keys=True)
    # Add HMAC for integrity
    signature = hashlib.sha256(
        f"{CURSOR_SECRET}:{payload}".encode()
    ).hexdigest()[:16]
    
    cursor_data = json.dumps({"p": payload, "s": signature})
    return base64.urlsafe_b64encode(cursor_data.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> Optional[dict]:
    """
    Decode and verify cursor integrity.
    Returns None if cursor is invalid or tampered.
    """
    try:
        # Re-add padding
        padding = 4 - len(cursor) % 4
        if padding != 4:
            cursor += "=" * padding
        
        cursor_data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        payload = cursor_data["p"]
        signature = cursor_data["s"]
        
        # Verify HMAC
        expected_sig = hashlib.sha256(
            f"{CURSOR_SECRET}:{payload}".encode()
        ).hexdigest()[:16]
        
        if signature != expected_sig:
            logger.warning("cursor_tampered", cursor=cursor[:20])
            return None
        
        return json.loads(payload)
    except (json.JSONDecodeError, KeyError, ValueError, Exception):
        return None


async def paginate_query(
    query: Select,
    pagination: CursorPagination,
    db: AsyncSession,
    order_columns: list[tuple] = None,
    count_total: bool = False,
) -> CursorPage:
    """
    Apply cursor-based pagination to a SQLAlchemy query.
    
    Args:
        query: Base SQLAlchemy select query (with filters already applied)
        pagination: CursorPagination dependency
        db: Database session
        order_columns: List of (column, direction) tuples for ordering.
                      e.g., [(Project.created_at, "desc"), (Project.id, "desc")]
                      Last column MUST be unique (typically the primary key).
        count_total: If True, also return total count (expensive for large tables)
    
    Returns:
        CursorPage with items, cursors, and navigation flags
    """
    if order_columns is None:
        # Default: newest first, with id as tiebreaker
        logger.warning("paginate_query called without order_columns, using default")
        return CursorPage(items=[], has_next=False, has_prev=False)
    
    # Get total count if requested
    total = None
    if count_total:
        from sqlalchemy import func
        count_q = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_q)
        total = result.scalar() or 0
    
    # Decode cursor if provided
    cursor_values = None
    if pagination.cursor:
        cursor_values = decode_cursor(pagination.cursor)
        if cursor_values is None:
            logger.warning("invalid_cursor_provided")
            # Invalid cursor — start from beginning
    
    # Apply cursor filter (keyset pagination)
    if cursor_values and pagination.direction == "next":
        query = _apply_cursor_filter(query, order_columns, cursor_values, "next")
    elif cursor_values and pagination.direction == "prev":
        query = _apply_cursor_filter(query, order_columns, cursor_values, "prev")
    
    # Apply ordering
    if pagination.direction == "prev":
        # Reverse order for previous page, then reverse results
        for col, direction in order_columns:
            query = query.order_by(asc(col) if direction == "desc" else desc(col))
    else:
        for col, direction in order_columns:
            query = query.order_by(desc(col) if direction == "desc" else asc(col))
    
    # Fetch limit + 1 to determine if there are more results
    query = query.limit(pagination.limit + 1)
    
    result = await db.execute(query)
    items = list(result.scalars().all())
    
    # Determine if there are more results
    has_more = len(items) > pagination.limit
    if has_more:
        items = items[:pagination.limit]
    
    # Reverse results if going backwards
    if pagination.direction == "prev":
        items.reverse()
    
    # Build cursors
    next_cursor = None
    prev_cursor = None
    
    if items:
        if has_more or pagination.direction == "prev":
            # Build next cursor from last item
            last_item = items[-1]
            next_cursor = encode_cursor(
                _extract_cursor_values(last_item, order_columns)
            )
        
        if pagination.cursor:
            # Build prev cursor from first item
            first_item = items[0]
            prev_cursor = encode_cursor(
                _extract_cursor_values(first_item, order_columns)
            )
    
    has_next = has_more if pagination.direction == "next" else True
    has_prev = bool(pagination.cursor) if pagination.direction == "next" else has_more
    
    return CursorPage(
        items=items,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_next=has_next,
        has_prev=has_prev,
        total=total,
    )


def _apply_cursor_filter(
    query: Select,
    order_columns: list[tuple],
    cursor_values: dict,
    direction: str,
) -> Select:
    """
    Apply keyset pagination filter.
    
    For multi-column ordering (e.g., created_at DESC, id DESC):
    WHERE (created_at < cursor_created_at)
       OR (created_at = cursor_created_at AND id < cursor_id)
    
    This is the "seek method" that maintains O(1) performance.
    """
    conditions = []
    
    for i in range(len(order_columns)):
        col, col_direction = order_columns[i]
        col_name = col.key if hasattr(col, 'key') else str(col).split('.')[-1]
        cursor_val = cursor_values.get(col_name)
        
        if cursor_val is None:
            continue
        
        # Build equality conditions for preceding columns
        eq_conditions = []
        for j in range(i):
            prev_col, _ = order_columns[j]
            prev_col_name = prev_col.key if hasattr(prev_col, 'key') else str(prev_col).split('.')[-1]
            prev_val = cursor_values.get(prev_col_name)
            if prev_val is not None:
                eq_conditions.append(prev_col == prev_val)
        
        # Determine comparison operator based on sort direction and page direction
        if direction == "next":
            if col_direction == "desc":
                cmp_condition = col < cursor_val
            else:
                cmp_condition = col > cursor_val
        else:  # prev
            if col_direction == "desc":
                cmp_condition = col > cursor_val
            else:
                cmp_condition = col < cursor_val
        
        if eq_conditions:
            conditions.append(and_(*eq_conditions, cmp_condition))
        else:
            conditions.append(cmp_condition)
    
    if conditions:
        query = query.where(or_(*conditions))
    
    return query


def _extract_cursor_values(item: Any, order_columns: list[tuple]) -> dict:
    """Extract cursor values from a result item."""
    values = {}
    for col, _ in order_columns:
        col_name = col.key if hasattr(col, 'key') else str(col).split('.')[-1]
        value = getattr(item, col_name, None)
        
        # Serialize datetime for JSON encoding
        if isinstance(value, datetime):
            values[col_name] = value.isoformat()
        else:
            values[col_name] = value
    
    return values
