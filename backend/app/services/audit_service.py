"""AuditService — INSERT-ONLY audit log (LLD §9.7)."""

from __future__ import annotations

from uuid import UUID

PII_KEYS = {"email", "phone", "ssn", "aadhaar", "credit_card", "ip", "query", "content"}


class AuditService:
    ALLOWED_EVENTS = {
        "PIPELINE_CREATED",
        "PIPELINE_UPDATED",
        "INGESTION_STARTED",
        "INGESTION_COMPLETED",
        "DOCUMENT_STATUS_CHANGED",
        "EVALUATION_STARTED",
        "EVALUATION_COMPLETED",
        "IMPROVEMENT_TRIGGERED",
        "APPROVAL_GRANTED",
        "APPROVAL_DENIED",
        "PIPELINE_DEPLOYED",
        "PIPELINE_ROLLED_BACK",
    }

    def __init__(self, audit_repo=None):
        self._repo = audit_repo

    async def log(
        self,
        organization_id: UUID,
        event_type: str,
        actor_id: UUID,
        resource_type: str,
        resource_id: UUID,
        trace_id: UUID,
        payload: dict | None = None,
    ) -> UUID | None:
        assert event_type in self.ALLOWED_EVENTS, f"unknown audit event: {event_type}"
        clean = self._strip_pii(payload or {})
        if self._repo is None:
            return None
        return await self._repo.insert(
            organization_id=organization_id,
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            trace_id=trace_id,
            payload=clean,
        )

    @staticmethod
    def _strip_pii(payload: dict) -> dict:
        return {k: v for k, v in payload.items() if k.lower() not in PII_KEYS}
