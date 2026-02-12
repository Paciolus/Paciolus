"""
Paciolus API — Rate Limiting Configuration
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

RATE_LIMIT_AUDIT = "10/minute"
RATE_LIMIT_AUTH = "5/minute"
RATE_LIMIT_EXPORT = "20/minute"
RATE_LIMIT_DEFAULT = "60/minute"
