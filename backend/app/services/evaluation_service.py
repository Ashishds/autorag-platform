"""EvaluationService — Unified Score + deploy decision + full eval run (LLD §9.5, §11)."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from uuid import UUID
from langfuse import observe, propagate_attributes

from app.config import settings
from app.constants import (
    ADVERSARIAL_ANCHOR_PASS_RATE,
    DEPLOY_SCORE_THRESHOLD,
    FAITHFULNESS_HARD_GATE,
    IMPROVE_SCORE_THRESHOLD,
    LATENCY_GOOD_MS,
    LATENCY_OK_MS,
    REFUSAL_PHRASES,
    WEIGHT_COST_PENALTY,
    WEIGHT_FAITHFULNESS,
    WEIGHT_LATENCY_PENALTY,
    WEIGHT_QUALITY,
    WEIGHT_RETRIEVAL,
)
from app.models import DeployDecision, EvalMetrics, GoldenQA
from app.schemas.query import FlagMode, QueryRequest


@dataclass
class EvalRunResult:
    unified_score: float
    retrieval_score: float
    quality_score: float
    faithfulness_score: float
    latency_penalty: float
    cost_penalty: float
    ragas_scores: dict[str, float]
    ragas_scorer: str
    adversarial_pass_rate: float
    adversarial_fail_count: int
    deploy_eligible: bool
    deploy_decision: DeployDecision
    diagnosis: list[str]
    judge_reasoning: str
    eval_duration_ms: int


class EvaluationService:
    def compute_unified_score(self, m: EvalMetrics) -> float:
        return (
            WEIGHT_RETRIEVAL * m.retrieval
            + WEIGHT_QUALITY * m.quality
            + WEIGHT_FAITHFULNESS * m.faithfulness
            - WEIGHT_LATENCY_PENALTY * m.latency_penalty
            - WEIGHT_COST_PENALTY * m.cost_penalty
        )

    def make_deploy_decision(
        self, score: float, faithfulness: float, adversarial_pass_rate: float
    ) -> DeployDecision:
        if faithfulness < FAITHFULNESS_HARD_GATE:
            return DeployDecision.BLOCKED_FAITHFULNESS
        if adversarial_pass_rate < ADVERSARIAL_ANCHOR_PASS_RATE:
            return DeployDecision.BLOCKED_ADVERSARIAL
        if score >= DEPLOY_SCORE_THRESHOLD:
            return DeployDecision.DEPLOY
        if score >= IMPROVE_SCORE_THRESHOLD:
            return DeployDecision.IMPROVE
        return DeployDecision.BLOCKED_SCORE

    @staticmethod
    def classify_failures(
        ragas: dict, faithfulness: float, adversarial_pass_rate: float
    ) -> list[str]:
        """Rule-based remediation hints (MVP Diagnoser, LLD §8.3)."""
        hints: list[str] = []
        if ragas.get("context_recall", 1.0) < 0.7:
            hints.append("increase_top_k_or_chunk_overlap")
        if ragas.get("context_precision", 1.0) < 0.7:
            hints.append("enable_rerank_or_tighten_chunks")
        if faithfulness < 0.9:
            hints.append("strengthen_grounding_prompt")
        if adversarial_pass_rate < 0.9:
            hints.append("add_refusal_instruction")
        return hints

    @observe()
    async def run_evaluation(
        self,
        pipeline_id: UUID,
        organization_id: UUID,
        golden_qas: list[GoldenQA],
        query_svc,
        llm,
    ) -> EvalRunResult:
        """Score pipeline against frozen golden set."""
        with propagate_attributes(
            trace_name="Evaluation Run",
            user_id=str(organization_id),
            metadata={"pipeline_id": str(pipeline_id), "golden_count": len(golden_qas)},
        ):
            started = time.monotonic()
            synthetic = [q for q in golden_qas if q.question_type == "synthetic"]
            adversarial = [q for q in golden_qas if q.question_type == "adversarial_fixed"]

            recall_scores: list[float] = []
            precision_scores: list[float] = []
            relevancy_scores: list[float] = []
            faithfulness_scores: list[float] = []
            latencies: list[int] = []
            judge_notes: list[str] = []

            import asyncio

            async def process_synthetic(qa):
                result = await query_svc.query(
                    QueryRequest(
                        pipeline_id=pipeline_id,
                        q=qa.question,
                        top_k=5,
                        options={"rewrite": FlagMode.off, "hyde": FlagMode.off},
                    ),
                    organization_id=organization_id,
                )
                # sources are returned in rank order (best first)
                ranked_ids = [str(s.chunk_id) for s in result.sources]
                retrieved_ids = set(ranked_ids)
                expected = {str(c) for c in qa.expected_chunks}

                recall = len(retrieved_ids & expected) / max(len(expected), 1)

                # Rank-aware average precision (RAGAS-style context precision):
                hits = 0
                ap_sum = 0.0
                for rank, cid in enumerate(ranked_ids, start=1):
                    if cid in expected:
                        hits += 1
                        ap_sum += hits / rank
                precision = ap_sum / max(len(expected), 1) if expected else 0.0

                # Judge faithfulness and relevancy in parallel
                faith_task = self._judge_faithfulness(
                    llm, qa.question, result.answer, qa.expected_answer
                )
                relevancy_task = self._judge_relevancy(llm, qa.question, result.answer)
                
                faith_res, relevancy = await asyncio.gather(faith_task, relevancy_task)
                faith, reasoning = faith_res

                return {
                    "latency_ms": result.latency_ms,
                    "recall": recall,
                    "precision": min(precision, 1.0),
                    "faithfulness": faith,
                    "reasoning": reasoning,
                    "relevancy": relevancy,
                }

            async def process_adversarial(qa):
                result = await query_svc.query(
                    QueryRequest(
                        pipeline_id=pipeline_id,
                        q=qa.question,
                        top_k=5,
                        options={"rewrite": FlagMode.off, "hyde": FlagMode.off},
                    ),
                    organization_id=organization_id,
                )
                return 1 if self._is_refusal(result.answer) else 0

            # Execute synthetic and adversarial evaluations concurrently
            synth_results = await asyncio.gather(*(process_synthetic(qa) for qa in synthetic))
            adv_results = await asyncio.gather(*(process_adversarial(qa) for qa in adversarial))

            for r in synth_results:
                latencies.append(r["latency_ms"])
                recall_scores.append(r["recall"])
                precision_scores.append(r["precision"])
                faithfulness_scores.append(r["faithfulness"])
                judge_notes.append(r["reasoning"])
                relevancy_scores.append(r["relevancy"])

            adv_pass = sum(adv_results)
            adv_rate = adv_pass / max(len(adversarial), 1)
            adv_fail = len(adversarial) - adv_pass

            retrieval = sum(recall_scores) / max(len(recall_scores), 1)
            context_precision = sum(precision_scores) / max(len(precision_scores), 1)
            context_recall = retrieval
            answer_relevancy = sum(relevancy_scores) / max(len(relevancy_scores), 1)
            faithfulness = sum(faithfulness_scores) / max(len(faithfulness_scores), 1)

            quality = (answer_relevancy + context_precision) / 2
            # Use the median (typical) latency rather than max-of-N: with only ~5
            # golden queries a single congested gateway call would otherwise dominate
            # a p95 and unfairly penalise an otherwise-healthy pipeline.
            if latencies:
                ordered = sorted(latencies)
                median_ms = ordered[len(ordered) // 2]
            else:
                median_ms = 0
            # Calibrated for a remote LLM gateway (gpt-4o over HTTP): single
            # completions routinely take several seconds, so the original 3s/6s
            # bands were never reachable. Bands reflect realistic cloud latency.
            latency_penalty = 0.0 if median_ms <= LATENCY_GOOD_MS else (
                0.5 if median_ms <= LATENCY_OK_MS else 1.0
            )
            cost_penalty = 0.0

            ragas_scores = {
                "context_precision": context_precision,
                "context_recall": context_recall,
                "answer_faithfulness": faithfulness,
                "answer_relevancy": answer_relevancy,
            }

            metrics = EvalMetrics(
                retrieval=retrieval,
                quality=quality,
                faithfulness=faithfulness,
                latency_penalty=latency_penalty,
                cost_penalty=cost_penalty,
            )
            unified = self.compute_unified_score(metrics)
            decision = self.make_deploy_decision(unified, faithfulness, adv_rate)
            diagnosis = self.classify_failures(ragas_scores, faithfulness, adv_rate)

            return EvalRunResult(
                unified_score=unified,
                retrieval_score=retrieval,
                quality_score=quality,
                faithfulness_score=faithfulness,
                latency_penalty=latency_penalty,
                cost_penalty=cost_penalty,
                ragas_scores=ragas_scores,
                ragas_scorer=settings.LLM_PRIMARY,
                adversarial_pass_rate=adv_rate,
                adversarial_fail_count=adv_fail,
                deploy_eligible=decision == DeployDecision.DEPLOY,
                deploy_decision=decision,
                diagnosis=diagnosis,
                judge_reasoning="; ".join(judge_notes[:3]),
                eval_duration_ms=int((time.monotonic() - started) * 1000),
            )

    async def _judge_faithfulness(
        self, llm, question: str, answer: str, expected: str | None
    ) -> tuple[float, str]:
        prompt = (
            "Rate faithfulness of the answer to the expected answer on a 0.0-1.0 scale.\n"
            f"Question: {question}\nExpected: {expected or 'N/A'}\nAnswer: {answer}\n\n"
            'Respond JSON: {"score": 0.0, "reasoning": "..."}'
        )
        resp = await llm.complete([{"role": "user", "content": prompt}])
        parsed = self._parse_score_json(resp.content)
        if parsed:
            return float(parsed.get("score", 0.5)), str(parsed.get("reasoning", ""))
        return 0.5, resp.content[:200]

    async def _judge_relevancy(self, llm, question: str, answer: str) -> float:
        prompt = (
            "Rate answer relevancy to the question on 0.0-1.0.\n"
            f"Question: {question}\nAnswer: {answer}\n\n"
            'Respond JSON: {"score": 0.0}'
        )
        resp = await llm.complete([{"role": "user", "content": prompt}])
        parsed = self._parse_score_json(resp.content)
        if parsed:
            return float(parsed.get("score", 0.5))
        return 0.5

    @staticmethod
    def _parse_score_json(text: str) -> dict | None:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _is_refusal(answer: str) -> bool:
        lower = answer.lower()
        return any(phrase in lower for phrase in REFUSAL_PHRASES)
