"""Log viewer API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.log_entry import LogEntry

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    level: str | None = None,
    source: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(LogEntry)

    if level:
        query = query.where(LogEntry.level == level)
    if source:
        query = query.where(LogEntry.source == source)

    query = query.order_by(desc(LogEntry.timestamp)).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [log.to_dict() for log in logs]


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LogEntry.source).distinct())
    sources = [row[0] for row in result.all()]
    return sources
