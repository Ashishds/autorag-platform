from __future__ import annotations

from app.chunkers.base import BaseChunker
from app.models import Chunk, ChunkStrategy
from app.parsers.base import DocumentBlock


class HierarchicalChunker(BaseChunker):
    def __init__(self, parent_tokens: int = 1024, child_tokens: int = 128):
        self.parent_tokens = parent_tokens
        self.child_tokens = child_tokens

    def chunk(self, text: str | list[DocumentBlock]) -> list[Chunk]:
        if isinstance(text, str):
            blocks = [DocumentBlock(type="text", content=text, page_number=1)]
        else:
            blocks = text

        chunks: list[Chunk] = []
        chunk_idx = 0

        for block in blocks:
            if block.type == "table":
                # Table-Aware Chunking: yield table block intact!
                p_tokens = len(block.content.split())
                chunks.append(
                    Chunk(
                        content=block.content,
                        chunk_index=chunk_idx,
                        token_count=p_tokens,
                        strategy=ChunkStrategy.HIERARCHICAL_PARENT,
                        page_number=block.page_number,
                        source_type="table",
                        media_path=block.media_path,
                        metadata=block.metadata,
                    )
                )
                chunk_idx += 1
                continue

            paragraphs = [p.strip() for p in block.content.split("\n\n") if p.strip()]
            for p in paragraphs:
                p_tokens = len(p.split())
                if p_tokens == 0:
                    continue

                chunks.append(
                    Chunk(
                        content=p,
                        chunk_index=chunk_idx,
                        token_count=p_tokens,
                        strategy=ChunkStrategy.HIERARCHICAL_PARENT,
                        page_number=block.page_number,
                        source_type="text",
                        media_path=block.media_path,
                        metadata=block.metadata,
                    )
                )
                chunk_idx += 1

                # Sub-split into children
                words = p.split()
                for i in range(0, len(words), self.child_tokens):
                    child_words = words[i : i + self.child_tokens]
                    child_content = " ".join(child_words)
                    chunks.append(
                        Chunk(
                            content=child_content,
                            chunk_index=chunk_idx,
                            token_count=len(child_words),
                            strategy=ChunkStrategy.HIERARCHICAL_CHILD,
                            page_number=block.page_number,
                            source_type="text",
                            media_path=block.media_path,
                            metadata=block.metadata,
                        )
                    )
                    chunk_idx += 1

        return chunks
