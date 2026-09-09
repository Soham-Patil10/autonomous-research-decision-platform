"""Chunking. The least glamorous part of RAG and the one that decides whether it works.

Two rules worth keeping:
  1. Never split a table or a numbered clause across chunks - analytical questions
     ask about exactly those.
  2. Carry a locator (page / section) on every chunk, or citations cannot be verified.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    text: str
    locator: str
    metadata: dict


def chunk_document(doc_id: str, text: str, metadata: dict | None = None) -> list[Chunk]:
    """TODO(v1): structure-aware splitting.

    Start with recursive character splitting on paragraph boundaries, then upgrade to
    heading-aware splitting once the corpus is real.
    """
    s = get_settings()
    metadata = metadata or {}
    chunks: list[Chunk] = []
    step = s.chunk_size - s.chunk_overlap

    for i, start in enumerate(range(0, len(text), step)):
        window = text[start : start + s.chunk_size]
        if not window.strip():
            continue
        chunks.append(
            Chunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}::{i}",
                text=window,
                locator=f"chars {start}-{start + len(window)}",
                metadata=metadata,
            )
        )
    return chunks
