from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactResponse, ContactListResponse
from app.api.deps import get_current_admin
from app.utils.exceptions import NotFoundException, BadRequestException
from app.utils.validators import sanitize_html

router = APIRouter()


@router.post("/", status_code=201)
async def submit_contact(
    data: ContactCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a contact form message (Public, rate-limited)."""
    # Check honeypot (bot detection)
    if data.honeypot:
        # Bot detected - pretend it succeeded (don't reveal detection)
        return {"message": "Message sent successfully"}

    # Sanitize inputs (prevent stored XSS)
    contact = Contact(
        name=sanitize_html(data.name),
        email=data.email,
        subject=sanitize_html(data.subject),
        message=sanitize_html(data.message),
    )
    db.add(contact)
    await db.flush()

    # Send notification email to admin (background)
    background_tasks.add_task(_notify_admin, contact.name, contact.subject)

    return {"message": "Message sent successfully"}


@router.get("/", response_model=ContactListResponse)
async def get_messages(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Get all contact messages (Admin only)."""
    result = await db.execute(
        select(Contact).order_by(Contact.created_at.desc())
    )
    messages = result.scalars().all()

    # Count unread
    unread_result = await db.execute(
        select(func.count()).where(Contact.is_read == False)
    )
    unread_count = unread_result.scalar() or 0

    return ContactListResponse(
        messages=[ContactResponse.model_validate(m) for m in messages],
        total=len(messages),
        unread_count=unread_count,
    )


@router.put("/{message_id}/read")
async def mark_as_read(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Mark a message as read (Admin only)."""
    result = await db.execute(select(Contact).where(Contact.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise NotFoundException("Message not found")

    message.is_read = True
    return {"message": "Marked as read"}


@router.delete("/{message_id}", status_code=204)
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Delete a contact message (Admin only)."""
    result = await db.execute(select(Contact).where(Contact.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise NotFoundException("Message not found")

    await db.delete(message)


async def _notify_admin(sender_name: str, subject: str):
    """Background task to send email notification to admin."""
    # TODO: Implement with Resend API
    # For now, just log
    print(f"[EMAIL] New contact from {sender_name}: {subject}")
