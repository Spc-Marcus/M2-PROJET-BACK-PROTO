from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationInfo


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    timestamp: datetime
    path: str


def create_pagination(page: int, limit: int, total_items: int) -> PaginationInfo:
    """Helper to create pagination info."""
    total_pages = (total_items + limit - 1) // limit if limit > 0 else 0
    return PaginationInfo(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        has_next_page=page < total_pages,
        has_previous_page=page > 1
    )
