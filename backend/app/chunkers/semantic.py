"""SemanticChunker — split on semantic boundaries (LLD §12)."""

from __future__ import annotations

from app.chunkers.base import BaseChunker
from app.models import Chunk, ChunkStrategy
from app.parsers.base import DocumentBlock


class SemanticChunker(BaseChunker):
    def __init__(self, target_tokens: int = 512, overlap_tokens: int = 64):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

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
                        strategy=ChunkStrategy.SEMANTIC,
                        page_number=block.page_number,
                        source_type="table",
                        media_path=block.media_path,
                        metadata=block.metadata,
                    )
                )
                chunk_idx += 1
                continue

            paragraphs = [p.strip() for p in block.content.split("\n\n") if p.strip()]
            current_chunk: list[str] = []
            current_tokens = 0

            for p in paragraphs:
                p_tokens = len(p.split())

                if p_tokens > self.target_tokens:
                    if current_chunk:
                        content = "\n\n".join(current_chunk)
                        chunks.append(
                            Chunk(
                                content=content,
                                chunk_index=chunk_idx,
                                token_count=current_tokens,
                                strategy=ChunkStrategy.SEMANTIC,
                                page_number=block.page_number,
                                source_type="text",
                                media_path=block.media_path,
                                metadata=block.metadata,
                            )
                        )
                        chunk_idx += 1
                        current_chunk = []
                        current_tokens = 0

                    # Split long paragraph into sentences
                    sentences = [
                        s.strip() for s in p.replace("?", ".").replace("!", ".").split(".") if s.strip()
                    ]
                    sent_chunk: list[str] = []
                    sent_tokens = 0
                    for s in sentences:
                        s_tokens = len(s.split())
                        if sent_tokens + s_tokens > self.target_tokens:
                            if sent_chunk:
                                chunks.append(
                                    Chunk(
                                        content=". ".join(sent_chunk) + ".",
                                        chunk_index=chunk_idx,
                                        token_count=sent_tokens,
                                        strategy=ChunkStrategy.SEMANTIC,
                                        page_number=block.page_number,
                                        source_type="text",
                                        media_path=block.media_path,
                                        metadata=block.metadata,
                                    )
                                )
                                chunk_idx += 1
                            sent_chunk = sent_chunk[-1:] if len(sent_chunk) > 1 else []
                            sent_tokens = sum(len(x.split()) for x in sent_chunk)
                        sent_chunk.append(s)
                        sent_tokens += s_tokens
                    if sent_chunk:
                        chunks.append(
                            Chunk(
                                content=". ".join(sent_chunk) + ".",
                                chunk_index=chunk_idx,
                                token_count=sent_tokens,
                                strategy=ChunkStrategy.SEMANTIC,
                                page_number=block.page_number,
                                source_type="text",
                                media_path=block.media_path,
                                metadata=block.metadata,
                            )
                        )
                        chunk_idx += 1
                    continue

                if current_tokens + p_tokens > self.target_tokens:
                    content = "\n\n".join(current_chunk)
                    chunks.append(
                        Chunk(
                            content=content,
                            chunk_index=chunk_idx,
                            token_count=current_tokens,
                            strategy=ChunkStrategy.SEMANTIC,
                            page_number=block.page_number,
                            source_type="text",
                            media_path=block.media_path,
                            metadata=block.metadata,
                        )
                    )
                    chunk_idx += 1
                    if current_chunk and len(current_chunk[-1].split()) <= self.overlap_tokens:
                        current_chunk = [current_chunk[-1], p]
                        current_tokens = len(current_chunk[0].split()) + p_tokens
                    else:
                        current_chunk = [p]
                        current_tokens = p_tokens
                else:
                    current_chunk.append(p)
                    current_tokens += p_tokens

            if current_chunk:
                content = "\n\n".join(current_chunk)
                chunks.append(
                    Chunk(
                        content=content,
                        chunk_index=chunk_idx,
                        token_count=current_tokens,
                        strategy=ChunkStrategy.SEMANTIC,
                        page_number=block.page_number,
                        source_type="text",
                        media_path=block.media_path,
                        metadata=block.metadata,
                    )
                )
        return chunks
