"""OpenAI GPT-4o provider (failover + RAGAS scorer fallback)."""

from __future__ import annotations

from app.config import settings
from app.exceptions import LLMFailoverExhaustedError
from app.models import LLMResponse
from app.services.llm.base import BaseLLMProvider


class OpenAILLM(BaseLLMProvider):
    def __init__(self, model: str = "gpt-4o"):
        self.name = model
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI  # lazy import
            kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def complete(self, messages: list[dict], schema: dict | None = None) -> LLMResponse:
        try:
            client = self._get_client()
            resp = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                timeout=30.0,
            )
            choice = resp.choices[0].message.content or ""
            return LLMResponse(content=choice, provider=self.name)
        except Exception as exc:  # noqa: BLE001
            raise LLMFailoverExhaustedError(f"openai::{self.model} failed: {exc}") from exc

