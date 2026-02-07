from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(..., alias="page")
    limit: int = Field(..., alias="limit")
    total_items: int = Field(..., alias="totalItems")
    total_pages: int = Field(..., alias="totalPages")
    has_next_page: bool = Field(..., alias="hasNextPage")
    has_previous_page: bool = Field(..., alias="hasPreviousPage")


class PaginatedResponseDto(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)

    data: list[T] = Field(..., alias="data")
    pagination: PaginationDto = Field(..., alias="pagination")


class ErrorResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error: str = Field(..., alias="error")
    message: str = Field(..., alias="message")
    status_code: int = Field(..., alias="statusCode")
    timestamp: datetime = Field(..., alias="timestamp")
    path: str = Field(..., alias="path")
