from __future__ import annotations

import io
from app.parsers.base import DocumentBlock


class DOCXParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        blocks = []
        try:
            import docx

            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            if paragraphs:
                blocks.append(
                    DocumentBlock(type="text", content="\n\n".join(paragraphs), page_number=1)
                )
        except ImportError:
            # Fallback to plain-text decode
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="ignore")
            if text.strip():
                blocks.append(DocumentBlock(type="text", content=text, page_number=1))
        return blocks
