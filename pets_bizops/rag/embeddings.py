"""Thin wrapper around a local sentence-transformers model.

Local + offline by design -- no API key, no network dependency, so the RAG
layer works the same way for anyone running this app, without adding a
second paid vendor key alongside the Anthropic one.
"""

from __future__ import annotations

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Embed a list of texts, returning an (n, EMBEDDING_DIM) float32 array."""
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


_prewarm_started = False


def prewarm() -> None:
    """Load the embedding model in a background thread (once per process) so the
    first retrieve_knowledge call inside an AI request doesn't pay the ~8s
    model cold-load mid-request. Idempotent and non-blocking.
    """
    global _prewarm_started
    if _prewarm_started:
        return
    _prewarm_started = True
    import threading

    def _warm():
        try:
            _get_model()
        except Exception:
            # Best-effort only -- the real embed() call will load the model
            # synchronously if this background warm didn't finish.
            pass

    threading.Thread(target=_warm, daemon=True).start()
