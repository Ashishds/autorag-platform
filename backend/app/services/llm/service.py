"""LLMService — failover chain + circuit breaker (LLD §9.4, §13)."""

from __future__ import annotations

import time
from uuid import UUID

from app.config import settings
from app.constants import (
    CIRCUIT_BREAKER_COOLDOWN_S,
    CIRCUIT_BREAKER_ERROR_THRESHOLD,
)
from app.exceptions import LLMFailoverExhaustedError
from app.models import LLMResponse
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini import GeminiLLM
from app.services.llm.openai import OpenAILLM
from langfuse import observe, get_client


class _CircuitBreaker:
    """CLOSED -> OPEN (N consecutive errors) -> HALF_OPEN (after cooldown)."""

    def __init__(self) -> None:
        self.failures = 0
        self.opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= CIRCUIT_BREAKER_COOLDOWN_S:
            return True  # HALF_OPEN: allow a trial request
        return False

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= CIRCUIT_BREAKER_ERROR_THRESHOLD:
            self.opened_at = time.monotonic()


class LLMService:
    """Attempts providers in failover order; raises LLMFailoverExhaustedError when all fail."""

    def __init__(self) -> None:
        models = [settings.LLM_PRIMARY, settings.LLM_FAST, settings.LLM_FALLBACK]
        self._providers: dict[str, BaseLLMProvider] = {}
        for model in models:
            if model not in self._providers:
                # Use the native Gemini SDK only when a Google API key is set.
                # Otherwise (e.g. via the Euron OpenAI-compatible gateway) route
                # gemini-* models through the OpenAI-compatible provider too.
                if model.startswith("gemini") and settings.GOOGLE_API_KEY:
                    self._providers[model] = GeminiLLM(model)
                else:
                    self._providers[model] = OpenAILLM(model)
        self._breakers: dict[str, _CircuitBreaker] = {k: _CircuitBreaker() for k in self._providers}

    def _order(self, preference: str) -> list[str]:
        # Failover: preferred model first, then remaining registered providers
        all_models = list(self._providers.keys())
        order = [preference] + [m for m in all_models if m != preference]
        return [m for m in order if m in self._providers]

    @observe(as_type="generation")
    async def complete(
        self,
        messages: list[dict],
        model_preference: str | None = None,
        response_schema: dict | None = None,
        trace_id: UUID | None = None,
    ) -> LLMResponse:
        preference = model_preference or settings.LLM_PRIMARY
        last_error: Exception | None = None

        for model in self._order(preference):
            breaker = self._breakers[model]
            if not breaker.allow():
                continue
            try:
                resp = await self._providers[model].complete(messages, schema=response_schema)
                breaker.record_success()
                
                # Log to Langfuse
                get_client().update_current_generation(
                    name=f"llm-complete-{model}",
                    model=model,
                    input=messages,
                    output=resp.content,
                    usage_details={"total": resp.token_count} if resp.token_count else None,
                )
                
                return resp
            except Exception as exc:  # noqa: BLE001 - try next provider
                breaker.record_failure()
                last_error = exc

        raise LLMFailoverExhaustedError(
            "all LLM providers failed", details={"last_error": str(last_error)}
        )
