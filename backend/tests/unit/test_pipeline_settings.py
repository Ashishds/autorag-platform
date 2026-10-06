from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models import ApprovalTier
from app.services.approval_service import ApprovalService
from app.services.pipeline_service import PipelineService
from app.schemas.pipeline import PipelineUpdate, ChunkingStrategy, RetrievalMethod, ApprovalMode


def test_approval_policy_auto_override():
    service = ApprovalService()
    baseline = {"top_k": 5, "llm_judge": "gemini-2.5-pro"}
    
    # Normally changing LLM judge is mandatory_gate (high risk)
    variant_high_risk = {"top_k": 5, "llm_judge": "gpt-4o"}
    tier_default = service.classify_tier(variant_high_risk, baseline, approval_mode="human_in_loop")
    assert tier_default == ApprovalTier.MANDATORY_GATE
    
    # With approval_mode = "auto", it should be AUTO immediately
    tier_auto = service.classify_tier(variant_high_risk, baseline, approval_mode="auto")
    assert tier_auto == ApprovalTier.AUTO


def test_approval_policy_mandatory_gate_override():
    service = ApprovalService()
    baseline = {"top_k": 5, "llm_judge": "gemini-2.5-pro"}
    
    # Normally changing top_k is AUTO (low risk)
    variant_low_risk = {"top_k": 10, "llm_judge": "gemini-2.5-pro"}
    tier_default = service.classify_tier(variant_low_risk, baseline, approval_mode="human_in_loop")
    assert tier_default == ApprovalTier.AUTO
    
    # With approval_mode = "mandatory_gate", it should be MANDATORY_GATE immediately
    tier_gate = service.classify_tier(variant_low_risk, baseline, approval_mode="mandatory_gate")
    assert tier_gate == ApprovalTier.MANDATORY_GATE


def test_approval_policy_human_in_loop_default():
    service = ApprovalService()
    baseline = {"top_k": 5, "llm_judge": "gemini-2.5-pro"}
    
    # Low risk -> AUTO
    variant_low = {"top_k": 10, "llm_judge": "gemini-2.5-pro"}
    assert service.classify_tier(variant_low, baseline, "human_in_loop") == ApprovalTier.AUTO
    
    # High risk -> MANDATORY_GATE
    variant_high = {"top_k": 5, "llm_judge": "gpt-4o"}
    assert service.classify_tier(variant_high, baseline, "human_in_loop") == ApprovalTier.MANDATORY_GATE


@pytest.mark.asyncio
async def test_pipeline_service_update():
    mock_repo = MagicMock()
    mock_repo.update = AsyncMock(return_value={"id": "pipeline-uuid", "name": "New Name"})
    
    mock_audit = MagicMock()
    mock_audit.log = AsyncMock()
    
    service = PipelineService(pipeline_repo=mock_repo, audit=mock_audit)
    
    update_data = PipelineUpdate(
        name="New Name",
        approval_mode=ApprovalMode.auto,
    )
    
    p_id = uuid4()
    actor_id = uuid4()
    org_id = uuid4()
    
    res = await service.update(p_id, update_data, actor_id, org_id)
    
    assert res is not None
    assert res["name"] == "New Name"
    mock_repo.update.assert_called_once_with(
        p_id,
        {"name": "New Name", "approval_mode": "auto"}
    )
    mock_audit.log.assert_called_once()
