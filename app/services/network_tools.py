"""Network diagnostic tools: DNS lookup, IP geolocation, port scanning, reverse DNS."""

import asyncio
import socket

import dns.resolver
import dns.reversename
import httpx


async def dns_lookup(domain: str, record_type: str = "A") -> dict:
    """Perform a DNS lookup for the given domain and record type."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        answers = resolver.resolve(domain, record_type)
        records = [str(rdata) for rdata in answers]
        return {
            "domain": domain,
            "record_type": record_type,
            "records": records,
            "ttl": answers.rrset.ttl,
        }
    except dns.resolver.NXDOMAIN:
        return {"domain": domain, "record_type": record_type, "error": "Domain not found (NXDOMAIN)"}
    except dns.resolver.NoAnswer:
        return {"domain": domain, "record_type": record_type, "error": f"No {record_type} records found"}
    except dns.resolver.Timeout:
        return {"domain": domain, "record_type": record_type, "error": "DNS query timed out"}
    except Exception as e:
        return {"domain": domain, "record_type": record_type, "error": str(e)}


async def geoip_lookup(ip: str) -> dict:
    """Look up geolocation data for an IP address using ip-api.com."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"},
                timeout=5.0,
            )
            data = response.json()
            if data.get("status") == "fail":
                return {"ip": ip, "error": data.get("message", "Lookup failed")}
            return {
                "ip": data.get("query", ip),
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "zip": data.get("zip"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "timezone": data.get("timezone"),
                "isp": data.get("isp"),
                "organization": data.get("org"),
                "as_number": data.get("as"),
            }
    except Exception as e:
        return {"ip": ip, "error": str(e)}


async def port_scan(host: str, ports: list[int] | None = None, timeout: float = 2.0) -> dict:
    """Check if specified ports are open on a given host."""
    if ports is None:
        ports = [22, 80, 443, 3306, 5432, 8080]

    # Limit to 20 ports max for safety
    ports = ports[:20]
    results = []

    async def check_port(port: int) -> dict:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )
            writer.close()
            await writer.wait_closed()
            return {"port": port, "status": "open"}
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return {"port": port, "status": "closed"}

    tasks = [check_port(p) for p in ports]
    results = await asyncio.gather(*tasks)

    return {
        "host": host,
        "ports": sorted(results, key=lambda x: x["port"]),
        "open_count": sum(1 for r in results if r["status"] == "open"),
        "closed_count": sum(1 for r in results if r["status"] == "closed"),
    }


async def reverse_dns_lookup(ip: str) -> dict:
    """Perform a reverse DNS lookup on an IP address."""
    try:
        rev_name = dns.reversename.from_address(ip)
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        answers = resolver.resolve(rev_name, "PTR")
        hostnames = [str(rdata) for rdata in answers]
        return {
            "ip": ip,
            "hostnames": hostnames,
        }
    except dns.resolver.NXDOMAIN:
        return {"ip": ip, "error": "No reverse DNS record found"}
    except dns.resolver.Timeout:
        return {"ip": ip, "error": "Reverse DNS query timed out"}
    except Exception as e:
        return {"ip": ip, "error": str(e)}
