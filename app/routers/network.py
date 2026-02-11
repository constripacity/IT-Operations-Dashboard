"""Network diagnostic tools API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.network_tools import dns_lookup, geoip_lookup, port_scan, reverse_dns_lookup

router = APIRouter(prefix="/api/network", tags=["network"])


class DnsRequest(BaseModel):
    domain: str
    record_type: str = "A"


class GeoIpRequest(BaseModel):
    ip: str


class PortScanRequest(BaseModel):
    host: str
    ports: list[int] | None = None


class ReverseDnsRequest(BaseModel):
    ip: str


@router.post("/dns")
async def dns_lookup_endpoint(data: DnsRequest):
    return await dns_lookup(data.domain, data.record_type)


@router.post("/geoip")
async def geoip_endpoint(data: GeoIpRequest):
    return await geoip_lookup(data.ip)


@router.post("/portscan")
async def portscan_endpoint(data: PortScanRequest):
    return await port_scan(data.host, data.ports)


@router.post("/reverse-dns")
async def reverse_dns_endpoint(data: ReverseDnsRequest):
    return await reverse_dns_lookup(data.ip)
