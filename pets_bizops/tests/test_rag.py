import numpy as np
import pytest

from pets_bizops.rag.corpus_loader import load_all_chunks, CORPUS_IDS
from pets_bizops.rag.retriever import Chunk, Retriever


def _fake_embed(texts: list[str]) -> np.ndarray:
    """Deterministic fake embedder for fast, offline retrieval tests --
    one-hot-ish vectors keyed by a fixed vocabulary so ranking is exact and
    predictable without loading the real model.
    """
    vocab = ["growth", "margin", "claims", "sentiment", "lemonade", "strategy"]
    vectors = []
    for text in texts:
        lower = text.lower()
        vec = np.array([1.0 if word in lower else 0.0 for word in vocab], dtype=np.float32)
        norm = np.linalg.norm(vec)
        vectors.append(vec / norm if norm > 0 else vec)
    return np.array(vectors, dtype=np.float32)


def test_retriever_ranks_exact_keyword_match_highest():
    chunks = [
        Chunk(text="This is about claims handling.", source="A", corpus="x"),
        Chunk(text="This is about growth and margin tradeoffs.", source="B", corpus="x"),
        Chunk(text="Unrelated text about nothing in the vocab.", source="C", corpus="x"),
    ]
    retriever = Retriever(chunks=chunks, embed_fn=_fake_embed)
    results = retriever.retrieve("growth margin", corpus=None, k=2)
    assert results[0]["source"] == "B"
    assert results[0]["score"] >= results[1]["score"]


def test_retriever_filters_by_corpus():
    chunks = [
        Chunk(text="growth claims", source="A", corpus="business"),
        Chunk(text="growth claims", source="B", corpus="sentiment"),
    ]
    retriever = Retriever(chunks=chunks, embed_fn=_fake_embed)
    results = retriever.retrieve("growth", corpus="sentiment", k=5)
    assert len(results) == 1
    assert results[0]["source"] == "B"


def test_retriever_returns_empty_for_unknown_corpus():
    chunks = [Chunk(text="growth", source="A", corpus="business")]
    retriever = Retriever(chunks=chunks, embed_fn=_fake_embed)
    assert retriever.retrieve("growth", corpus="nonexistent", k=3) == []


def test_load_all_chunks_parses_real_corpus_files():
    chunks = load_all_chunks()
    assert len(chunks) >= 9
    corpora_present = {c.corpus for c in chunks}
    assert corpora_present == set(CORPUS_IDS)
    for c in chunks:
        assert c.text
        assert c.source
        assert "Source:" not in c.text


@pytest.mark.slow
def test_real_embedder_produces_expected_shape():
    from pets_bizops.rag.embeddings import embed, EMBEDDING_DIM

    vectors = embed(["a short test sentence", "another one"])
    assert vectors.shape == (2, EMBEDDING_DIM)
