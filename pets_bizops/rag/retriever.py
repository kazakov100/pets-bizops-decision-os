"""Cosine-similarity retrieval over a small, in-memory set of chunks.

No vector database -- the corpus is a few dozen chunks total, so a plain
numpy dot-product search (embeddings are pre-normalized, so dot product IS
cosine similarity) is the whole algorithm, easy to verify and test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass
class Chunk:
    text: str
    source: str
    corpus: str


class Retriever:
    def __init__(self, chunks: list[Chunk], embed_fn: Callable[[list[str]], np.ndarray]):
        self.chunks = chunks
        self.embed_fn = embed_fn
        self.vectors = embed_fn([c.text for c in chunks]) if chunks else np.zeros((0, 1), dtype=np.float32)

    def retrieve(self, query: str, corpus: str | None = None, k: int = 3) -> list[dict]:
        candidate_idxs = [i for i, c in enumerate(self.chunks) if corpus is None or c.corpus == corpus]
        if not candidate_idxs:
            return []

        query_vec = self.embed_fn([query])[0]
        scores = self.vectors[candidate_idxs] @ query_vec

        ranked = sorted(zip(candidate_idxs, scores), key=lambda pair: -pair[1])[:k]
        return [
            {
                "text": self.chunks[idx].text,
                "source": self.chunks[idx].source,
                "corpus": self.chunks[idx].corpus,
                "score": round(float(score), 4),
            }
            for idx, score in ranked
        ]
