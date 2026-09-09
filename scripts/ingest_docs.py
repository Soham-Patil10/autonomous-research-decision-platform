"""Index data/documents into both retrieval stores.

Put 10-30 real documents in data/documents before running this: annual reports,
regulatory PDFs, competitor write-ups, internal memos. A corpus you can reason about
is worth far more than a large one you cannot.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.rag.ingest import ingest_directory

DOCS = Path("data/documents")


async def main() -> None:
    if not DOCS.exists() or not any(DOCS.iterdir()):
        print(f"no documents in {DOCS} - add some first")
        return
    count = await ingest_directory(DOCS)
    print(f"indexed {count} chunks from {DOCS}")


if __name__ == "__main__":
    asyncio.run(main())
