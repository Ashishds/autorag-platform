"""QueryService — synchronous FastPath chain (LLD §8.1). NOT LangGraph.

Chain: rewrite?* -> hybrid retrieve -> rerank (graceful) -> hyde?* -> generate
* rewrite and hyde are optional flags, off by default.
Context Compressor is deferred to Phase 2 (top-k reranked chunks go straight to the LLM).
"""

from __future__ import annotations

import time
import uuid
from uuid import UUID

from app.models import ScoredChunk
from app.repositories.chunk_repo import ChunkRepository
from app.retrieval.hybrid import hybrid_retrieve
from app.retrieval.hyde import maybe_hyde
from app.retrieval.reranker import rerank_graceful
from app.schemas.query import FlagMode, QueryRequest, QueryResult, QueryStages, Source, QueryMode
from app.services.embedding.base import BaseEmbeddingProvider
from app.services.llm.service import LLMService
from app.services.reranker.base import BaseReranker
from app.utils.citations import format_answer
from app.utils.text_normalize import normalize_extracted_text
from langfuse import observe, propagate_attributes


class QueryService:
    def __init__(
        self,
        llm: LLMService,
        embedder: BaseEmbeddingProvider,
        reranker: BaseReranker,
        chunk_repo: ChunkRepository,
        query_log_repo=None,
    ):
        self.llm = llm
        self.embedder = embedder
        self.reranker = reranker
        self.chunk_repo = chunk_repo
        self.query_log_repo = query_log_repo

    @observe()
    async def query(self, req: QueryRequest, organization_id: UUID = UUID(int=0)) -> QueryResult:
        with propagate_attributes(
            trace_name="Query FastPath",
            user_id=str(organization_id),
            metadata={"pipeline_id": str(req.pipeline_id), "mode": req.mode.value},
        ):
            if req.mode == QueryMode.agentic:
                return await self._agentic_query(req, organization_id)

            started = time.monotonic()
            stages = QueryStages()
            trace_id = uuid.uuid4()

            q = req.q
            if req.options.rewrite == FlagMode.on and not self._is_simple(q):
                q = await self._rewrite(q)
                stages.rewrite_applied = True

            # Multi-Query Expansion
            queries = [q]
            if req.options.multi_query == FlagMode.on:
                queries = await self._expand_queries(q)
                stages.multi_query_applied = True

            # Parallel retrieval
            import asyncio
            if len(queries) > 1:
                tasks = [
                    hybrid_retrieve(
                        query,
                        req.pipeline_id,
                        self.chunk_repo,
                        self.embedder,
                        metadata_filter=req.metadata_filter,
                    )
                    for query in queries
                ]
                results = await asyncio.gather(*tasks)
                # Deduplicate chunks
                seen = set()
                candidates = []
                for chunk_list in results:
                    for c in chunk_list:
                        if c.chunk_id not in seen:
                            seen.add(c.chunk_id)
                            candidates.append(c)
            else:
                candidates = await hybrid_retrieve(
                    q,
                    req.pipeline_id,
                    self.chunk_repo,
                    self.embedder,
                    metadata_filter=req.metadata_filter,
                )

            await self.chunk_repo.attach_metadata(candidates)
            top = await rerank_graceful(req.q, candidates, self.reranker, top_k=req.top_k)

            if req.options.hyde == FlagMode.on:
                before = len(top)
                top = await maybe_hyde(
                    req.q, req.pipeline_id, top, self.chunk_repo, self.embedder, self.llm
                )
                stages.hyde_applied = len(top) != before

            # Context Compressor deferred to Phase 2 — pass reranked chunks directly.
            answer = await self._generate(req.q, top)
            latency_ms = int((time.monotonic() - started) * 1000)

            if self.query_log_repo is not None:
                await self.query_log_repo.insert(
                    {
                        "q": req.q,
                        "pipeline_id": req.pipeline_id,
                        "organization_id": organization_id,
                        "trace_id": trace_id,
                        "rewrite_applied": stages.rewrite_applied,
                        "hyde_applied": stages.hyde_applied,
                        "retrieval_k": req.top_k,
                        "chunks_retrieved": len(candidates),
                        "rerank_applied": len(candidates) > 0,
                        "latency_ms": latency_ms,
                        "llm_provider": answer.provider,
                        "token_count": answer.token_count,
                    }
                )

            return QueryResult(
                answer=format_answer(answer.content, len(top)),
                sources=[
                    Source(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        filename=c.filename,
                        chunk_index=c.chunk_index,
                        page_number=c.page_number,
                        score=c.score or c.rrf_score,
                        content=normalize_extracted_text(c.content),
                        source_type=c.source_type,
                        media_path=c.media_path,
                    )
                    for c in top
                ],
                latency_ms=latency_ms,
                llm_provider=answer.provider,
                stages=stages,
            )

    @observe()
    async def _agentic_query(self, req: QueryRequest, organization_id: UUID) -> QueryResult:
        started = time.monotonic()
        stages = QueryStages(agentic_steps=0)
        trace_id = uuid.uuid4()

        # Initial search
        candidates = await hybrid_retrieve(
            req.q,
            req.pipeline_id,
            self.chunk_repo,
            self.embedder,
            metadata_filter=req.metadata_filter,
        )
        await self.chunk_repo.attach_metadata(candidates)
        top = await rerank_graceful(req.q, candidates, self.reranker, top_k=req.top_k)

        # Agent planning loop (max 2 steps)
        max_steps = 2
        for step in range(1, max_steps + 1):
            stages.agentic_steps = step
            context_text = "\n\n".join(
                [
                    f"[{i+1}] (file: {c.filename or 'unknown'}) {normalize_extracted_text(c.content)}"
                    for i, c in enumerate(top)
                ]
            )

            prompt = (
                "You are a retrieval planning agent.\n"
                "Based on the user query and the current retrieved context, do you have sufficient information to answer the question? "
                "Respond in JSON format with a decision:\n"
                "- If you have enough information, set decision='answer'.\n"
                "- If you need to search more, set decision='search' and provide a search_query.\n"
                "- If you need to read more chunks from a specific document, set decision='read' and provide the filename.\n\n"
                "JSON format:\n"
                '{"decision": "answer"|"search"|"read", "search_query": "...", "filename": "..."}\n\n'
                f"Query: {req.q}\n\n"
                f"Current Context:\n{context_text}"
            )

            resp = await self.llm.complete(
                [{"role": "user", "content": prompt}],
                model_preference="gemini-2.5-flash",
                response_schema={
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string"},
                        "search_query": {"type": "string"},
                        "filename": {"type": "string"},
                    },
                    "required": ["decision"],
                },
            )

            import json
            import re

            try:
                parsed = json.loads(re.search(r"\{.*\}", resp.content, re.DOTALL).group())
            except Exception:
                parsed = {"decision": "answer"}

            decision = parsed.get("decision", "answer")
            if decision == "search" and parsed.get("search_query"):
                new_q = parsed["search_query"]
                new_candidates = await hybrid_retrieve(
                    new_q,
                    req.pipeline_id,
                    self.chunk_repo,
                    self.embedder,
                    metadata_filter=req.metadata_filter,
                )
                await self.chunk_repo.attach_metadata(new_candidates)
                # Union & Deduplicate
                merged = {c.chunk_id: c for c in top}
                for c in new_candidates:
                    merged[c.chunk_id] = c
                top = await rerank_graceful(
                    req.q, list(merged.values()), self.reranker, top_k=req.top_k
                )
            elif decision == "read" and parsed.get("filename"):
                fn = parsed["filename"]
                doc_chunks = await self.chunk_repo.get_by_filename(req.pipeline_id, fn)
                await self.chunk_repo.attach_metadata(doc_chunks)
                # Union & Deduplicate
                merged = {c.chunk_id: c for c in top}
                for c in doc_chunks:
                    merged[c.chunk_id] = c
                top = await rerank_graceful(
                    req.q, list(merged.values()), self.reranker, top_k=req.top_k
                )
            else:
                break

        # Generate final answer
        answer = await self._generate(req.q, top)
        latency_ms = int((time.monotonic() - started) * 1000)

        if self.query_log_repo is not None:
            await self.query_log_repo.insert(
                {
                    "q": req.q,
                    "pipeline_id": req.pipeline_id,
                    "organization_id": organization_id,
                    "trace_id": trace_id,
                    "rewrite_applied": False,
                    "hyde_applied": False,
                    "retrieval_k": req.top_k,
                    "chunks_retrieved": len(top),
                    "rerank_applied": len(top) > 0,
                    "latency_ms": latency_ms,
                    "llm_provider": answer.provider,
                    "token_count": answer.token_count,
                }
            )

        return QueryResult(
            answer=format_answer(answer.content, len(top)),
            sources=[
                Source(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    filename=c.filename,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    score=c.score or c.rrf_score,
                    content=normalize_extracted_text(c.content),
                    source_type=c.source_type,
                    media_path=c.media_path,
                )
                for c in top
            ],
            latency_ms=latency_ms,
            llm_provider=answer.provider,
            stages=stages,
        )

    @staticmethod
    def _is_simple(q: str) -> bool:
        """Skip rewrite for short or already-clear queries (LLD §8.1)."""
        words = q.split()
        if len(words) <= 6:
            return True
        lower = q.lower().strip()
        clear_starters = (
            "what is",
            "what are",
            "how do",
            "how does",
            "how to",
            "why does",
            "when did",
            "where is",
            "who is",
            "explain",
            "describe",
            "list",
        )
        if any(lower.startswith(s) for s in clear_starters) and len(words) <= 14:
            return True
        # Long, multi-clause queries benefit from rewrite.
        return len(words) <= 8 and q.count(",") == 0 and q.count("?") <= 1

    @observe()
    async def _rewrite(self, q: str) -> str:
        resp = await self.llm.complete(
            [{"role": "user", "content": f"Rewrite this search query to be clearer: {q}"}],
            model_preference="gemini-2.5-flash",
        )
        return resp.content.strip() or q

    @observe()
    async def _expand_queries(self, q: str) -> list[str]:
        prompt = (
            "Generate 3 diverse search query variations (one per line, no numbering, no bullet points, no markdown formatting) "
            "to retrieve documents relevant to the following user question. These search queries should "
            "cover different facets or synonyms of the query to optimize retrieval.\n\n"
            f"User Question: {q}"
        )
        resp = await self.llm.complete(
            [{"role": "user", "content": prompt}],
            model_preference="gemini-2.5-flash",
        )
        queries = [line.strip() for line in resp.content.split("\n") if line.strip()]
        clean_queries = []
        for query in queries:
            query = query.lstrip("0123456789.-*• ")
            if query:
                clean_queries.append(query)
        if q not in clean_queries:
            clean_queries.insert(0, q)
        return clean_queries[:4]

    @observe()
    async def _generate(self, question: str, chunks: list[ScoredChunk]) -> LLMResponse:
        numbered = []
        for i, c in enumerate(chunks, start=1):
            content = normalize_extracted_text(c.content)
            numbered.append(f"[{i}] {content}")
        context = "\n\n".join(numbered)
        prompt = (
            "Answer the question using ONLY the numbered context below.\n"
            "Format rules:\n"
            "- Write a clear, structured answer in markdown (short paragraphs; use bullet "
            "lists when listing multiple points).\n"
            "- Do NOT start with phrases like 'Based on the provided context'.\n"
            "- Cite sources ONLY with bracket notation: [1], [2], or [1][5]. "
            "Never use bare numbers (e.g. 5 or 15) for citations.\n"
            "- Valid source numbers are 1 through N only.\n"
            "- If the answer is not present, say you don't know.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}"
        )
        return await self.llm.complete(
            [{"role": "user", "content": prompt}], model_preference="gemini-2.5-flash"
        )
