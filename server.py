#!/usr/bin/env python3
"""
IP Geolocation MCP Server

Provides IP geolocation data via ipinfo.io (free tier, no API key needed).
Tools:
  - ip_lookup(ip)     — Lookup a specific IP address
  - ip_lookup_own()   — Lookup your own public IP
  - ip_batch(ips)     — Batch lookup up to 10 IPs at once

Pricing: $19/month — https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m
"""

from __future__ import annotations

import httpx
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ServerResult
import mcp.server.stdio

# ── Constants ────────────────────────────────────────────────────────────────

BASE_URL = "https://ipinfo.io"
MAX_BATCH = 10
SERVERS = [server for server in [Server("ip-geolocation")] if True][0]

# ── HTTP client (lazy-init) ─────────────────────────────────────────────────

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Accept": "application/json"},
            timeout=15.0,
        )
    return _client


async def _cleanup():
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_location(loc: str | None) -> dict:
    """Parse 'lat,lon' string into a dict."""
    if not loc:
        return {"latitude": None, "longitude": None}
    parts = loc.split(",")
    if len(parts) != 2:
        return {"latitude": None, "longitude": None}
    try:
        return {"latitude": float(parts[0]), "longitude": float(parts[1])}
    except ValueError:
        return {"latitude": None, "longitude": None}


def _format_ip_data(data: dict) -> dict:
    """Normalize ipinfo.io response into a clean geolocation object."""
    loc = _format_location(data.get("loc"))
    return {
        "ip": data.get("ip", ""),
        "city": data.get("city", ""),
        "region": data.get("region", ""),
        "country": data.get("country", ""),
        "org": data.get("org", ""),
        "timezone": data.get("timezone", ""),
        "postal": data.get("postal", ""),
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "loc": data.get("loc", ""),
    }


# ── MCP Tool Implementations ────────────────────────────────────────────────

async def ip_lookup(ip: str) -> list[TextContent]:
    """Lookup geolocation data for a specific IP address."""
    client = await _get_client()
    try:
        resp = await client.get(f"/{ip}/json")
        resp.raise_for_status()
        data = resp.json()
        formatted = _format_ip_data(data)
        return [TextContent(type="text", text=str(formatted))]
    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"HTTP error {e.response.status_code}: {e.response.text}")]
    except httpx.RequestError as e:
        return [TextContent(type="text", text=f"Request failed: {e}")]


async def ip_lookup_own() -> list[TextContent]:
    """Lookup geolocation data for the server's own public IP."""
    client = await _get_client()
    try:
        resp = await client.get("/json")
        resp.raise_for_status()
        data = resp.json()
        formatted = _format_ip_data(data)
        return [TextContent(type="text", text=str(formatted))]
    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"HTTP error {e.response.status_code}: {e.response.text}")]
    except httpx.RequestError as e:
        return [TextContent(type="text", text=f"Request failed: {e}")]


async def ip_batch(ips: list[str]) -> list[TextContent]:
    """Batch lookup geolocation data for up to 10 IPs.

    Uses ipinfo.io's /batch endpoint with a comma-separated list.
    """
    if len(ips) > MAX_BATCH:
        return [
            TextContent(
                type="text",
                text=f"Error: Maximum {MAX_BATCH} IPs per batch request (got {len(ips)})",
            )
        ]
    client = await _get_client()
    try:
        resp = await client.post("/batch", json=ips)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for ip, info in data.items():
            if info is None:
                results.append({"ip": ip, "error": "No data available"})
            else:
                results.append(_format_ip_data(info))
        return [TextContent(type="text", text=str(results))]
    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"HTTP error {e.response.status_code}: {e.response.text}")]
    except httpx.RequestError as e:
        return [TextContent(type="text", text=f"Request failed: {e}")]


# ── MCP Server Setup ─────────────────────────────────────────────────────────

@servers.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="ip_lookup",
            description="Look up geolocation data for a specific IP address (city, region, country, org, timezone, lat/lon, postal code)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ip": {
                        "type": "string",
                        "description": "IP address to look up (e.g. '8.8.8.8' or '2001:4860:4860::8888')",
                    }
                },
                "required": ["ip"],
            },
        ),
        Tool(
            name="ip_lookup_own",
            description="Get geolocation data for your own public IP address (no arguments needed)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="ip_batch",
            description=f"Batch lookup up to {MAX_BATCH} IP addresses at once. Returns geolocation data for each IP.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ips": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": f"List of IP addresses to look up (max {MAX_BATCH})",
                    }
                },
                "required": ["ips"],
            },
        ),
    ]


@servers.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "ip_lookup":
        return await ip_lookup(arguments["ip"])
    elif name == "ip_lookup_own":
        return await ip_lookup_own()
    elif name == "ip_batch":
        return await ip_batch(arguments["ips"])
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ── Lifecycle hooks ──────────────────────────────────────────────────────────

@servers.shutdown()
async def handle_shutdown() -> None:
    await _cleanup()


# ── Entrypoint ───────────────────────────────────────────────────────────────

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await servers.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ip-geolocation",
                server_version="1.0.0",
                capabilities=servers.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
