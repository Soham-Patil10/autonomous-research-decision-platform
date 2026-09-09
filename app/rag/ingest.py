"""One ingestion pass that feeds both retrieval indexes.

    load -> parse -> chunk -> embed -> vector store
                          \\-> tokenise -> BM25 store

Both indexes must come from the same chunk list. If they drift, RRF is fusing two
different corpora and your retrieval metrics become meaningless.
"""

from __future__ import annotations

from pathlib import Path

from app.rag.bm25_store import BM25Store
from app.rag.chunking import chunk_document
from app.rag.vector_store import VectorStore

SUPPORTED = {".pdf", ".md", ".txt", ".html"}


async def ingest_directory(path: Path) -> int:
    """Index every supported file under `path`. Returns the chunk count."""
    vector, sparse = VectorStore(), BM25Store()
    all_chunks: list = []

    for file in sorted(path.rglob("*")):
        if file.suffix.lower() not in SUPPORTED:
            continue
        # TODO(v1): real parsers - pypdf for .pdf, keep page numbers as the locator.
        text = file.read_text(encoding="utf-8", errors="ignore")
        all_chunks.extend(chunk_document(doc_id=file.name, text=text, metadata={"path": str(file)}))

    await vector.upsert(all_chunks)
    await sparse.build(all_chunks)
    return len(all_chunks)
