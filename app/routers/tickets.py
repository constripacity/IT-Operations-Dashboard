"""Ticket management system CRUD endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ticket import Ticket
from app.services.log_collector import create_log
from app.routers.websocket import broadcast_event

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


class TicketCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    category: str | None = None
    assigned_to: str | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    category: str | None = None
    assigned_to: str | None = None


@router.get("")
async def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(Ticket)

    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if category:
        query = query.where(Ticket.category == category)

    if sort_by == "priority":
        col = Ticket.priority
    elif sort_by == "updated_at":
        col = Ticket.updated_at
    else:
        col = Ticket.created_at

    query = query.order_by(desc(col) if order == "desc" else col)

    result = await db.execute(query)
    tickets = result.scalars().all()
    return [t.to_dict() for t in tickets]


@router.post("", status_code=201)
async def create_ticket(data: TicketCreate, db: AsyncSession = Depends(get_db)):
    ticket = Ticket(**data.model_dump())
    db.add(ticket)
    await db.flush()

    await create_log(db, "INFO", "ticket-system", f"New ticket created: {ticket.title} (#{ticket.id}).")
    await db.commit()
    await db.refresh(ticket)

    await broadcast_event({
        "type": "ticket_created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {"id": ticket.id, "title": ticket.title, "priority": ticket.priority},
    })

    return ticket.to_dict()


@router.get("/stats")
async def ticket_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket))
    tickets = result.scalars().all()

    open_count = sum(1 for t in tickets if t.status == "open")
    in_progress = sum(1 for t in tickets if t.status == "in_progress")
    resolved = sum(1 for t in tickets if t.status == "resolved")
    closed = sum(1 for t in tickets if t.status == "closed")

    by_priority = {}
    for t in tickets:
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

    by_category = {}
    for t in tickets:
        cat = t.category or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total": len(tickets),
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "by_priority": by_priority,
        "by_category": by_category,
    }


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket.to_dict()


@router.put("/{ticket_id}")
async def update_ticket(ticket_id: int, data: TicketUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_status = ticket.status
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(ticket, key, value)

    # Auto-set resolved_at when status changes to resolved
    new_status = update_data.get("status")
    if new_status == "resolved" and old_status != "resolved":
        ticket.resolved_at = datetime.utcnow()
    elif new_status and new_status != "resolved":
        ticket.resolved_at = None

    ticket.updated_at = datetime.utcnow()

    if new_status and new_status != old_status:
        await create_log(
            db, "INFO", "ticket-system",
            f"Ticket #{ticket.id} status changed: {old_status} -> {new_status}.",
        )

    await db.commit()
    await db.refresh(ticket)
    return ticket.to_dict()


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    await db.delete(ticket)
    await db.commit()
    return {"message": "Ticket deleted"}
