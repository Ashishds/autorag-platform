"""Gemini LLM provider (primary). SDK imported lazily to keep startup light."""

from __future__ import annotations

from app.config import settings
from app.exceptions import LLMFailoverExhaustedError
from app.models import LLMResponse
from app.services.llm.base import BaseLLMProvider


class GeminiLLM(BaseLLMProvider):
    def __init__(self, model: str):
        self.name = model
        self.model = model

    async def complete(self, messages: list[dict], schema: dict | None = None) -> LLMResponse:
        try:
            from google import genai  # lazy import
            from google.genai import types
            import base64

            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            contents = []
            for m in messages:
                content = m.get("content")
                if isinstance(content, str):
                    contents.append(content)
                elif isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        part_type = part.get("type")
                        if part_type == "text":
                            contents.append(part.get("text", ""))
                        elif part_type == "image_url":
                            img_url = part.get("image_url", {}).get("url", "")
                            if img_url.startswith("data:"):
                                try:
                                    header, encoded = img_url.split(",", 1)
                                    mime_type = header.split(";")[0].split(":")[1]
                                    img_data = base64.b64decode(encoded)
                                    contents.append(
                                        types.Part.from_bytes(data=img_data, mime_type=mime_type)
                                    )
                                except Exception:
                                    pass
                            else:
                                contents.append(img_url)

            config = None
            if schema:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                )

            resp = await client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            return LLMResponse(content=resp.text or "", provider=self.name)
        except Exception as exc:  # noqa: BLE001 - normalized to domain error for failover
            raise LLMFailoverExhaustedError(f"gemini::{self.model} failed: {exc}") from exc
