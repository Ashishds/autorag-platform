from __future__ import annotations

from app.parsers.base import DocumentBlock


class TextParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")

        return [DocumentBlock(type="text", content=text, page_number=1)]
