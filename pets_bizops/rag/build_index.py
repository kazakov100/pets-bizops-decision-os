"""Build the cached embeddings index from the corpus markdown files.

Run as: python -m pets_bizops.rag.build_index
Writes pets_bizops/rag/index/{chunks.json,embeddings.npy} -- gitignored
build artifacts, regenerated whenever the corpus files change.
"""

from __future__ import annotations

import json
import os

import numpy as np

from pets_bizops.rag.corpus_loader import load_all_chunks
from pets_bizops.rag.embeddings import embed

_INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")


def main() -> None:
    chunks = load_all_chunks()
    if not chunks:
        raise RuntimeError("No corpus chunks found -- check pets_bizops/rag/corpus/.")

    vectors = embed([c.text for c in chunks])

    os.makedirs(_INDEX_DIR, exist_ok=True)
    with open(os.path.join(_INDEX_DIR, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump([{"text": c.text, "source": c.source, "corpus": c.corpus} for c in chunks], f, indent=2)
    np.save(os.path.join(_INDEX_DIR, "embeddings.npy"), vectors)

    print(f"Indexed {len(chunks)} chunks across {len({c.corpus for c in chunks})} corpora -> {_INDEX_DIR}")


if __name__ == "__main__":
    main()
