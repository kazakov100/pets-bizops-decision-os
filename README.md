# Pets BizOps Decision OS

A Streamlit decision tool that analyzes **Lemonade, Inc. (NASDAQ: LMND)** Pet
insurance using **only real, publicly disclosed SEC data**. Each analysis stage
is LLM-driven and grounded in a purpose-built RAG corpus, with deterministic
safeguards against fabrication.

## The approach

1. **Business Overview** — real KPI snapshot, then a chosen strategic framework
   maps the company's **risks & opportunities** (consulting-frameworks RAG).
2. **User Pain Points** — public sentiment read into named pains (sentiment-
   methodology RAG).
3. **Course of Action** — frames one problem (Minto/SCQA) and recommends a
   course of action grounded in **Lemonade's own stated strategy** RAG.
4. **RAG Deep Dive** — explains and lets you query the retrieval layer.
5. **Data** — every underlying disclosed number.

**Discipline:** the AI explains/frames; **code computes every number** (KPIs,
$ estimates). Each run is checked by a separate validator — a deterministic
pass verifying every citation against the real tool-call transcript, plus an
optional second-model audit.

Each AI page shows a **precomputed example by default** (real prior runs in
`pets_bizops/data/default_runs/`), so it's usable with no setup; a button
re-runs any step (or all three) live.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env      # only needed to run live analyses
streamlit run Business_Overview.py
```

The RAG index builds itself in memory from `pets_bizops/rag/corpus/` on first
use (or pre-build a cache with `python -m pets_bizops.rag.build_index`).

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. At [share.streamlit.io](https://share.streamlit.io) → **New app** → pick this
   repo, branch `main`, main file **`Business_Overview.py`**.
3. **Advanced settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   (Streamlit exposes secrets as env vars, which is how the app reads the key.)
4. Deploy. Live analyses need the key; the precomputed defaults render without it.

> Note: `sentence-transformers` + `torch` are memory-heavy — if the free tier
> runs tight, the defaults still work; the live RAG path is what needs the RAM.

## Tests

```bash
pytest -q
```
