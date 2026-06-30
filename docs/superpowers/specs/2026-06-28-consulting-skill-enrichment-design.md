# Enrich the App from the consulting-analysis Skill

## Context

The project-scoped `consulting-analysis` Claude Code skill (installed from
bytedance/deer-flow at `.claude/skills/consulting-analysis/`) is a
consulting-grade research-report generator with a broad framework toolkit and
a strict zero-hallucination policy. It runs in the Claude Code session, not in
the Streamlit app (the app calls the Claude API directly with its own skill
files + RAG corpus). The user wants to MINE the skill to enrich the app
itself, not to produce a separate report.

Key constraint, flagged by the skill's own "data-feasible" selection
principle: most of its 30 frameworks need data this app does not have (DCF/EVA
= no cash flows, TAM-SAM-SOM = no market sizing, RFM/AARRR = no per-customer
transaction/funnel data, GE-McKinsey = invented attractiveness scores).
Adding those would force the exact fabrication the app is built to avoid, so
they are explicitly excluded. Only data-honest enrichments are in scope.

## Part A -- Methodology upgrade (prompt-only, no new fabrication surface)

Two of the skill's analytical disciplines are baked into existing prompts:

1. **Insight chain (Data -> Why -> So What).** Added to
   `pets_bizops/ai/skills/business_deep_dive.md`: every `key_implication`
   and the narrative must state the observed data, the likely attribution
   (directional, not certain -- consistent with the existing guardrail), and
   the strategic implication. Sharpens output quality with no new claims.
2. **Framework-selection principles** (complementary not overlapping,
   depth-over-breadth, data-feasible). Added to
   `BUSINESS_FRAMEWORK_ADVISOR_SYSTEM_PROMPT` so the advisor reasons about
   WHY a lens fits, not just lists pros/cons.

## Part B -- Two new text-grounded frameworks

Added exactly like the existing `swot` framework: qualitative,
evidence-cited bullets, no numeric data the app lacks, no chart. The AI
grounds them in get_mission_and_strategy_context, get_market_sentiment, the
KPI tools, and retrieve_knowledge; the existing grounding-check + per-item
`evidence_source` enforce traceability.

- **`porters_five_forces`** -- industry/competitive structure. framework_content:
  `{"forces": [{"force": "Threat of new entrants|Supplier power|Buyer power|Threat of substitutes|Competitive rivalry", "intensity": "high|medium|low", "assessment": "...", "evidence_source": "..."}]}` (exactly 5 forces).
- **`pestel`** -- macro environment (Political/Legal especially relevant for a
  regulated insurer). framework_content:
  `{"factors": [{"factor": "Political|Economic|Social|Technological|Environmental|Legal", "assessment": "...", "evidence_source": "..."}]}` (4-6 factors; the AI may focus on the ones with real signal rather than padding all six).

The framework menu grows from 4 -> 6. Both new ids supply `framework_content`
(like swot/issue_tree); bcg_growth_share and three_horizons remain
null-content/code-rendered.

## New corpus docs (real, cited -- same discipline as existing corpus)

In `pets_bizops/rag/corpus/consulting_best_practices/`:
- `porters_five_forces.md` -- Michael E. Porter, "How Competitive Forces
  Shape Strategy," Harvard Business Review, 1979 (and "The Five Competitive
  Forces That Shape Strategy," HBR 2008). Real citation; content verified via
  WebSearch at implementation time.
- `pestel_analysis.md` -- origin in Francis J. Aguilar's ETPS scanning
  ("Scanning the Business Environment," 1967), later PEST/PESTEL. Real
  citation; content verified via WebSearch.

Rebuild index (`python -m pets_bizops.rag.build_index`); corpus goes 13 -> 15
chunks. The existing `test_rag.py` `len(chunks) >= 9` lower-bound assertion
still holds.

## Files to modify
- `pets_bizops/ai/skills/business_deep_dive.md` -- insight chain; add the 2
  framework_ids + content shapes to the menu/branching instructions.
- `pets_bizops/ai/prompts.py` -- `BUSINESS_FRAMEWORK_ADVISOR_SYSTEM_PROMPT`:
  add the 2 frameworks (now 6 total, all present) + selection principles.
- `Business_Overview.py` -- add `FRAMEWORK_LABELS` entries for the 2;
  `_render_porters_five_forces(framework_content)` and
  `_render_pestel(framework_content)`; dispatch them in the render block.

## Files to create
- `pets_bizops/rag/corpus/consulting_best_practices/porters_five_forces.md`
- `pets_bizops/rag/corpus/consulting_best_practices/pestel_analysis.md`

## Verification
- `pytest -q` green.
- `AppTest` stub-render Business_Overview for `porters_five_forces` and
  `pestel` framework_ids -> no exception, content shows.
- `AppTest` cold load of Business_Overview still clean.
- Rebuild index; confirm 15 chunks; restart server.
