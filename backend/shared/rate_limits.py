"""
Paciolus API — Rate Limiting Configuration

Sprint 279: Custom key_func that only trusts X-Forwarded-For from
configured proxy IPs, preventing rate-limit bypass via header spoofing.
"""
from slowapi import Limiter
from starlette.requests import Request


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP for rate limiting.

    Trusts X-Forwarded-For ONLY when the direct peer is in TRUSTED_PROXY_IPS.
    Falls back to the direct socket address otherwise.
    """
    from config import TRUSTED_PROXY_IPS

    peer_ip = request.client.host if request.client else "127.0.0.1"

    if TRUSTED_PROXY_IPS and peer_ip in TRUSTED_PROXY_IPS:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First entry is the original client
            return forwarded.split(",")[0].strip()

    return peer_ip


limiter = Limiter(key_func=_get_client_ip, default_limits=["60/minute"])

RATE_LIMIT_AUDIT = "10/minute"
RATE_LIMIT_AUTH = "5/minute"
RATE_LIMIT_EXPORT = "20/minute"
RATE_LIMIT_WRITE = "30/minute"
RATE_LIMIT_DEFAULT = "60/minute"
