"""SSRF guard for server-side URL fetching.

Blocks private, loopback, link-local, multicast, and reserved addresses, plus
known cloud-metadata and local hostnames. Hostnames are DNS-resolved so a name
that points at an internal IP is rejected, not just literal private IPs.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket
import urllib.parse
from typing import Any

RESERVED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
}
RESOLVE_TIMEOUT = 2.0
IPv4Address = ipaddress.IPv4Address
IPv6Address = ipaddress.IPv6Address


def _is_blocked_ip(ip: IPv4Address | IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
    )


def is_blocked_host_literal(host: str) -> bool | None:
    """Classify a literal IP; returns None when ``host`` is not an IP literal."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None
    return _is_blocked_ip(ip)


async def _resolve_host_ips(host: str) -> list[IPv4Address | IPv6Address]:
    """Resolve a hostname to IPs without blocking the event loop."""
    try:
        loop = asyncio.get_running_loop()
        addrinfo = await asyncio.wait_for(loop.getaddrinfo(host, None), RESOLVE_TIMEOUT)
    except Exception:
        return []
    ips: list[IPv4Address | IPv6Address] = []
    for entry in addrinfo:
        try:
            sockaddr = entry[4][0] if isinstance(entry, tuple) and len(entry) >= 5 else None
            if sockaddr:
                ips.append(ipaddress.ip_address(sockaddr))
        except (ValueError, IndexError, TypeError):
            continue
    return ips


async def is_private_host(host: str) -> bool:
    """Return True when ``host`` (hostname or IP literal) is internal.

    Literal IPs are classified directly. Hostnames are DNS-resolved and
    rejected if any resolved address is private/loopback/link-local/
    multicast/reserved. Fail closed when resolution fails.
    """
    host = (host or "").strip().lower().rstrip(".")
    if not host:
        return True
    if host in RESERVED_HOSTNAMES:
        return True

    literal = is_blocked_host_literal(host)
    if literal is not None:
        return literal

    resolved = await _resolve_host_ips(host)
    if not resolved:
        return True
    return any(_is_blocked_ip(ip) for ip in resolved)


async def is_private_url(url: str) -> bool:
    """Return True when the URL targets internal infrastructure."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return True
    if (parsed.scheme or "").lower() not in ("http", "https"):
        return True
    return await is_private_host(parsed.hostname or "")


def is_private_url_sync(url: str) -> bool:
    """Synchronous variant for non-async callers and tests."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return True
    if (parsed.scheme or "").lower() not in ("http", "https"):
        return True
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host or host in RESERVED_HOSTNAMES:
        return True
    literal = is_blocked_host_literal(host)
    if literal is not None:
        return literal
    try:
        resolved = socket.getaddrinfo(host, None)
    except Exception:
        return True
    for entry in resolved:
        try:
            sockaddr = entry[4][0] if isinstance(entry, tuple) and len(entry) >= 5 else None
            if sockaddr and _is_blocked_ip(ipaddress.ip_address(sockaddr)):
                return True
        except (ValueError, IndexError, TypeError):
            continue
    return False