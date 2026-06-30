# Pets BizOps Decision OS — Design Spec

Date: 2026-06-20
Status: Approved, ready for implementation planning

## Purpose

A portfolio project demonstrating "mini-COO" thinking for a BizOps Senior Lead role
(Lemonade, Pet Insurance line): diagnose business problems from data, connect data to
decisions, evaluate trade-offs, design experiments, and learn from results — using AI
as a reasoning layer over deterministically computed evidence, not as a chatbot or a
plain dashboard.

All data is **synthetic** and clearly labeled as such throughout the UI and README.
No real Lemonade data, no unsupported actuarial claims — uncertainty and missing
evidence are surfaced explicitly rather than smoothed over.

## 1. MVP Scope

**Flagship scenario, full loop:** pricing increase, built end-to-end through diagnosis
→ hypotheses → decision → experiment → results → memo → memory.

**Primary KPI for the flagship decision:** all trade-off framing, recommendation,
experiment success criteria, and evaluation are anchored on a single primary metric —
**expected 12-month underwriting contribution per quoted customer**. Named
"underwriting contribution," not "contribution margin," because no reliable CAC input
exists in this model (see formula below) — the name must not overstate what's actually
measured. This is the metric that already nets the per-policy economics against the
conversion loss, so "did the pricing change help" has one unambiguous answer instead of
a debate between separate margin and conversion numbers. Conversion rate, churn, and
loss ratio remain tracked as secondary/guardrail metrics, never as competing primary
metrics.

**Formula (computed in `analysis/kpis.py`):**

```
expected_12mo_underwriting_contribution_per_quote =
    (
        expected_12mo_earned_premium
        - expected_12mo_claim_cost
        - variable_support_cost
        - payment_processing_cost
    ) / total_quotes   # denominator includes non-converted quotes
```

- **Same time window for premium and claims, always:** both `earned_premium` and
  `claim_cost` are computed as **expected 12-month values** for every quote/policy,
  regardless of how long the policy has actually been in force. Without this, recently
  written policies look artificially profitable simply because they haven't had time to
  file claims yet — this is the single most important correctness rule in the data
  model. Concretely: `expected_12mo_claim_cost` is derived from each cohort's
  age/breed/pet_type claim-rate and severity distributions (the same generative
  parameters used to create the synthetic claims), not from claims actually observed
  in-sample to date.
- **No acquisition cost (CAC) term** is included — the schema has no reliable
  per-channel CAC input, and the brief's risk list already flags "missing CAC by
  channel" as a hypothesis-ranking limitation. Including a fabricated CAC number would
  contradict the "don't invent evidence" principle. If CAC is added later, the metric
  name reverts to "contribution margin" — not before.
- `variable_support_cost` derives from `support_contacts × per_contact_cost`.
  `payment_processing_cost` is a small fixed percentage of premium. Both are
  named constants in `scenario_config`, not fitted.

Two secondary scenarios (claims-flow improvement, acquisition-channel quality issue)
are embedded in the synthetic data and surfaced through KPI/anomaly detection and
driver analysis, but do not get their own full workflow in v1.

**In scope:**
- Synthetic data generation (config-driven, not hardcoded)
- Deterministic KPI computation, anomaly detection, driver decomposition
- A structured evidence layer between analysis and AI
- LLM (Claude) tool-calling for diagnosis, hypothesis generation/ranking, options
  comparison, experiment plan generation, results evaluation, executive memo
- Explicit recommendation (AI) vs. decision (user-approved) separation
- Persistent institutional memory (SQLite), populated only by approved decisions
- Tests for the deterministic core (KPIs, drivers, scenario generation, pre/post comparison)

**Out of scope for v1:**
- Real file upload (data is generated/loaded internally via a button)
- A real standalone MCP server process (tools are Claude API tool-calling functions;
  MCP exposure is an explicit future-work item, not implied as built)
- Full workflows for the two secondary scenarios
- Auth/multi-user, real actuarial pricing models

## 2. Architecture

