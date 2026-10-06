from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.chunkers.semantic import SemanticChunker
from app.chunkers.hierarchical import HierarchicalChunker
from app.models import Chunk, ChunkStrategy, ScoredChunk, LLMResponse
from app.parsers.base import DocumentBlock
from app.services.query_service import QueryService
from app.schemas.query import QueryRequest, QueryOptions, FlagMode, QueryMode


def test_table_aware_chunking_semantic():
    chunker = SemanticChunker(target_tokens=100)
    blocks = [
        DocumentBlock(type="text", content="Paragraph one content that is relatively short.", page_number=1),
        DocumentBlock(
            type="table",
            content="| Col 1 | Col 2 |\n|---|---|\n| Value 1 | Value 2 |",
            page_number=2,
            metadata={"source": "table_extract"},
        ),
        DocumentBlock(type="text", content="Paragraph two content after table.", page_number=3),
    ]

    chunks = chunker.chunk(blocks)
    
    # We expect at least 3 chunks
    assert len(chunks) >= 3
    # Check that table block was kept intact as a table source_type chunk
    table_chunks = [c for c in chunks if c.source_type == "table"]
    assert len(table_chunks) == 1
    assert table_chunks[0].content == "| Col 1 | Col 2 |\n|---|---|\n| Value 1 | Value 2 |"
    assert table_chunks[0].page_number == 2
    assert table_chunks[0].metadata == {"source": "table_extract"}
    
    # Check text chunks
    text_chunks = [c for c in chunks if c.source_type == "text"]
    assert len(text_chunks) >= 2
    assert text_chunks[0].page_number == 1
    assert text_chunks[-1].page_number == 3


def test_table_aware_chunking_hierarchical():
    chunker = HierarchicalChunker(parent_tokens=100, child_tokens=20)
    blocks = [
        DocumentBlock(type="text", content="Short paragraph text content here.", page_number=1),
        DocumentBlock(
            type="table",
            content="| A | B |\n|---|---|\n| 1 | 2 |",
            page_number=2,
        ),
    ]

    chunks = chunker.chunk(blocks)
    assert len(chunks) >= 2
    
    table_chunks = [c for c in chunks if c.source_type == "table"]
    assert len(table_chunks) == 1
    assert table_chunks[0].strategy == ChunkStrategy.HIERARCHICAL_PARENT
    assert table_chunks[0].page_number == 2


@pytest.mark.asyncio
async def test_multi_query_expansion():
    # Mock LLM response for query expansion
    mock_llm = MagicMock()
    mock_llm.complete = AsyncMock(
        return_value=LLMResponse(
            content="first sub query\nsecond sub query\nthird sub query",
            provider="gemini-2.5-flash",
        )
    )

    query_svc = QueryService(
        llm=mock_llm,
        embedder=MagicMock(),
        reranker=MagicMock(),
        chunk_repo=MagicMock(),
    )

    expanded = await query_svc._expand_queries("How to deploy?")
    # Original query is inserted first, followed by up to 3 variations
    assert len(expanded) == 4
    assert expanded[0] == "How to deploy?"
    assert expanded[1] == "first sub query"
    assert expanded[2] == "second sub query"
    assert expanded[3] == "third sub query"


@pytest.mark.asyncio
async def test_agentic_query_answer_decision():
    mock_llm = MagicMock()
    # First complete decides to answer directly
    mock_llm.complete = AsyncMock(
        side_effect=[
            # step 1 planning decision
            LLMResponse(
                content='{"decision": "answer"}',
                provider="gemini-2.5-flash",
            ),
            # final generation answer
            LLMResponse(
                content="This is the answer from the context.",
                provider="gemini-2.5-flash",
                token_count=15,
            )
        ]
    )

    mock_embedder = MagicMock()
    mock_embedder.embed_one = AsyncMock(return_value=[0.1] * 768)

    mock_chunk_repo = MagicMock()
    mock_chunk_repo.hybrid_search = AsyncMock(
        return_value=[
            ScoredChunk(chunk_id=uuid4(), content="some database content", rrf_score=0.9)
        ]
    )
    mock_chunk_repo.attach_metadata = AsyncMock()

    mock_reranker = MagicMock()
    mock_reranker.rerank = AsyncMock(
        return_value=[
            ScoredChunk(chunk_id=uuid4(), content="some database content", rrf_score=0.9, score=0.95)
        ]
    )

    query_svc = QueryService(
        llm=mock_llm,
        embedder=mock_embedder,
        reranker=mock_reranker,
        chunk_repo=mock_chunk_repo,
    )

    req = QueryRequest(
        pipeline_id=uuid4(),
        q="test query",
        mode=QueryMode.agentic,
    )

    res = await query_svc.query(req)
    assert "This is the answer" in res.answer
    assert res.stages.agentic_steps == 1


@pytest.mark.asyncio
async def test_youtube_parser_segmentation():
    from app.parsers.youtube import YouTubeParser
    import json

    mock_segments = [
        {"text": "hello and welcome to AutoRAG tutorial.", "start": 10.0, "duration": 5.0},
        {"text": "Today we will see how to ingest youtube transcripts.", "start": 15.0, "duration": 4.0},
    ]
    file_bytes = json.dumps(mock_segments).encode("utf-8")

    parser = YouTubeParser()
    blocks = await parser.parse(file_bytes, "youtube_dQw4w9WgXcQ.youtube")

    assert len(blocks) == 1
    block = blocks[0]
    assert block.type == "text"
    assert "[00:10 - 00:19]" in block.content
    assert "hello and welcome to AutoRAG tutorial." in block.content
    assert block.media_path == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
    assert block.metadata["video_id"] == "dQw4w9WgXcQ"
    assert block.metadata["start_seconds"] == 10.0
    assert block.metadata["source"] == "youtube"
