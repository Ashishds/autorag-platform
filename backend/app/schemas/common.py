"""Standard response wrapper (LLD §6.1)."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class APIResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: T | None = None
    error: ErrorDetail | None = None
    request_id: UUID = Field(default_factory=uuid4)

    @classmethod
    def ok(cls, data: T) -> APIResponse[T]:
        return cls(status="success", data=data)

    @classmethod
    def fail(cls, code: str, message: str, details: dict | None = None) -> APIResponse[None]:
        return cls(
            status="error",
            error=ErrorDetail(code=code, message=message, details=details or {}),
        )
