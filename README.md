---
title: Pets BizOps Decision OS
emoji: 🍋
colorFrom: pink
colorTo: gray
sdk: streamlit
sdk_version: 1.58.0
app_file: Business_Overview.py
python_version: "3.11"
pinned: false
---

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

## Deploy to Hugging Face Spaces (recommended — more RAM, sleeps far less)

The YAML header at the top of this README configures the Space (`sdk: streamlit`,
`app_file: Business_Overview.py`). Free CPU Spaces get ~16 GB RAM, so the
`torch`/`sentence-transformers` RAG path runs comfortably, and Spaces only pause
after ~48h idle (vs. Streamlit Cloud's quick sleep).

1. Create a Space at [huggingface.co/new-space](https://huggingface.co/new-space)
   → **SDK: Streamlit**, hardware **CPU basic (free)**.
2. Add it as a git remote and push this repo to it:
   ```bash
   git remote add hf https://huggingface.co/spaces/<user>/<space-name>
   git push hf main
   ```
   (Auth with a Hugging Face **write** access token when prompted.)
3. In the Space → **Settings → Variables and secrets → New secret**, add
   `ANTHROPIC_API_KEY` = your key (exposed as an env var, which is how the app
   reads it). Live analyses need it; the precomputed defaults render without it.

## Tests

```bash
pytest -q
```
