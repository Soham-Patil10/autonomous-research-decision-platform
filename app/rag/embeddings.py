"""Embedding provider. Isolated so the model can be swapped without touching callers.

Pin the model name in config and record it alongside the index — changing embedding
models invalidates every stored vector, and silent drift here is a nasty bug.
"""

from __future__ import annotations

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSIONS = 384


class Embedder:
    """TODO(v1): load the model once, batch encode, normalise to unit length."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self.model_name = model_name
        self._model = None

    def encode(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("TODO(v1)")
