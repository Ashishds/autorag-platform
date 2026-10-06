"""Adversarial fixed-anchor tests — must pass at 100% to deploy (LLD §9.5)."""

import pytest

from app.constants import FIXED_ADVERSARIAL_ANCHORS, REFUSAL_PHRASES
from app.services.evaluation_service import EvaluationService


@pytest.mark.parametrize(
    "answer",
    [
        "I don't know based on the provided context.",
        "The answer is not present in the documents.",
        "I cannot answer that question.",
        "There is no information about that.",
        "I'm unable to find this in the context.",
    ],
)
def test_refusal_phrases_are_detected(answer: str):
    assert EvaluationService._is_refusal(answer)


@pytest.mark.parametrize(
    "answer",
    [
        "The CEO announced record revenue in Q3 2024.",
        "John Smith joined the company in 2015.",
    ],
)
def test_factual_answers_are_not_refusals(answer: str):
    assert not EvaluationService._is_refusal(answer)


def test_fixed_adversarial_anchor_set_has_five_questions():
    assert len(FIXED_ADVERSARIAL_ANCHORS) == 5
    assert all(isinstance(q, str) and q for q in FIXED_ADVERSARIAL_ANCHORS)


def test_refusal_phrases_are_non_empty():
    assert len(REFUSAL_PHRASES) >= 5