```
pets-bizops/
├── data/
│   ├── scenario_config.py   # explicit per-scenario config: trigger dates, affected
│   │                         # segments, expected effect sizes, embedded patterns
│   ├── generator.py          # synthetic data generation, reads scenario_config
│   └── store.py              # load/save datasets (parquet/csv): policies + quotes,
│                               # pre/post period
├── analysis/
│   ├── kpis.py                # deterministic KPI computation (contribution margin
│   │                           # per quote, conversion, churn, loss ratio, etc.)
│   ├── anomaly.py             # period-over-period KPI change/anomaly detection
│   ├── drivers.py             # driver decomposition (which segments/channels explain
│   │                           # a KPI move)
│   ├── evidence.py            # structured Evidence layer between analysis and AI.
│   │                            # Returns objects like:
│   │                            # {finding, segment, confidence, supporting_metrics,
│   │                            #  limitations}
│   │                            # This is what the LLM receives — never raw numbers
│   │                            # to free-interpret.
│   └── experiment_design.py   # NEW: deterministic sample-size / minimum-detectable-
│                                # effect calculation and guardrail-threshold checks.
│                                # AI explains rationale; this module computes the
│                                # numbers, same separation principle as hypothesis
│                                # ranking.
├── ai/
│   ├── tools.py               # tool-calling functions: get_business_kpis,
│   │                           # analyze_loss_ratio, compare_customer_segments,
│   │                           # evaluate_pricing_change, review_experiment_results,
│   │                           # generate_executive_memo, get_related_history
│   ├── client.py              # Claude API wrapper, tool-calling loop
│   └── prompts.py             # system prompts per workflow stage
├── memory/
│   ├── store.py                # SQLite: approved Decisions, Experiments, Outcomes
│   └── models.py               # Decision, Experiment, Outcome, Recommendation schemas
├── workflow/
│   └── engine.py                # orchestrates the flow, holds session state, enforces
│                                  # recommendation -> user approval -> decision gate
├── app.py                       # Streamlit entrypoint
├── pages/                       # Streamlit pages: Overview, Diagnose, Decide & Experiment,
│                                  # Results & Memo
└── tests/
    ├── test_kpis.py
    ├── test_drivers.py
    ├── test_scenario_generation.py   # verifies embedded effect sizes are statistically
    │                                  # recoverable from generated data
    ├── test_experiment_comparison.py # pre/post experiment comparison logic
    └── test_experiment_design.py     # sample-size / MDE / guardrail-check logic
```

**Key boundaries:**
- `data/` and `analysis/` are pure Python/pandas, no LLM calls, fully testable and
  deterministic.
- `analysis/evidence.py` is the contract boundary: the AI layer only ever consumes
  `Evidence` objects, never raw rows or unstructured numbers, and every Evidence object
  carries its own `limitations`.
- `ai/` reasons over evidence via tool calls; it never invents stats.
- `memory/` is the only persistent store, written to only via an explicit user-approved
  `Decision`. AI `Recommendation` objects are ephemeral / UI-only until approved.
- `workflow/engine.py` is the single source of truth for step order and session state,
  so Streamlit pages stay thin and don't desync.
- This boundary design makes it straightforward to later swap `data/store.py` and
  `memory/store.py` internals for a real DB, and to later wrap `ai/tools.py` in an
  actual MCP server, without touching the analysis or workflow layers.

**Terminology note:** the tool functions in `ai/tools.py` are exposed to Claude via the
Claude API's native **tool-calling** (tool use) mechanism. This is *not* a running MCP
server. The README and any demo narration must describe it accurately as tool calling,
with "expose these tools via a real MCP server" listed as explicit future work.

## 3. Synthetic Data Model

**Volume:** ~12,000 **policies** plus a backing **quotes** table (~30,000–40,000 rows,
since not every quote converts), spanning a "before" and "after" period relative to the
pricing change, so period-over-period comparison is built into generation.

**Two tables, because conversion needs a denominator of people who were quoted but
didn't necessarily buy — `policies` alone can't express that:**

**`quotes`** (the conversion funnel; one row per quote):

| Field | Notes |
|---|---|
| quote_id | unique |
| customer_id | links repeat quotes from the same prospect |
| quote_date | when the quote was generated |
| quoted_premium | the price shown to the prospect |
| state | ~10 US states |
| pet_age | drives both quoted premium and downstream claim risk |
| acquisition_channel | organic, paid_search, paid_social, partner, referral |
| experiment_group | control / treatment, assigned at quote time for the pricing experiment |
| converted | boolean — did this quote become a policy |
| policy_id | nullable; set only when `converted = true`, links to `policies` |

