"""Service monitoring CRUD and health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service import MonitoredService
from app.services.health_checker import check_service

router = APIRouter(prefix="/api/services", tags=["services"])


class ServiceCreate(BaseModel):
    name: str
    url: str
    check_type: str = "http"
    expected_status: int = 200
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    check_type: str | None = None
    expected_status: int | None = None
    is_active: bool | None = None


@router.get("")
async def list_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredService).order_by(MonitoredService.name))
    services = result.scalars().all()
    return [s.to_dict() for s in services]


@router.post("", status_code=201)
async def create_service(data: ServiceCreate, db: AsyncSession = Depends(get_db)):
    service = MonitoredService(**data.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service.to_dict()


@router.get("/stats")
async def service_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredService))
    services = result.scalars().all()

    total = len(services)
    online = sum(1 for s in services if s.status == "online")
    offline = sum(1 for s in services if s.status == "offline")
    degraded = sum(1 for s in services if s.status == "degraded")
    response_times = [s.response_time_ms for s in services if s.response_time_ms is not None]
    avg_response = round(sum(response_times) / len(response_times), 2) if response_times else 0

    return {
        "total": total,
        "online": online,
        "offline": offline,
        "degraded": degraded,
        "unknown": total - online - offline - degraded,
        "avg_response_time_ms": avg_response,
        "online_percentage": round((online / total) * 100, 1) if total > 0 else 0,
    }


@router.get("/{service_id}")
async def get_service(service_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service.to_dict()


@router.put("/{service_id}")
async def update_service(service_id: int, data: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)

    await db.commit()
    await db.refresh(service)
    return service.to_dict()


@router.delete("/{service_id}")
async def delete_service(service_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    await db.delete(service)
    await db.commit()
    return {"message": "Service deleted"}


@router.post("/{service_id}/check")
async def manual_check(service_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    check_result = await check_service(service)
    service.status = check_result["status"]
    service.response_time_ms = check_result["response_time_ms"]
    service.last_checked = datetime.utcnow()

    await db.commit()
    await db.refresh(service)
    return service.to_dict()
