"""Page routes serving Jinja2 templates."""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/services")
async def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})


@router.get("/tickets")
async def tickets_page(request: Request):
    return templates.TemplateResponse("tickets.html", {"request": request})


@router.get("/network")
async def network_page(request: Request):
    return templates.TemplateResponse("network.html", {"request": request})


@router.get("/knowledge")
async def knowledge_page(request: Request):
    return templates.TemplateResponse("knowledge.html", {"request": request})


@router.get("/logs")
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})