**`policies`** (one row per converted quote — i.e. `policy_id` here is always also
present in `quotes.policy_id`):

| Field | Notes |
|---|---|
| policy_id | unique |
| pet_type | dog / cat / other, weighted |
| breed | category list per pet_type, affects claim cost distribution |
| pet_age | drives claim probability |
| state | ~10 US states, label-level variation only (no real regulatory modeling) |
| acquisition_channel | organic, paid_search, paid_social, partner, referral |
| policy_start_date | spread across before/after periods |
| premium | base + state/breed/age adjustments; bumped post pricing_change_date for treatment cohort |
| deductible | low/mid/high tiers |
| renewal_status | renewed / not_yet_due / lapsed |
| churn | boolean, derived from renewal_status + price sensitivity + claims experience |
| claim_count | Poisson-ish by pet_type/age/breed |
| total_claim_cost | derived from claim_count × severity distribution |
| support_contacts | count, elevated for poor claims-flow segment pre-improvement |
| experiment_group | control / treatment, used for the pricing experiment cohort |
| pricing_change_date | global date marking the pricing initiative |
| feature_change_date | global date marking the claims-flow improvement |

**`data/scenario_config.py` (or YAML) defines, per scenario, explicitly and separately
from the generator:**
- trigger date(s)
- affected segments (e.g. states, channels, cohorts)
- expected effect size(s) (e.g. conversion delta, loss-ratio delta)
- which embedded pattern it represents

This lets scenarios be tuned or swapped without touching generator mechanics.

**Three embedded scenarios:**

1. **Pricing increase (flagship).** Treatment group gets a configured premium increase
   (e.g. +12–15%) after `pricing_change_date`. Effect: conversion (new policy volume)
   drops in the treatment cohort, loss ratio improves, margin per policy rises. Control
   group unaffected — gives a clean causal comparison.
2. **Claims-flow improvement.** After `feature_change_date`, customers with a claim
   filed post-change show lower `support_contacts` and higher renewal/retention than
   pre-change claimants. Surfaced via driver analysis, not a full workflow.
3. **Acquisition campaign quality issue.** One channel shows a volume ramp in a
   configured window with a materially worse loss ratio (`claim_count` /
   `total_claim_cost` per policy) than other channels. Surfaced as an anomaly/driver
   finding, not a full workflow.

All effect sizes are explicit named constants in `scenario_config`, so generation has a
known ground truth and `test_scenario_generation.py` can assert the analysis layer
recovers it.

**Pre-defined success criteria (fixed before any data is generated or any experiment is
run, not interpreted after the fact):**
- **Primary:** expected 12-month underwriting contribution per quoted customer in
  treatment states improves by at least `CONTRIBUTION_UPLIFT_TARGET` (e.g. +8%) vs.
  control, after the pricing change.
- **Guardrail (conversion):** conversion rate in treatment states must not decline by
  more than `MAX_CONVERSION_DECLINE` (e.g. 12 points) vs. control.
- **Guardrail (churn):** churn rate in treatment states must not increase by more than
  `CHURN_GUARDRAIL` (e.g. 3 points) vs. control.
- **Decision rule per state:** a state is classified "success" only if the primary
  margin target is met AND both guardrails hold; "failed" if any guardrail is
  breached, regardless of margin performance; "inconclusive" if the primary target is
  missed but no guardrail is breached.

These thresholds live in `scenario_config` and are passed into
`analysis/experiment_design.py` and `analysis/evidence.py` so the per-state
success/failure classification used in Results & Memo is computed deterministically,
not asserted by the LLM after seeing the outcome.

## 4. AI Workflow

The LLM never sees raw rows. It receives `Evidence` objects (from `analysis/evidence.py`)
via tool calls, at these points:

1. **Diagnose** — given KPI deltas + anomaly flags for the selected issue, calls
   `analyze_loss_ratio`, `compare_customer_segments` to pull Evidence objects, then
   produces a structured diagnosis: what changed, by how much, in which segments, with
   a confidence level and limitations per claim.
