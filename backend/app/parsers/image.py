from __future__ import annotations

import base64
from app.config import settings
from app.parsers.base import DocumentBlock
from app.services.llm.service import LLMService


class ImageParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        llm_svc = LLMService()

        # Determine standard mime type
        mtype = mime_type or "image/png"
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if ext in (".jpg", ".jpeg"):
            mtype = "image/jpeg"
        elif ext == ".png":
            mtype = "image/png"

        prompt = (
            "Analyze this image and perform two tasks:\n"
            "1. Extract all text verbatim (OCR).\n"
            "2. Provide a descriptive caption/summary of what the image shows for search index retrieval.\n\n"
            "Format the result precisely like:\n"
            "--- START OCR ---\n"
            "[Extracted Text]\n"
            "--- END OCR ---\n"
            "--- START CAPTION ---\n"
            "[Image Caption]\n"
            "--- END CAPTION ---"
        )

        base64_str = base64.b64encode(file_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mtype};base64,{base64_str}"},
                    },
                ],
            }
        ]

        # Request completions using our LLMService's fast model preference
        resp = await llm_svc.complete(messages, model_preference=settings.LLM_FAST)
        text_content = resp.content or ""

        return [
            DocumentBlock(
                type="image",
                content=text_content,
                page_number=1,
                media_path=storage_path,
            )
        ]
