# AI-Chosen Framework Redesign (Business Deep Dive, User Pain Points, Course of Action)

## Context

The Business Overview Deep Dive (`Business_Overview.py`) currently has the AI
select 3-5 charts from a fixed registry of 6 real, code-rendered chart views
and write a long flowing narrative referencing them. In practice this
produced a wall of text and five charts that didn't add up to a clear
"bottom line" -- the actual signal (Pet's loss ratio plateau vs. its 2.4x
IFP scale-up, contrasted with Car/Europe's real improvement) was buried in
prose rather than led with. Separately, a real rendering bug surfaced:
Streamlit's `st.markdown` interprets `$...$` as LaTeX math, so any AI text
containing dollar figures (e.g. "$1.333B at Q1'26") renders as garbled
fraction-like gibberish.

While designing the fix for Business Overview, the user asked to apply the
same principle everywhere in the app: the AI should decide which real,
cited methodology/approach applies, grounded in the RAG corpus -- not have
code pre-select an analytical lens for it. This spec now covers all 3
RAG-grounded pages, plus removing the one remaining brittle heuristic
(`_infer_pain_point_id` keyword matching on Course of Action) in favor of
the AI calling the deterministic `get_pain_point_impact_estimate` tool
itself. The dollar figure returned by that tool is still 100%
code-computed (`impact.py`) -- only the judgment of *whether* one of the 3
known pain points applies to a given item moves from a keyword-matching
heuristic to the AI's own call.

This redesign does two things: (1) fixes the `$`-as-LaTeX rendering bug
everywhere AI-generated text is displayed, and (2) restructures the Deep
Dive so the AI's real job is choosing *which analytical lens* (framework)
best fits the current quarter's data pattern -- grounded in real, cited
consulting-framework material it retrieves via RAG -- rather than choosing
which of several pre-built charts to show. The "code computes, AI explains"
discipline is preserved: every quadrant/bucket/bubble position in every
chart-bearing framework is computed in code from real disclosed numbers;
the AI only ever picks the lens, justifies the pick, and supplies the
evidence-cited text content that has always been AI's job elsewhere in this
app (risks, opportunities, SWOT-style bullets, ranked findings).

## Fixed framework menu (USER chooses, AI advises)

**Design decision (revised):** the *user* selects which framework to apply --
this is the human BizOps judgment call, which is exactly what a senior lead
is hired to make -- and the AI's job is to (a) lay out the pros/cons of each
lens *for this specific data pattern* to inform that choice, then (b) apply
the chosen one rigorously. This is a stronger showcase than "AI picks a lens"
(which reads as gimmicky to a consultant) or "user picks blind" (which wastes
the AI's framework literacy). Flow:

1. **Framework advisor (optional AI call).** A "Compare frameworks for this
   situation" button runs one AI call that retrieves from
   `consulting_best_practices` and returns, for each of the 4 frameworks, a
   short "best for / pro here / con here" grounded in Lemonade's actual
   current numbers + the cited framework doc. Rendered as 4 compact cards so
   the user can decide with eyes open. Includes a `suggested_default` the AI
   leans toward, but the user is free to ignore it.
2. **User selects** one framework via a radio/selectbox (defaulting to the
   advisor's `suggested_default` if the advisor was run, else `bcg_growth_share`).
3. **Apply (AI call).** "Generate Deep Dive with <framework>" applies the
   user-chosen framework, grounded in RAG, producing the narrative +
   framework_content + key_implications.

The 4 frameworks the user picks from:

1. **`bcg_growth_share`** -- BCG-style 2x2 bubble chart. x = segment's share
   of company-wide IFP, y = segment's latest YoY IFP growth rate, bubble
   size = $ IFP, bubble color = loss-ratio health band (green=improving,
   amber=flat, red=worsening). Fully deterministic; AI supplies no numbers
   for this chart, only references it in the narrative.
2. **`three_horizons`** -- McKinsey Three Horizons classification. Each of
   the 5 real segments is deterministically bucketed into Horizon 1 (mature
   core: high share, low/moderate growth), Horizon 2 (scaling: high growth,
   moderate share), or Horizon 3 (early: low share, short/thin history) by
   fixed real-number thresholds in code. Rendered as 3 columns listing each
   segment's real share/growth numbers under its bucket.
3. **`swot`** -- 2x2 grid of Strengths/Weaknesses/Opportunities/Threats,
   2-3 bullets per quadrant, each AI-written but evidence-cited (same
   discipline as today's risks/opportunities -- a labeled claim tied to a
   specific tool result, not a fabricated number).
4. **`issue_tree`** -- McKinsey/Minto-style pyramid: one bottom-line
   headline, a short ranked list of 3-5 AI-written supporting findings
   (evidence-cited), plus exactly ONE supporting chart chosen from the
   existing 6-chart registry (`company_ifp_trend`, `growth_acceleration`,
   `pet_ifp_trend`, `segment_breakdown`, `company_vs_pet_loss_ratio`,
   `pet_loss_ratio_trend` -- unchanged from today).

Both the advisor call and the apply call must call
`retrieve_knowledge(corpus="consulting_best_practices")` and cite what they
retrieved. Two new real, cited corpus documents are added to support `swot`
and `issue_tree` specifically (the corpus already has Three Horizons and BCG
Growth-Share docs from the original RAG build):

- SWOT analysis origin (Albert Humphrey / Stanford Research Institute,
  1960s-70s) -- real, citable, e.g. via a Mind Tools or CFI overview that
  correctly attributes it.
- Barbara Minto's "Pyramid Principle" / MECE issue-tree structure -- real,
  citable (McKinsey-originated writing/reasoning framework).

## Deterministic segment positioning data

Before calling Claude, `Business_Overview.py` computes a `segment_positioning`
list (one entry per real segment: Homeowners, Pet, Car, Europe, Other) using
existing `kpis` functions (`kpis.segment_breakdown()` for share/$ IFP,
`kpis.segment_yoy_growth_series()` for latest YoY growth,
`kpis.segment_quarterly()` for the loss-ratio trend used to assign the
health band). This table is used by the `bcg_growth_share` and
`three_horizons` renderers regardless of which framework the AI ultimately
picks -- it's cheap to compute and removes any AI involvement in the
numbers for those two paths.

Loss-ratio health band thresholds (deterministic, real-number based):
compare each segment's latest disclosed quarter to its value 4 quarters
earlier (or earliest available if shorter); improving if it moved down >=3
points, worsening if it moved up >=3 points, otherwise flat/amber.

Three Horizons bucket thresholds (deterministic, evaluated in this priority
order so each segment lands in exactly one bucket): (1) Horizon 2 if YoY
growth >= 30%, regardless of share -- fast-growing takes priority over
share size; (2) else Horizon 1 if share >= median segment share -- mature
and not fast-growing; (3) else Horizon 3 -- everything else (low share,
not fast-growing: a thin/early line). Exact threshold values are tunable
during implementation but must be stated in code comments, not hidden
magic numbers.

## Output schemas

**Advisor call** (`BUSINESS_FRAMEWORK_ADVISOR_SYSTEM_PROMPT`) -- helps the
user choose:
```json
{
  "framework_options": [
    {
      "framework_id": "bcg_growth_share|three_horizons|swot|issue_tree",
      "best_for": "what kind of question this lens answers best",
      "pro_for_this_situation": "why it fits Lemonade's current numbers (cite real figure)",
      "con_for_this_situation": "where it falls short for this situation",
      "rag_source": "the 'source' field from the retrieve_knowledge result used"
    }
  ],
  "suggested_default": "framework_id"
}
```
(exactly one entry per framework, all 4 present)

**Apply call** (`BUSINESS_DEEP_DIVE_SYSTEM_PROMPT` / skill) -- the
`framework_id` is supplied in the user message from the user's selection,
not chosen by the AI:
```json
{
  "framework_id": "<echoes the user-selected id back>",
  "rag_source": "the 'source' field from the retrieve_knowledge result used",
  "bottom_line": "1 punchy sentence -- the single headline",
  "narrative": "2-3 sentences max, citing real numbers from tool calls",
  "framework_content": "<shape depends on framework_id -- OMITTED entirely (null/absent) when framework_id is bcg_growth_share or three_horizons, since those are fully code-rendered and need no AI-supplied content>",
  "key_implications": [
    {"implication": "...", "type": "risk|opportunity", "evidence_source": "..."}
  ]
}
```

`key_implications` must contain exactly 2-3 entries with `type: "risk"` and
exactly 2-3 with `type: "opportunity"` -- enforced by prompt instruction, and
spot-checked in tests against a stubbed response shape (cannot be enforced
at the schema-validation level without adding a JSON-schema validator,
which is out of scope here).

## Executive POV banner (make the recommendation the hero)

A 5-minute reviewer should get the *judgment* before any chart. Add a
prominent banner at the very top of `Business_Overview.py` (above the
Company snapshot) stating the headline point of view in one confident
sentence. It is **deterministic** (computed in code from real KPIs, same
numbers feeding the existing "Bottom line" insights) so it is always present
on cold load with zero fabrication risk and no AI call required -- e.g.
"Pet is Lemonade's clearest growth engine (+{yoy}% YoY, now {share}% of
company premium), but its loss ratio has plateaued at {lr}% while the
company-wide ratio improved {pts}pts -- the one signal that turns that engine
into a liability at scale." Rendered via a new `style.exec_pov(text)` callout
visually distinct from (and above) the per-section `style.insight` bottom
lines. The wording is a code template over real figures, not a hardcoded
string, so it stays correct if the underlying data changes.

When `framework_id` is `swot`, `framework_content` is:
`{"strengths": [{"point": "...", "evidence_source": "..."}], "weaknesses": [...], "opportunities": [...], "threats": [...]}`
(2-3 entries per quadrant). When `framework_id` is `issue_tree`,
`framework_content` is:
`{"chart_id": "<one of the 6 registry ids>", "supporting_findings": [{"finding": "...", "evidence_source": "..."}]}`
(3-5 supporting findings).

## `$`-as-LaTeX rendering bug fix

Add a small `style.escape_dollar(text: str) -> str` helper
(`text.replace("$", "\\$")`) and apply it everywhere AI-generated free text
is rendered via `st.markdown` or `style.note()`/`style.insight()` across all
pages (`Business_Overview.py`'s narrative/bottom_line/justification/SWOT-or-
issue-tree text, `pages/0_User_Pain_Points.py`'s pain points/risks/
opportunities, `pages/1_Course_of_Action.py`'s approaches/rationale/
bottom_line). Simplest implementation: apply the escape inside
`style.note()` itself (the most common rendering path for AI text), plus at
the handful of direct `st.markdown(f"...{ai_text}...")` call sites that
don't go through `note()`.

## Explicit `framework_choice` on User Pain Points

The Sentiment Analysis Skill's output gains the same `framework_choice`
field used by Business Deep Dive: `{"document_used": "<source field from a
retrieve_knowledge result>", "justification": "1-2 sentences"}`. The AI
names which real, cited `sentiment_methodology` document (NPS origin,
review-bias research, or thematic-coding) is driving how much weight it
gives the raw Trustpilot/complaint-theme data for this run, instead of
implicitly citing sources only inline in the narrative. For consistency
with the downstream Course of Action merge, `risks` and `opportunities` are
also capped at exactly 2-3 each (matching Business Deep Dive's
`key_implications` cap) -- `pain_points` stays uncapped since those don't
feed the downstream merge directly.

Updated schema:
```json
{
  "framework_choice": {"document_used": "...", "justification": "..."},
  "pain_points": [{"pain_point": "...", "evidence_source": "..."}],
  "risks": [{"risk": "...", "evidence_source": "...", "severity": "high|medium|low"}],
  "opportunities": [{"opportunity": "...", "evidence_source": "...", "potential_impact": "high|medium|low"}]
}
```
(exactly 2-3 entries each in `risks` and `opportunities`)

## Explicit `framework_choice` + generalized AI-assumption $ estimation on Course of Action

The Course of Action Skill's output gains the same `framework_choice`
field, naming which real `lemonade_approach` document (flat fee/Giveback,
AI-first claims, synthetic agents/CAC financing, or cross-sell/reinsurance
strategy) is grounding the candidate approaches for this run.

**Why not just let the AI state the dollar figure directly, and why not
keep the original 3 hardcoded `impact.py` functions either:** letting the
AI assert a final dollar number trades away the one fully reproducible
guarantee this app has had throughout (the arithmetic is a Python
function, not a model's token-by-token math) -- "the AI shows its
assumptions and a range" is good transparency, but it doesn't stop a wrong
multiplication or an invented baseline from slipping through. Keeping the
3 hardcoded `pet_loss_ratio_flat` / `pet_new_customer_vs_monetization` /
`pet_loss_ratio_vs_car_improvement` functions, on the other hand, is what
forced the brittle `_infer_pain_point_id()` keyword-matching in the first
place -- the AI now surfaces dynamic, RAG-grounded risks/opportunities that
don't map cleanly onto only 3 fixed cases. The fix is to generalize the
*formula*, not abandon code-computed arithmetic: all 3 existing formulas
already reduce to the same shape, `value = real_base_$_figure ×
(assumed_percentage_points / 100)` -- so one generic tool replaces all 3
specific ones.

**New tool, replacing `get_pain_point_impact_estimate`:**
```
estimate_dollar_value(base_metric: "pet_ifp_m"|"company_ifp_m", low_points: float, base_points: float, high_points: float) ->
    {"base_metric": "...", "base_usd_m": <real value, resolved server-side via kpis, never trusted from the AI>,
     "low_usd_m": ..., "base_usd_m_estimate": ..., "high_usd_m": ...,
     "formula": "base_usd_m * (points / 100)"}
```
The AI supplies only `base_metric` (one of a small enumerated, code-resolved
set -- it cannot name an arbitrary number) and the assumed percentage-point
range it believes is achievable, grounded in something it retrieved from
`consulting_best_practices` or `lemonade_approach` (e.g. citing the
McKinsey insurance-underwriting doc for "a 1-4 point loss-ratio improvement
via underwriter training/pricing analytics is a realistic range"). Code
resolves `base_metric` to the real current $ figure and does the
multiplication -- the AI never states a dollar number itself, only the
inputs to a deterministic formula, with its `confidence` (high|medium|low,
same convention used elsewhere in this app) and a `rationale` citing the
RAG source for why that point-range is realistic.

`pages/1_Course_of_Action.py` per item:
```json
{
  "source_item": "...", "source_type": "risk|opportunity",
  "approaches": [...],
  "chosen_approach": "...", "rationale": "...", "confidence": "high|medium|low",
  "dollar_estimate": {
    "applies": true,
    "base_metric": "pet_ifp_m",
    "low_points": 1, "base_points": 2, "high_points": 4,
    "assumption_rationale": "1-2 sentences citing the retrieved RAG source for this point range"
  }
}
```
(`dollar_estimate.applies: false` when no real base metric/assumption
genuinely fits -- rendered as "no deterministic estimate available," never
a fabricated number.) The page calls `estimate_dollar_value` itself (or
reads it from the transcript if the AI already called it) using the AI's
stated `base_metric`/points, and displays the code-computed `low_usd_m`/
`high_usd_m`/`formula` -- the AI's role is fully limited to selecting
real-world-grounded inputs, never the output number.

`impact.py`'s 3 specific functions and `PAIN_POINT_REGISTRY` are removed in
favor of the single generic `estimate_dollar_value`-backing function.

## Live validation agent (visible in the UI on every AI run)

The hallucination audit shouldn't only be a one-time pre-launch dev
process -- it should be a visible part of the product itself, so a viewer
watches grounding get checked, not just told it was checked once. Two
tiers, both wired into all 3 AI pages (Business Overview Deep Dive, User
Pain Points, Course of Action), right after each AI response is parsed:

**Tier 1 -- automatic deterministic check (always runs, no extra API
call).** New module `pets_bizops/ai/grounding_check.py`:
```python
def check_grounding(ai_output: dict, transcript: list[dict]) -> GroundingReport
```
Walks every citation-bearing field in the AI's JSON output
(`evidence_source`, `rag_source`, `document_used`, and any
`framework_choice.*` source field) and checks each claimed citation against
the REAL transcript: a claimed tool name must match a tool actually called
in the transcript; a claimed RAG source string must match a `source` field
actually returned by a real `retrieve_knowledge` result in the transcript.
A small allow-list (e.g. `"market context"`) covers the handful of
generic, non-citation fallback values the prompts already permit. Returns
a per-claim verdict: `verified_tool` / `verified_rag` / `allowed_generic` /
`unverified`.

UI: immediately after parsing the AI's response, before rendering the
analysis content, show a brief animated step --
`with st.spinner("🔍 Validating claims against retrieved evidence..."):`
running the real check (a short fixed pause, e.g. ~0.6s, may be added
purely so the spinner is visible to a human eye even though the check
itself completes in milliseconds -- the check itself is never faked, only
its visibility is paced). Then a `style.grounding_badge(report)` renders a
one-line summary ("✅ 7/7 citations verified against the real transcript")
with an expander listing every claim, its verdict, and what it matched
against -- and a visibly different state (⚠ amber) if anything comes back
`unverified`.

**Tier 2 -- optional deeper AI audit (one extra Claude call, on demand).**
A "🔬 Run Deep Hallucination Audit" button below the Tier 1 badge on each
page, calling a new `HALLUCINATION_AUDIT_SYSTEM_PROMPT` (no tools needed --
single text-in, text-out call) with the AI's full output JSON + the full
transcript + the system prompt/skill body that produced it, instructed
exactly as in the pre-launch audit procedure above: go claim by claim,
verdict each as grounded/hallucinated/unverifiable against the transcript,
cite the matching transcript entry. Rendered the same way as Tier 1's
badge/expander, clearly labeled "AI-reviewed" vs. Tier 1's
"code-verified" so a viewer can tell which guarantee is which.

## Files to modify

- `Business_Overview.py` -- replace the Deep Dive section's chart-selection
  flow with the framework-chosen flow described above; add the
  `segment_positioning` computation and the 4 framework renderers
  (`_render_bcg_growth_share`, `_render_three_horizons`, `_render_swot`,
  `_render_issue_tree`).
- `pets_bizops/ai/skills/business_deep_dive.md` -- rewrite to describe the
  framework menu, the justification requirement, and the new output schema.
- `pets_bizops/ai/skills/sentiment_analysis.md`,
  `pets_bizops/ai/prompts.py` (`SENTIMENT_ANALYSIS_SYSTEM_PROMPT_SUFFIX`) --
  add `framework_choice` field and the 2-3 cap on risks/opportunities.
- `pets_bizops/ai/skills/course_of_action.md` -- add `framework_choice`
  field and the `dollar_estimate` (base_metric + points + rationale)
  per-item instruction; instruct the AI to never state a dollar figure
  itself, only the inputs to `estimate_dollar_value`.
- `pets_bizops/analysis/impact.py` -- remove the 3 specific functions and
  `PAIN_POINT_REGISTRY`; add a generic `estimate_dollar_value(base_metric,
  low_points, base_points, high_points)` that resolves `base_metric` via
  `kpis` (enumerated set: `pet_ifp_m`, `company_ifp_m`) and returns
  `{base_metric, base_usd_m, low_usd_m, base_usd_m_estimate, high_usd_m,
  formula}`.
- `pets_bizops/ai/tools.py` -- replace `get_pain_point_impact_estimate`
  with `estimate_dollar_value`, input schema as above.
- `pages/1_Course_of_Action.py` -- delete `_infer_pain_point_id()`; render
  `dollar_estimate.applies` per item by calling
  `impact.estimate_dollar_value()` directly with the AI's stated
  base_metric/points (or reading it from the transcript if already called),
  never recomputing or guessing those inputs itself; update to read
  `key_implications` from `business_deep_dive` exactly as today (shape
  unchanged downstream); render the new `framework_choice` badge (same
  visible pattern as Business Deep Dive and User Pain Points).
- `pages/0_User_Pain_Points.py` -- render the new `framework_choice` badge.
- `pets_bizops/ui/style.py` -- add `escape_dollar`; apply inside `note()`;
  add `framework_choice_badge(choice: dict)` and `grounding_badge(report,
  label: str)` helpers reused by all 3 pages for a consistent look.
- All 3 AI pages (`Business_Overview.py`, `pages/0_User_Pain_Points.py`,
  `pages/1_Course_of_Action.py`) -- wire in the Tier 1 deterministic
  grounding check (spinner + badge) immediately after parsing each AI
  response, and the Tier 2 "Run Deep Hallucination Audit" button below it.
- `pages/0_User_Pain_Points.py`, `pages/1_Course_of_Action.py` -- apply
  `escape_dollar` at any direct `st.markdown(ai_text)` call sites not
  covered by `note()`.

## Files to create

- `pets_bizops/ai/grounding_check.py` -- `GroundingReport`
  dataclass + `check_grounding(ai_output, transcript)` (Tier 1).
- `pets_bizops/ai/prompts.py` addition: `HALLUCINATION_AUDIT_SYSTEM_PROMPT`
  (Tier 2).
- `pets_bizops/tests/test_grounding_check.py` -- unit tests for Tier 1:
  a citation matching a real transcript tool call/RAG source verifies; a
  fabricated citation string is flagged `unverified`; an allow-listed
  generic value (e.g. `"market context"`) is `allowed_generic`, not
  flagged.
- `pets_bizops/rag/corpus/consulting_best_practices/swot_analysis_origin.md`
- `pets_bizops/rag/corpus/consulting_best_practices/minto_pyramid_principle.md`
- (rebuild the cached index after adding these: `python -m
  pets_bizops.rag.build_index`)

## Verification

- `pytest -q` -- full suite green. New/updated tests:
  - `style.escape_dollar` unit test (dollar signs escaped, other text
    unchanged).
  - A test stubbing each of the 4 `framework_content` shapes through the
    Business Overview rendering helpers (extracted as testable functions
    where reasonable) to confirm each framework's deterministic numbers
    come from `kpis`/`segment_positioning`, not from the stubbed AI
    response.
  - `test_rag.py` -- `consulting_best_practices` grows from 4 to 6 docs
    (13 total chunks across all 3 corpora); the existing `len(chunks) >= 9`
    assertion still holds, no change needed there.
  - `test_impact.py` rewritten for `estimate_dollar_value`: given
    `base_metric="pet_ifp_m"` and a points range, the returned `low_usd_m`
    /`high_usd_m` are an exact, reproducible function of the REAL current
    `pet_ifp_m` value (read from `kpis.pet_latest_snapshot()` in the test
    itself, not hardcoded) -- proves the arithmetic, not the AI, produces
    the number. A test for an unknown `base_metric` raising/erroring rather
    than silently guessing a value.
  - A test for Course of Action's dollar-estimate rendering: given a
    stubbed item with `dollar_estimate.applies=true` and a given
    base_metric/points, confirm the displayed range matches calling
    `impact.estimate_dollar_value()` directly with those same inputs;
    given `applies=false`, confirm "no deterministic estimate available"
    is shown and no $ figure appears anywhere in the rendered item.
- Headless `streamlit.testing.v1.AppTest` smoke-check confirming all 3
  pages still load with no exception, both before and after a run, using a
  stubbed/mocked `run_tool_loop` for each `framework_id` value and for both
  `dollar_estimate.applies` cases above (real Claude calls aren't
  deterministic enough for CI-style testing).

## Hallucination audit (live-output review, the main ask)

Static code review can't catch a hallucination -- it can only catch a
*structural* gap that would allow one. Catching an actual hallucination
requires looking at a REAL model run's output side-by-side with the REAL
transcript it had available, claim by claim. Procedure, run once
implementation is done and the app is live:

1. Run all 3 AI pages for real (Business Overview Deep Dive → User Pain
   Points → Course of Action), at least 2-3 times each to get varied
   outputs (framework choice and dollar-estimate inputs are live model
   decisions, not fixed).
2. For each run, capture the full triplet already stored in
   `st.session_state`: the AI's final parsed JSON, the tool-call
   transcript (every tool name + input + real result, including any
   `retrieve_knowledge` results with their real chunk text and `source`),
   and the system prompt/skill body that was active.
3. Dispatch a **fresh `general-purpose` subagent with no memory of this
   design conversation** (so it isn't anchored on my assumptions about
   what "should" be true) for each captured triplet, with this exact task:
   "Here is an AI's JSON output, the full tool-call transcript it had
   access to, and the system prompt it was given. Go through the JSON
   output claim by claim -- every number, every cited tool name, every
   `source`/`rag_source`/`document_used` field, every named framework --
   and verify each one is actually present in the transcript. Flag
   anything in the output that is NOT traceable to a specific transcript
   entry, however minor. Report a numbered list: claim, verdict
   (grounded/hallucinated/unverifiable), and the exact transcript entry it
   matched (or didn't)."
4. Any claim the subagent flags as hallucinated or unverifiable is a real
   bug to fix -- either tighten the prompt/skill instructions, or (if it's
   a citation mismatch) fix the rendering code that's supposed to pull the
   citation from the transcript rather than trust the AI's restatement of
   it.
5. Repeat after the fix until a full pass comes back clean on at least 2
   fresh runs per page.

This is the actual hallucination check the user asked for -- it requires
real model output and a real transcript to compare against, so it cannot
be run until implementation is complete and the app has been exercised
live.

## Post-implementation QA pass (static checks)

In addition to the live hallucination audit above, a static review (via
the `code-review` skill or a fresh review subagent) should confirm:

1. No dollar figure anywhere in the 3 pages traces back to AI-generated
   text rather than a real `impact.estimate_dollar_value()` /
   `style.fmt_usd_m` call -- grep for raw `$` followed by a number inside
   any AI-sourced JSON field render path.
2. Every `framework_choice.rag_source`/`document_used` value rendering
   path actually pulls from the transcript/corpus, never restates the
   AI's own claimed source string unverified.
3. Each of the 4 Business Deep Dive frameworks renders correctly when
   forced via a stubbed response (no exception, no missing chart).
4. `escape_dollar` is applied at every render path that displays
   AI-generated free text, not just the ones touched in this change.
5. `pain_point`/`risk`/`opportunity` counts respect the stated caps
   (2-3 each) when instructed, and the UI doesn't silently truncate or
   silently allow overflow without it being obvious which happened.
6. The deleted `_infer_pain_point_id` and the old `get_pain_point_impact_estimate`
   tool have zero remaining references anywhere in the codebase (grep).
7. `pytest -q` is green and the new tests in this spec actually exercise
   the real `kpis`/`impact` functions, not mocks of them, wherever the
   point is to prove real-number reproducibility.
8. `streamlit.testing.v1.AppTest` passes on all 5 pages with no
   session-state prerequisite set (cold start) -- confirms blocking
   `st.warning`/`st.stop()` paths still work, not just the happy path.
9. The RAG Deep Dive page's corpus document counts/listings match the
   actual files on disk after the 2 new corpus docs are added.
10. Dollar amounts render as plain text (not LaTeX) and `key_implications`
    always shows exactly 2-3 risks + 2-3 opportunities across the manual
    click-throughs done for the hallucination audit above.
