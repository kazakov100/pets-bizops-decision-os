# Banner Redesign: Situation/Question Up Front, Recommendation at the End

## Context

The Business Overview page currently opens with an `exec_pov` banner that
asserts a conclusion ("...the one signal that turns that engine into a
liability at scale") BEFORE any AI analysis, RAG retrieval, or the user's
framework choice has happened. This pre-empts both the AI's findings and the
user's own judgment, and makes the downstream analysis look like theater
(the answer is already on screen). Per the user, the fix is to split the one
banner into two, tied to two different moments:

- **Up front (deterministic):** state the factual situation + the central
  question the analysis exists to answer -- legitimate to show cold, since
  it's the setup, not the verdict.
- **At the end (after the work):** a synthesized recommendation hero that
  appears only once the analysis chain has actually run.

## Design

Two `style` helpers replace the single `exec_pov`:

1. **`style.situation_banner(text)`** -- top of `Business_Overview.py`.
   Calmer styling (navy, not the pink gradient), labeled "The central
   question". Deterministic: a code template over real KPIs, always present
   on cold load, asserts no conclusion. Text frames facts + the question,
   e.g.: "Pet is Lemonade's fastest-growing line (+X% YoY, now Y% of company
   premium), but its gross loss ratio has held at Z% while the company-wide
   ratio improved Npts to W%. The question this analysis pressure-tests: is
   Pet's growth creating durable value, or scaling an underwriting problem?"

2. **`style.recommendation_hero(text)`** -- the existing pink-gradient
   `exec_pov` CSS is repurposed here (rename `.pbz-exec-pov*` ->
   `.pbz-rec-hero*`, label "Executive recommendation"). Shown ONLY after the
   work is done: at the top of the Course of Action results block, surfacing
   that page's synthesized `bottom_line`. It's the answer, and it appears
   after the analysis, not before it.

The Deep Dive's per-framework `bottom_line` (rendered via `style.insight`)
is unchanged -- it's a section-level finding, not the final recommendation.

## Changes

- `pets_bizops/ui/style.py`:
  - Rename `exec_pov` -> `recommendation_hero`; rename its CSS classes
    `pbz-exec-pov`/`-label`/`-text` -> `pbz-rec-hero`/`-label`/`-text`;
    change the label text to "Executive recommendation".
  - Add `situation_banner(text)` + `.pbz-situation*` CSS (navy left-border
    or navy fill, visually distinct from and calmer than the rec hero).
    Both still run AI text through `escape_dollar` (the situation banner is
    deterministic but harmless to escape; keep it consistent).
- `Business_Overview.py`: replace the top `style.exec_pov(...)` call with
  `style.situation_banner(...)`, reworded to the question framing above
  (still computed from the same real figures: `pet['yoy_ifp_growth_pct']`,
  `share['pet_share_pct']`, `pet['gross_loss_ratio']`,
  `company['gross_loss_ratio']`, `_company_lr_improvement_pts`).
- `pages/1_Course_of_Action.py`: when `result` exists, render
  `style.recommendation_hero(result["bottom_line"])` at the TOP of the
  results block (above the framework badge / per-item list). Remove the
  now-duplicated plain `bottom_line` note near the bottom (or keep only the
  hero -- single source, no duplicate).

## Verification

- `pytest -q` green (no test references `exec_pov`; confirm via grep before
  renaming, update if any).
- `AppTest` on `Business_Overview.py` cold load: situation banner present,
  no recommendation hero, no exception.
- `AppTest` on `pages/1_Course_of_Action.py` with a stubbed
  `course_of_action` session state containing a `bottom_line`: recommendation
  hero renders at the top, no exception.
- Restart server; confirm dollar figures in both banners render as plain
  text (escape_dollar), not LaTeX.