2. **Hypothesize** — generates 4–6 candidate explanations, each scored on evidence
   strength, estimated impact, and confidence against a fixed rubric; explicitly flags
   missing data needed to validate (e.g. "no CAC by channel, so ROI ranking is
   incomplete"). The LLM proposes per-hypothesis scores against the rubric; ranking
   itself is computed in code, not asserted by the LLM.
3. **Compare options** — given 2–3 candidate actions, produces a trade-off table
   (impact on margin/conversion/churn, risk, confidence) and an AI **Recommendation**
   with explicit caveats. This is *not* yet a Decision.
4. **User approval gate** — the user reviews the Recommendation and explicitly
   approves (or edits/rejects) it. Only on approval does a `Decision` object get
   created; only `Decision` objects are persisted to memory.
5. **Experiment design** — turns the approved Decision into a structured plan:
   hypothesis statement, primary/guardrail KPIs, target segment, success criteria
   (from the pre-defined thresholds in `scenario_config`), and sample size / minimum
   detectable effect / duration. The sample-size and MDE numbers are computed by
   `analysis/experiment_design.py`, not by the LLM — the AI's role is limited to
   explaining the rationale in plain language, mirroring the hypothesis-ranking
   principle (LLM proposes/explains, code computes).
6. **Post-results evaluation** — given computed experiment KPIs from the "after"
   dataset and the deterministic per-state success/failed/inconclusive
   classification (via `review_experiment_results`, using the fixed decision rule
   from `scenario_config`), the AI explains *why* each state landed where it did and
   proposes a next iteration — it does not re-decide what counts as success. Reads
   `memory/store.py` via a `get_related_history` tool so it can reference prior
   decisions/experiments with overlapping KPIs or segments.
7. **Memo generation** — `generate_executive_memo` assembles diagnosis, hypotheses,
   the approved decision, the experiment, and results into a structured one-pager:
   situation, recommendation, evidence, risks/uncertainty, next steps. Saved to
   memory alongside the Decision/Outcome record.

**Guardrails enforced via prompts:** every AI claim must cite the Evidence object that
backed it; missing data/uncertainty must be flagged explicitly rather than smoothed
over; language must stay "directional signal," never implying actuarial precision.

## 5. Main Screens (Streamlit, 4 areas)

1. **Overview** — "Load Synthetic Pet Insurance Dataset" button with a persistent
   "SYNTHETIC DATA — for demonstration purposes only" banner; executive KPI dashboard
   with period-over-period deltas and anomaly callouts; decision log (institutional
   memory) showing past approved decisions and outcomes.
2. **Diagnose** — issue selection (pricing trade-off pre-selected as flagship); AI
   diagnosis with driver breakdown and confidence/limitations; ranked hypothesis cards
   (evidence strength, impact, confidence, missing-data chips).
3. **Decide & Experiment** — trade-off comparison table across candidate actions; AI
   Recommendation banner with rationale and caveats; explicit **Approve & Save**
   action that creates a Decision; experiment plan view (hypothesis, KPIs, guardrails,
   segment, duration, success criteria) with a "Load Results" action.
4. **Results & Memo** — loads the "after" dataset for the experiment cohort; actual vs.
   target KPIs; segment breakdown of where it worked/failed; AI's updated
   recommendation for the next iteration; rendered executive memo (markdown,
   exportable), auto-saved to memory tied to the Decision.

Navigation is a guided linear flow (sidebar shows the 4 stages as progress), reinforcing
"operating system for decisions" rather than "dashboard with tabs."

## 6. First Demo Scenario (walkthrough)

1. Load synthetic dataset (12k policies, before/after pricing change).
2. Overview shows: conversion down ~9% in the after period for the treatment cohort,
   margin per policy up, loss ratio improved — flagged as an anomaly cluster.
3. User opens Diagnose, selects "Pricing change impact."
4. AI diagnosis attributes the conversion drop to the treatment cohort post
   `pricing_change_date`, controls for unaffected segments, states confidence, flags
   missing CAC/elasticity-by-state data as a limitation.
5. AI generates ranked hypotheses (e.g. "broad increase overcorrected in
   price-sensitive states," "increase improved unit economics enough to offset volume
   loss," "increase disproportionately drove churn in the renewal-due cohort").
6. Decide & Experiment: trade-off table across broad rollout / state-segmented pricing
   / rollback; AI recommends segmented rollout in low-elasticity states. User reviews
   and clicks **Approve & Save** → Decision is created and persisted.
7. Experiment plan generated from the Decision: 12% increase in 3 selected states only;
   guardrails and success criteria pulled from the pre-defined `scenario_config`
   thresholds (margin uplift target, max conversion decline, churn guardrail);
   sample size/MDE computed by `analysis/experiment_design.py`.
8. User clicks "Load Results" → after-dataset (additional `quotes` + `policies` rows
   for the experiment cohort) loads.
9. Deterministic classification: 2/3 states succeed, 1 fails (churn guardrail
   breached). AI explains why the failing state likely breached guardrail and
   recommends a smaller increase there next round.
10. Executive memo generated and saved to memory, linked to the Decision and Outcome.

## 7. Risks & Assumptions

- **LLM cost/latency:** multiple tool-calling steps per session; mitigate with caching
  of Evidence objects per session and an explicit "regenerate" action rather than
  auto-rerunning on every interaction.
- **Believability of synthetic effects:** effect sizes must be clearly detectable but
  not so large they look fabricated; `test_scenario_generation.py` is the safety net —
  tune `scenario_config` until the test's recovered effect size matches the configured
  one within tolerance.
- **Scope creep:** the 4-area guided flow is still substantial; phasing below caps v1
  strictly to the flagship scenario plus secondary-scenario surfacing only via
  anomaly/driver detection (no secondary full workflows).
- **Streamlit session-state complexity:** `workflow/engine.py` plus `st.session_state`
  must be the single source of truth for step state (selected issue, diagnosis,
  recommendation, approved decision, experiment plan, results), or pages will desync.
- **Recommendation/Decision conflation risk:** must be enforced in code (not just UI
  convention) that `memory/store.py` only accepts `Decision` objects with an
  `approved_at` timestamp — never raw `Recommendation` objects.
- **Fixed-threshold tuning risk:** success/guardrail thresholds in `scenario_config`
  are set before generation, but the generator's actual effect sizes must be tuned so
  the demo produces an interesting mixed outcome (2/3 success, 1 fail) rather than a
  trivial all-pass or all-fail result — validated by `test_experiment_comparison.py`
  and `test_experiment_design.py` against the fixed thresholds, not adjusted after
  seeing results.
- **Quotes/policies join integrity:** `generator.py` must guarantee every
  `policies` row has exactly one corresponding `quotes` row with `converted = true`
  and matching `policy_id`; covered by a generation-integrity check in
  `test_scenario_generation.py`.
- **Assumption:** `ANTHROPIC_API_KEY` provided via environment variable; no key
  management UI needed.
- **Assumption:** local SQLite file is sufficient persistence; no auth/multi-user
  concerns; single local user/session at a time.

## 8. Phased Implementation Plan

- **Phase 0** — Scaffold repo; `data/scenario_config.py` (including fixed success
  thresholds) + `data/generator.py` (quotes + policies tables) + `analysis/kpis.py`
  (contribution margin per quote as primary KPI) + `analysis/drivers.py`;
  `tests/test_scenario_generation.py` and `tests/test_kpis.py` proving the 3 embedded
  scenarios are statistically recoverable from generated data alone. No AI, no UI yet.
- **Phase 1** — `analysis/evidence.py` + `analysis/anomaly.py`; Streamlit Overview page
  (load data, KPI dashboard, anomaly flags) — fully deterministic, no LLM.
- **Phase 2** — `ai/tools.py` + `ai/client.py` (Claude tool-calling loop) +
  `ai/prompts.py`; wire the Diagnose page end-to-end (diagnosis + ranked hypotheses).
- **Phase 3** — Decide & Experiment page: options comparison, AI Recommendation,
  Approve & Save gate, `memory/store.py` + `memory/models.py`,
  `analysis/experiment_design.py` (+ `tests/test_experiment_design.py`), experiment
  plan generation.
- **Phase 4** — Results & Memo page: "after" dataset load,
  `tests/test_experiment_comparison.py`, deterministic per-state success/fail
  classification against fixed thresholds, AI evaluation/explanation, executive memo
  generation, persistence of Outcome tied to Decision.
- **Phase 5** — Decision log surfaced on Overview; seed 1–2 fictional prior
  decisions/outcomes so institutional memory is visible from first run; memory-aware
  diagnosis/memo via `get_related_history`.
- **Phase 6** — Polish: styling, synthetic-data disclaimers, uncertainty/caveat
  language audit, README (accurately describing tool-calling vs. MCP, with MCP listed
  as future work) aimed at a hiring-manager audience.
