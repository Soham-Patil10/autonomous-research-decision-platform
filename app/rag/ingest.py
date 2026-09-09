"""One ingestion pass that feeds both retrieval indexes.

    load -> parse -> chunk -> embed -> vector store
                          \\-> tokenise -> BM25 store

Both indexes must come from the same chunk list. If they drift, RRF is fusing two
different corpora and your retrieval metrics become meaningless.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.rag.bm25_store import BM25Store
from app.rag.chunking import chunk_document
from app.rag.vector_store import VectorStore

SUPPORTED = {".pdf", ".md", ".txt", ".html"}
MANIFEST_NAME = "MANIFEST.json"


def load_provenance(path: Path) -> dict[str, dict[str, Any]]:
    """Read the fetcher's MANIFEST.json: filename -> {source_url, license, sha256, ...}.

    Missing is fine — hand-written internal documents have no upstream URL.
    """
    manifest = path / MANIFEST_NAME
    if not manifest.exists():
        return {}
    return json.loads(manifest.read_text(encoding="utf-8"))


async def ingest_directory(path: Path) -> int:
    """Index every supported file under `path`. Returns the chunk count."""
    vector, sparse = VectorStore(), BM25Store()
    provenance = load_provenance(path)
    all_chunks: list = []

    for file in sorted(path.rglob("*")):
        if file.suffix.lower() not in SUPPORTED:
            continue

        # TODO(v1): real parsers - pypdf for .pdf, keep page numbers as the locator.
        text = file.read_text(encoding="utf-8", errors="ignore")

        origin = provenance.get(file.name, {})
        metadata = {
            "path": str(file),
            # Carried onto every chunk so a Claim's citation resolves to a real URL
            # rather than just a filename. Without this, "cited" means very little.
            "source_url": origin.get("source_url", ""),
            "license": origin.get("license", ""),
            "sha256": origin.get("sha256", ""),
            "internal": not origin,  # no manifest entry => hand-written internal doc
        }
        all_chunks.extend(chunk_document(doc_id=file.name, text=text, metadata=metadata))

    await vector.upsert(all_chunks)
    await sparse.build(all_chunks)
    return len(all_chunks)
