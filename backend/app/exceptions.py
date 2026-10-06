"""Domain exceptions and error codes (LLD §17)."""

from __future__ import annotations


class AutoRAGException(Exception):
    """Base for all domain exceptions. Carries a stable error code."""

    code: str = "ERR_INTERNAL"

    def __init__(self, message: str | None = None, details: dict | None = None):
        super().__init__(message or self.code)
        self.message = message or self.code
        self.details = details or {}


class ValidationError(AutoRAGException):
    code = "ERR_VALIDATION"


class IngestionError(AutoRAGException):
    code = "ERR_INGESTION"


class ChunkingError(AutoRAGException):
    code = "ERR_CHUNKING"


class EmbeddingError(AutoRAGException):
    code = "ERR_EMBEDDING"


class PgVectorIndexError(AutoRAGException):
    code = "ERR_PGVECTOR_INDEX"


class RetrievalError(AutoRAGException):
    code = "ERR_RETRIEVAL"


class RerankerError(AutoRAGException):
    """Triggers graceful degradation in the retrieval pipeline."""

    code = "ERR_RERANKER"


class EvaluationError(AutoRAGException):
    code = "ERR_EVALUATION"


class RagasScorerFallback(AutoRAGException):
    code = "ERR_RAGAS_SCORER_FALLBACK"


class HardGateViolationError(AutoRAGException):
    """Non-bypassable faithfulness / adversarial gate violation."""

    code = "ERR_HARD_GATE"


class LLMFailoverExhaustedError(AutoRAGException):
    code = "ERR_LLM_FAILOVER_EXHAUSTED"


class ApprovalTimeoutError(AutoRAGException):
    code = "ERR_APPROVAL_TIMEOUT"


class DeploymentError(AutoRAGException):
    code = "ERR_DEPLOYMENT"


class DiagnosisError(AutoRAGException):
    code = "ERR_DIAGNOSIS"


class ImprovementError(AutoRAGException):
    code = "ERR_IMPROVEMENT"


class ObservabilityError(AutoRAGException):
    code = "ERR_OBSERVABILITY"
