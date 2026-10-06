"""Tier-1 PII masking tests."""

import pytest

from app.services.pii.service import TieredPIIService


@pytest.mark.asyncio
async def test_masks_email_and_ip():
    svc = TieredPIIService()
    masked, n = await svc.mask("contact me at jane.doe@example.com from 192.168.1.10")
    assert "[EMAIL]" in masked
    assert "[IP]" in masked
    assert n >= 2
