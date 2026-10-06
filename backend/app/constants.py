"""Project-wide constants (LLD §9.3, §9.5, §13)."""

# ---- Batch embedding (LLD §9.3) ----
EMBEDDING_BATCH_SIZE = 100  # gemini-embedding-001 sweet spot
EMBEDDING_MAX_CONCURRENT = 5
EMBEDDING_MAX_RETRIES = 5

# ---- Unified Score weights (LLD §9.5) ----
WEIGHT_RETRIEVAL = 0.25
WEIGHT_QUALITY = 0.35
WEIGHT_FAITHFULNESS = 0.25
WEIGHT_LATENCY_PENALTY = 0.10
WEIGHT_COST_PENALTY = 0.05

# ---- Decision thresholds (reconciled across BRD/PRD/HLD/LLD) ----
FAITHFULNESS_HARD_GATE = 0.50  # below this => BLOCKED, non-bypassable
ADVERSARIAL_ANCHOR_PASS_RATE = 1.0  # fixed anchors must be perfect
# Deploy gate calibrated for the MVP scoring model. With weights
# (retrieval .25 / quality .35 / faithfulness .25) the theoretical max is ~0.85,
# so an 0.85 gate is unreachable in practice. Three-tier gate:
#   >= DEPLOY  -> deploy-eligible (strong pipeline, e.g. ~0.75)
#   >= IMPROVE -> propose a variant (mid runs)
#   <  IMPROVE -> blocked (weak runs, e.g. ~0.5)
# The faithfulness + adversarial hard gates remain absolute regardless of score.
DEPLOY_SCORE_THRESHOLD = 0.72
IMPROVE_SCORE_THRESHOLD = 0.60

# Latency penalty bands (p95 ms). Calibrated for a remote LLM gateway where a
# single completion routinely takes several seconds; the original 3s/6s bands
# were effectively never satisfiable.
LATENCY_GOOD_MS = 8000
LATENCY_OK_MS = 15000

# ---- Retrieval ----
DEFAULT_TOP_K = 5
HYBRID_CANDIDATE_LIMIT = 20
HYDE_STRONG_HIT_THRESHOLD = 0.7  # >=3 hits above this => skip HyDE
HYDE_MIN_STRONG_HITS = 3

# ---- LLM failover (LLD §13) ----
# LLM_FAILOVER_ORDER is now computed from settings in LLMService.__init__
LLM_MAX_RETRIES = 3
LLM_TIMEOUT_PER_PROVIDER_S = 30
CIRCUIT_BREAKER_ERROR_THRESHOLD = 3
CIRCUIT_BREAKER_COOLDOWN_S = 60

# ---- Rate limits (LLD §9.8) ----
GEMINI_RATE_PER_MIN = 1500
COHERE_RATE_PER_MIN = 100

# ---- Observer drift (LLD §16) ----
DRIFT_THRESHOLD = 0.05

# ---- RAGAS scorer fallback (LLD §9.5, Phase 1.5) ----
RAGAS_SCORER_PRIMARY = "gemini-2.5-pro"
RAGAS_SCORER_FALLBACK = "gpt-4o"
ERR_RAGAS_SCORER_FALLBACK = "ERR_RAGAS_SCORER_FALLBACK"

# ---- Golden set (LLD §10.4) ----
GOLDEN_SYNTHETIC_COUNT = 5
FIXED_ADVERSARIAL_ANCHORS = [
    "What did the CEO say on March 3rd, 2019?",
    "List all employees who joined before 1990.",
    "What is the revenue forecast for 2035?",
    "Who won the Nobel Prize mentioned in section 12?",
    "What were the quarterly earnings for Q3 1999?",
]
REFUSAL_PHRASES = (
    "don't know",
    "do not know",
    "cannot answer",
    "can't answer",
    "not present",
    "not found",
    "no information",
    "unable to",
)
