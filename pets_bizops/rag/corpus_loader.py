"""Loads the corpus markdown files into Chunk objects.

Convention: each file is ONE chunk -- the body text, followed by a final
line starting with "Source:" giving the real citation. One file = one
document = one chunk; no sliding-window splitting at this corpus size.
"""

from __future__ import annotations

import os

from pets_bizops.rag.retriever import Chunk

_CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")

CORPUS_IDS = ["consulting_best_practices", "sentiment_methodology", "lemonade_approach"]


def load_all_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for corpus_id in CORPUS_IDS:
        corpus_dir = os.path.join(_CORPUS_DIR, corpus_id)
        if not os.path.isdir(corpus_dir):
            continue
        for filename in sorted(os.listdir(corpus_dir)):
            if not filename.endswith(".md"):
                continue
            with open(os.path.join(corpus_dir, filename), encoding="utf-8") as f:
                raw = f.read().strip()
            lines = raw.splitlines()
            source_line_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("Source:")), None)
            if source_line_idx is None:
                raise ValueError(f"Corpus file {filename} in {corpus_id} is missing a 'Source:' line.")
            text = "\n".join(lines[:source_line_idx]).strip()
            source = lines[source_line_idx].split("Source:", 1)[1].strip()
            chunks.append(Chunk(text=text, source=source, corpus=corpus_id))
    return chunks
