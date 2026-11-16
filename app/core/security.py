import hmac
import ipaddress
import logging
from typing import Iterable, List, Optional, Union

from fastapi import Request, HTTPException
from app.core.config import settings

logger = logging.getLogger("saraburi_agent.security")

IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


def _parse_networks(raw_values: Iterable[Optional[str]], setting_name: str) -> List[IPNetwork]:
    """
    Parse comma-separated IPs / CIDR ranges. Inline comments ("1.2.3.4 #note") are dropped
    and invalid entries are logged and skipped, so a typo never crashes the agent.
    """
    networks: List[IPNetwork] = []
    for raw in raw_values:
        if not raw:
            continue
        for token in str(raw).split(","):
            token = token.split("#", 1)[0].strip()
            if not token:
                continue
            try:
                networks.append(ipaddress.ip_network(token, strict=False))
            except ValueError:
                logger.warning(f"{setting_name}: ignoring invalid IP/CIDR '{token}'")
    return networks


ALLOWED_NETWORKS = _parse_networks(
    [settings.API_ALLOWED_IPS, settings.API_ALLOWED_IP1, settings.API_ALLOWED_IP2],
    "API_ALLOWED_IPS",
)
TRUSTED_PROXY_NETWORKS = _parse_networks([settings.TRUSTED_PROXIES], "TRUSTED_PROXIES")

if not ALLOWED_NETWORKS:
    logger.warning("No valid allowed IPs configured (API_ALLOWED_IPS / API_ALLOWED_IP1 / API_ALLOWED_IP2): every request will get 403")


def _to_ip(value: Optional[str]) -> Optional[IPAddress]:
    if not value:
        return None
    try:
        ip = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip


def _in_networks(value: Optional[str], networks: List[IPNetwork]) -> bool:
    ip = _to_ip(value)
    return ip is not None and any(ip in net for net in networks)


def get_client_ip(request: Request) -> str:
    peer = request.client.host if request.client else None
    xff = request.headers.get("x-forwarded-for")

    # X-Forwarded-For can be typed by anyone, so it only counts when the request came
    # through a trusted reverse proxy. Proxies append to the right, so walk from the right
    # and take the first hop that is not one of our proxies.
    if xff and peer and _in_networks(peer, TRUSTED_PROXY_NETWORKS):
        hops = [h.strip() for h in xff.split(",") if h.strip()]
        for hop in reversed(hops):
            if not _in_networks(hop, TRUSTED_PROXY_NETWORKS):
                return hop
        if hops:
            return hops[0]

    return peer or "unknown"


def _verify_ip_and_key(request: Request) -> None:
    # 1. IP Address
    client_ip = get_client_ip(request)
    if not _in_networks(client_ip, ALLOWED_NETWORKS):
        raise HTTPException(status_code=403, detail=f"IP {client_ip} is not allowed")

    # 2. API Key
    x_api_key = request.headers.get("x-api-key")
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY header")
    if not hmac.compare_digest(x_api_key.encode("utf-8"), settings.API_KEY.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Invalid API Key")


async def api_security(request: Request, body_hospcode: str):
    """Security check for endpoints that carry hospcode in the JSON body."""
    _verify_ip_and_key(request)

    hospcode_header = request.headers.get("x-hospcode")
    if hospcode_header != body_hospcode:
        raise HTTPException(status_code=400, detail="Hospcode mismatch")
    if settings.HOSP_CODE != body_hospcode:
        raise HTTPException(status_code=400, detail="Hospcode not allowed")
    return True


async def api_security_header(request: Request):
    """Security check for endpoints without a body (headers only)."""
    _verify_ip_and_key(request)

    hospcode_header = request.headers.get("x-hospcode")
    if hospcode_header is None:
        raise HTTPException(status_code=400, detail="Missing X-Hospcode header")
    if hospcode_header != settings.HOSP_CODE:
        raise HTTPException(status_code=400, detail="Hospcode not allowed")
    return True


def is_authorized(request: Request) -> bool:
    """True when the request passes the header-only check. Never raises."""
    try:
        _verify_ip_and_key(request)
    except HTTPException:
        return False
    return request.headers.get("x-hospcode") == settings.HOSP_CODE
