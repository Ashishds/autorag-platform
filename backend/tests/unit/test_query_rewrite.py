"""Query rewrite heuristic tests."""

from app.services.query_service import QueryService


def test_short_queries_skip_rewrite():
    assert QueryService._is_simple("What is AutoRAG?")


def test_long_vague_queries_need_rewrite():
    q = (
        "Can you tell me everything about the optimization loop "
        "and how it improves pipelines over time?"
    )
    assert not QueryService._is_simple(q)


def test_clear_starter_queries_skip_rewrite():
    assert QueryService._is_simple("What is the primary model used for completions?")
