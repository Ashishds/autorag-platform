"""GoldenSetService — generate-once, frozen static Q&A set (LLD §3.5, §8.3)."""

from __future__ import annotations

import json
import re
from uuid import UUID

from app.constants import FIXED_ADVERSARIAL_ANCHORS, GOLDEN_SYNTHETIC_COUNT
from app.models import GoldenQA


class GoldenSetService:
    def __init__(self, golden_repo=None, chunk_repo=None, llm=None):
        self._repo = golden_repo
        self._chunk_repo = chunk_repo
        self._llm = llm

    async def get_or_create_static_set(
        self, pipeline_id: UUID, organization_id: UUID
    ) -> tuple[list[GoldenQA], UUID]:
        """Return the frozen golden set; generate + persist once if absent."""
        existing = await self._repo.get_for_pipeline(pipeline_id)
        if existing:
            qas = [
                GoldenQA(
                    id=UUID(str(row["id"])),
                    question=row["question"],
                    expected_answer=row.get("expected_answer"),
                    expected_chunks=[UUID(str(c)) for c in (row.get("expected_chunks") or [])],
                    question_type=row.get("question_type", "synthetic"),
                )
                for row in existing
            ]
            golden_set_id = UUID(str(existing[0]["id"]))
            return qas, golden_set_id

        chunks = await self._chunk_repo.sample_for_pipeline(
            pipeline_id, limit=GOLDEN_SYNTHETIC_COUNT
        )
        if not chunks:
            raise ValueError("No chunks indexed for pipeline — ingest documents first")

        rows: list[dict] = []
        for chunk in chunks:
            qa = await self._generate_qa_from_chunk(chunk["content"])
            rows.append(
                {
                    "pipeline_id": pipeline_id,
                    "organization_id": organization_id,
                    "question": qa["question"],
                    "expected_answer": qa["expected_answer"],
                    "expected_chunks": [chunk["id"]],
                    "question_type": "synthetic",
                    "set_version": 1,
                }
            )

        for question in FIXED_ADVERSARIAL_ANCHORS:
            rows.append(
                {
                    "pipeline_id": pipeline_id,
                    "organization_id": organization_id,
                    "question": question,
                    "expected_answer": None,
                    "expected_chunks": [],
                    "question_type": "adversarial_fixed",
                    "set_version": 1,
                }
            )

        await self._repo.bulk_insert(rows)
        persisted = await self._repo.get_for_pipeline(pipeline_id)
        qas = [
            GoldenQA(
                id=UUID(str(row["id"])),
                question=row["question"],
                expected_answer=row.get("expected_answer"),
                expected_chunks=[UUID(str(c)) for c in (row.get("expected_chunks") or [])],
                question_type=row.get("question_type", "synthetic"),
            )
            for row in persisted
        ]
        golden_set_id = UUID(str(persisted[0]["id"]))
        return qas, golden_set_id

    async def _generate_qa_from_chunk(self, content: str) -> dict[str, str]:
        prompt = (
            "Given this text chunk, generate ONE factual question answerable ONLY from this "
            "text and its expected answer.\n\n"
            f"Chunk:\n{content[:2000]}\n\n"
            'Respond as JSON only: {"question": "...", "expected_answer": "..."}'
        )
        resp = await self._llm.complete(
            [{"role": "user", "content": prompt}],
            model_preference="gemini-2.5-flash",
        )
        parsed = self._parse_json(resp.content)
        if parsed:
            return parsed
        return {
            "question": f"What information is provided in: {content[:80]}...?",
            "expected_answer": content[:200],
        }

    @staticmethod
    def _parse_json(text: str) -> dict[str, str] | None:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            if "question" in data:
                return {
                    "question": str(data["question"]),
                    "expected_answer": str(data.get("expected_answer", "")),
                }
        except json.JSONDecodeError:
            return None
        return None
