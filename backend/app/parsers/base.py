from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class DocumentBlock:
    type: str  # "text" | "table" | "figure" | "image"
    content: str
    page_number: int | None = None
    media_path: str | None = None
    metadata: dict = field(default_factory=dict)


class DocumentParser(Protocol):
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        """Parse raw file bytes into a list of typed DocumentBlocks."""
        ...
