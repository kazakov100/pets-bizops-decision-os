"""RAG Deep Dive: how the retrieval layer used elsewhere in this app is
actually built -- the 3 corpora, the embedding model, chunking, vector
store, and a live, deterministic (no LLM call) search box so you can verify
retrieval quality yourself.
"""

from __future__ import annotations

import streamlit as st

from pets_bizops.rag.corpus_loader import load_all_chunks, CORPUS_IDS
from pets_bizops.rag.embeddings import MODEL_NAME, EMBEDDING_DIM
from pets_bizops.rag.load_index import get_retriever, IndexNotBuiltError
from pets_bizops.ui import style

st.set_page_config(page_title="RAG Deep Dive -- Pets BizOps Decision OS", page_icon="🐾", layout="wide")
style.inject_global_styles()

style.headline("RAG Deep Dive", "How the retrieval layer behind Business Overview, User Pain Points, and Course of Action is actually built.")

CORPUS_INFO = {
    "consulting_best_practices": {
        "label": "Consulting Best Practices",
        "used_by": "Business Overview's AI Deep Dive",
        "purpose": "Real, cited consulting frameworks (McKinsey/BCG) for reading growth, margin, and underwriting data -- shapes which charts the AI selects and how it frames them.",
    },
    "sentiment_methodology": {
        "label": "Sentiment Analysis Methodology",
        "used_by": "User Pain Points",
        "purpose": "Real, cited survey/NPS/review-bias/thematic-coding research -- shapes how much weight the AI gives a given complaint theme or rating.",
    },
    "lemonade_approach": {
        "label": "Lemonade's Strategic Approach",
        "used_by": "Course of Action",
        "purpose": "Real, cited excerpts on Lemonade's own stated strategic playbook (flat fee, Giveback, AI-first claims, cross-sell) -- grounds candidate approaches in what the company itself says it's trying to do.",
    },
}

chunks = load_all_chunks()
chunks_by_corpus = {cid: [c for c in chunks if c.corpus == cid] for cid in CORPUS_IDS}

st.divider()
style.headline("1. The 3 corpora")
for corpus_id in CORPUS_IDS:
    info = CORPUS_INFO[corpus_id]
    with st.expander(f"{info['label']} -- {len(chunks_by_corpus[corpus_id])} documents -- used by {info['used_by']}"):
        st.caption(info["purpose"])
        for c in chunks_by_corpus[corpus_id]:
            st.markdown(f"- {c.source}")

st.divider()
style.headline("2. Method", "The whole pipeline, end to end.")
mcol1, mcol2, mcol3 = st.columns(3)
with mcol1:
    style.kpi_card("Embedding model", MODEL_NAME, f"{EMBEDDING_DIM}-dim vectors", None)
with mcol2:
    style.kpi_card("Chunking", "1 doc = 1 chunk", "~150-300 words each, no splitting", None)
with mcol3:
    style.kpi_card("Vector store", "In-memory numpy", "cosine similarity (dot product on normalized vectors)", None)
st.caption(
    "No vector database -- the corpus is a few dozen chunks total, so a plain numpy "
    "dot-product search is the whole retrieval algorithm. Embeddings run locally "
    "(sentence-transformers), no API key, no network call at query time. The index "
    "is pre-built (`python -m pets_bizops.rag.build_index`) and cached to disk; "
    "`retrieve_knowledge` and this page's search box both load that same cached index."
)

st.divider()
style.headline("3. Try it yourself", "A live, deterministic search -- no LLM call, just the raw retrieval step.")
scol1, scol2, scol3 = st.columns([2, 2, 1])
with scol1:
    query = st.text_input("Query", value="is a thin margin on a fast-growing segment a bad sign")
with scol2:
    corpus_choice = st.selectbox("Corpus", CORPUS_IDS, format_func=lambda c: CORPUS_INFO[c]["label"])
with scol3:
    k = st.number_input("k", min_value=1, max_value=10, value=3)

if st.button("Search", type="primary"):
    try:
        retriever = get_retriever()
        results = retriever.retrieve(query, corpus=corpus_choice, k=int(k))
        for r in results:
            st.markdown(f"**Score: {r['score']:.3f}**")
            st.markdown(r["text"])
            st.caption(f"Source: {r['source']}")
            st.divider()
    except IndexNotBuiltError as e:
        st.error(str(e))
