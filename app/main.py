import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db

# Import models so tables are registered with Base.metadata
import app.models  # noqa: F401

from app.routers import services as services_router
from app.routers import network as network_router
from app.routers import tickets as tickets_router
from app.routers import knowledge as knowledge_router
from app.routers import logs as logs_router
from app.routers import websocket as websocket_router
from app.services.health_checker import health_check_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed data
    await init_db()
    from seed import seed_database
    await seed_database()

    # Start background health check loop
    task = asyncio.create_task(health_check_loop())
    yield
    # Shutdown
    task.cancel()


app = FastAPI(
    title="IT Operations Dashboard",
    description="A full-stack IT operations monitoring dashboard",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Register routers
app.include_router(services_router.router)
app.include_router(network_router.router)
app.include_router(tickets_router.router)
app.include_router(knowledge_router.router)
app.include_router(logs_router.router)
app.include_router(websocket_router.router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
