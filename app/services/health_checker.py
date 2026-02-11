"""Background service health checks using HTTP, ping, and TCP."""

import asyncio
import time
import subprocess
import platform

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.service import MonitoredService
from app.models.log_entry import LogEntry


async def check_http(url: str, expected_status: int = 200, timeout: float = 5.0) -> dict:
    """Perform an HTTP health check and return status + response time."""
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            start = time.monotonic()
            response = await client.get(url, timeout=timeout)
            elapsed_ms = (time.monotonic() - start) * 1000

            if response.status_code == expected_status:
                if elapsed_ms < 200:
                    status = "online"
                elif elapsed_ms < 1000:
                    status = "degraded"
                else:
                    status = "degraded"
            else:
                status = "degraded"

            return {"status": status, "response_time_ms": round(elapsed_ms, 2)}
    except Exception:
        return {"status": "offline", "response_time_ms": None}


async def check_ping(host: str, timeout: float = 2.0) -> dict:
    """Perform a ping check using subprocess."""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
        timeout_val = str(int(timeout * 1000)) if platform.system().lower() == "windows" else str(int(timeout))

        proc = await asyncio.create_subprocess_exec(
            "ping", param, "1", timeout_param, timeout_val, host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 2)
        output = stdout.decode()

        if proc.returncode == 0:
            # Parse response time from output
            ms = None
            for part in output.split():
                if "time=" in part or "time<" in part:
                    ms_str = part.split("=")[-1].replace("ms", "").replace("<", "")
                    try:
                        ms = float(ms_str)
                    except ValueError:
                        pass
                    break

            if ms is not None:
                status = "online" if ms < 200 else "degraded"
                return {"status": status, "response_time_ms": round(ms, 2)}
            return {"status": "online", "response_time_ms": None}
        else:
            return {"status": "offline", "response_time_ms": None}
    except Exception:
        return {"status": "offline", "response_time_ms": None}


async def check_tcp(host: str, port: int = 80, timeout: float = 2.0) -> dict:
    """Perform a TCP port connectivity check."""
    try:
        start = time.monotonic()
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        writer.close()
        await writer.wait_closed()

        status = "online" if elapsed_ms < 200 else "degraded"
        return {"status": status, "response_time_ms": round(elapsed_ms, 2)}
    except Exception:
        return {"status": "offline", "response_time_ms": None}


async def check_service(service: MonitoredService) -> dict:
    """Run the appropriate health check for a service."""
    if service.check_type == "ping":
        # Extract host from URL
        host = service.url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        return await check_ping(host)
    elif service.check_type == "tcp":
        host = service.url.replace("https://", "").replace("http://", "").split("/")[0]
        parts = host.split(":")
        hostname = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 80
        return await check_tcp(hostname, port)
    else:
        return await check_http(service.url, service.expected_status)


async def run_health_checks():
    """Run health checks for all active services and update the database."""
    from datetime import datetime

    async with async_session() as session:
        result = await session.execute(
            select(MonitoredService).where(MonitoredService.is_active == True)
        )
        services = result.scalars().all()

        for service in services:
            old_status = service.status
            check_result = await check_service(service)

            service.status = check_result["status"]
            service.response_time_ms = check_result["response_time_ms"]
            service.last_checked = datetime.utcnow()

            # Log status changes
            if old_status != service.status and old_status != "unknown":
                level = "CRITICAL" if service.status == "offline" else "WARNING" if service.status == "degraded" else "INFO"
                log = LogEntry(
                    level=level,
                    source="health-checker",
                    message=f"Service '{service.name}' changed status: {old_status} -> {service.status}.",
                )
                session.add(log)

                # Notify WebSocket clients
                from app.routers.websocket import broadcast_event
                await broadcast_event({
                    "type": "service_status_change",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "data": {
                        "service_name": service.name,
                        "old_status": old_status,
                        "new_status": service.status,
                        "response_time_ms": service.response_time_ms,
                    },
                })

        await session.commit()


async def health_check_loop():
    """Background loop that runs health checks every 60 seconds."""
    while True:
        try:
            await run_health_checks()
        except Exception as e:
            print(f"Health check error: {e}")
        await asyncio.sleep(60)
