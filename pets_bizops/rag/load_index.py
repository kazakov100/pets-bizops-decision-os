"""Loads the cached index at runtime into a ready-to-query Retriever.

Used by both the retrieve_knowledge tool (ai/tools.py) and the live search
demo on the RAG Deep Dive page.
"""

from __future__ import annotations

import json
import os

import numpy as np

from pets_bizops.rag.embeddings import embed
from pets_bizops.rag.corpus_loader import load_all_chunks
from pets_bizops.rag.retriever import Chunk, Retriever

_INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")

_retriever: Retriever | None = None


class IndexNotBuiltError(RuntimeError):
    pass


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is not None:
        return _retriever

    chunks_path = os.path.join(_INDEX_DIR, "chunks.json")
    vectors_path = os.path.join(_INDEX_DIR, "embeddings.npy")
    if os.path.exists(chunks_path) and os.path.exists(vectors_path):
        # Fast path: load the prebuilt, cached index.
        with open(chunks_path, encoding="utf-8") as f:
            raw_chunks = json.load(f)
        chunks = [Chunk(text=c["text"], source=c["source"], corpus=c["corpus"]) for c in raw_chunks]
        vectors = np.load(vectors_path)
        retriever = Retriever(chunks=[], embed_fn=embed)
        retriever.chunks = chunks
        retriever.vectors = vectors
    else:
        # Deploy path: no cached index (it's gitignored) -- build it in memory
        # from the committed corpus markdown. Embeds ~15 short chunks once.
        retriever = Retriever(chunks=load_all_chunks(), embed_fn=embed)

    _retriever = retriever
    return _retriever
