"""Audit log route — read-only listing (INSERT-only table)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.schemas.common import APIResponse

router = APIRouter()


@router.get("")
async def list_audit(organization_id: UUID):
    return APIResponse.fail("ERR_NOT_IMPLEMENTED", "audit list not implemented yet")
