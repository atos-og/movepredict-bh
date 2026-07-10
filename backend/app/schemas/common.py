from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    data: T


class PageMeta(BaseModel):
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class PageResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PageMeta


class StatusData(BaseModel):
    status: str
    service: str | None = None
    version: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
