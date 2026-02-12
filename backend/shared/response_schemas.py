"""
Paciolus API — Shared Response Models
Phase XIX: API Contract Hardening
"""
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Standard success response for mutations that return a confirmation."""
    success: bool
    message: str


class ClearResponse(SuccessResponse):
    """Response for bulk-clear operations that report deleted count."""
    deleted_count: int
