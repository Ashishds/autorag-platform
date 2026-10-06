"""EvaluationRepository (LLD §3.4)."""

from __future__ import annotations

from uuid import UUID

from app.repositories.base import SupabaseRepository


class EvaluationRepository(SupabaseRepository):
    TABLE = "evaluations"

    async def insert(self, row: dict) -> dict:
        if self.client is not None:
            payload = {
                "run_id": str(row["run_id"]),
                "organization_id": str(row["organization_id"]),
                "golden_set_id": str(row["golden_set_id"]),
                "unified_score": row["unified_score"],
                "retrieval_score": row["retrieval_score"],
                "quality_score": row["quality_score"],
                "faithfulness_score": row["faithfulness_score"],
                "latency_penalty": row.get("latency_penalty", 0),
                "cost_penalty": row.get("cost_penalty", 0),
                "ragas_context_precision": row.get("ragas_context_precision"),
                "ragas_context_recall": row.get("ragas_context_recall"),
                "ragas_answer_faithfulness": row.get("ragas_answer_faithfulness"),
                "ragas_answer_relevancy": row.get("ragas_answer_relevancy"),
                "ragas_scorer": row.get("ragas_scorer"),
                "adversarial_pass_rate": row.get("adversarial_pass_rate"),
                "adversarial_fail_count": row.get("adversarial_fail_count", 0),
                "adversarial_dynamic_count": row.get("adversarial_dynamic_count", 5),
                "deploy_eligible": row.get("deploy_eligible", False),
                "failure_reason": row.get("failure_reason"),
                "judge_reasoning": row.get("judge_reasoning"),
                "eval_duration_ms": row.get("eval_duration_ms"),
            }
            res = await self.client.table(self.TABLE).insert(payload).execute()
            return res.data[0]

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                INSERT INTO evaluations
                    (run_id, organization_id, golden_set_id, unified_score,
                     retrieval_score, quality_score, faithfulness_score,
                     latency_penalty, cost_penalty,
                     ragas_context_precision, ragas_context_recall,
                     ragas_answer_faithfulness, ragas_answer_relevancy,
                     ragas_scorer, adversarial_pass_rate, adversarial_fail_count,
                     adversarial_dynamic_count, deploy_eligible, failure_reason,
                     judge_reasoning, eval_duration_ms)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
                RETURNING *
                """,
                row["run_id"],
                row["organization_id"],
                row["golden_set_id"],
                row["unified_score"],
                row["retrieval_score"],
                row["quality_score"],
                row["faithfulness_score"],
                row.get("latency_penalty", 0),
                row.get("cost_penalty", 0),
                row.get("ragas_context_precision"),
                row.get("ragas_context_recall"),
                row.get("ragas_answer_faithfulness"),
                row.get("ragas_answer_relevancy"),
                row.get("ragas_scorer"),
                row.get("adversarial_pass_rate"),
                row.get("adversarial_fail_count", 0),
                row.get("adversarial_dynamic_count", 5),
                row.get("deploy_eligible", False),
                row.get("failure_reason"),
                row.get("judge_reasoning"),
                row.get("eval_duration_ms"),
            )
            return dict(r) if r else {}

    async def get_by_run_id(self, run_id: UUID) -> dict | None:
        if self.client is not None:
            res = (
                await self.client.table(self.TABLE)
                .select("*")
                .eq("run_id", str(run_id))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None

        async with self.pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                SELECT * FROM evaluations
                WHERE run_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                run_id,
            )
            return dict(r) if r else None

    async def list_scores_for_pipeline(self, pipeline_id: UUID, limit: int = 20) -> list[dict]:
        """Recent unified scores for drift detection."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT e.unified_score, e.created_at
                FROM evaluations e
                JOIN pipeline_runs r ON r.id = e.run_id
                WHERE r.pipeline_id = $1
                ORDER BY e.created_at DESC
                LIMIT $2
                """,
                pipeline_id,
                limit,
            )
            return [dict(r) for r in rows]
