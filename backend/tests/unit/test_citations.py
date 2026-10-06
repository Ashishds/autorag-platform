"""Tests for answer citation normalization."""

from app.utils.citations import format_answer, normalize_answer_citations, strip_answer_boilerplate


def test_strip_boilerplate():
    assert strip_answer_boilerplate("Based on the provided context, the Transformer is...").startswith(
        "The Transformer"
    )


def test_bare_single_digit_citation():
    assert normalize_answer_citations("allows parallelization 5.", max_source=5) == (
        "allows parallelization [5]."
    )


def test_bare_multi_digit_citation():
    assert normalize_answer_citations("dependencies between them 15.", max_source=5) == (
        "dependencies between them [1][5]."
    )


def test_leaves_non_citation_numbers():
    assert normalize_answer_citations("trained for 12 hours.", max_source=5) == "trained for 12 hours."


def test_format_answer_combined():
    raw = "Based on the provided context, the model uses attention 1."
    assert format_answer(raw, max_source=3) == "The model uses attention [1]."
