"""Utility to create log entries from various parts of the application."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_entry import LogEntry


async def create_log(session: AsyncSession, level: str, source: str, message: str, metadata_json: str | None = None):
    """Create a new log entry in the database."""
    log = LogEntry(
        level=level,
        source=source,
        message=message,
        metadata_json=metadata_json,
        timestamp=datetime.utcnow(),
    )
    session.add(log)
    return log
