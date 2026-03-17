"""
Shared Pagination Utilities — Sprint 544.

Generic PaginatedResponse[T] and PaginationParams dependency
for consistent list endpoints across all routes.
"""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response.

    All list endpoints return this shape:
    - items: list of domain objects
    - total_count: total matching records (for pagination controls)
    - page: current page number (1-indexed)
    - page_size: items per page
    """

    items: list[T]
    total_count: int
    page: int
    page_size: int


class PaginationParams:
    """FastAPI dependency for pagination query parameters.

    Usage::

        @router.get("/things")
        def list_things(pagination: PaginationParams = Depends()):
            offset = pagination.offset
            ...
    """

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """Compute SQL offset from page and page_size."""
        return (self.page - 1) * self.page_size
