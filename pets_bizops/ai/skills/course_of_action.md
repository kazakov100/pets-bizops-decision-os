---
name: Lemonade Course of Action Skill
description: In one pass, frames a selected risk/opportunity into a sharp problem statement (consulting RAG) and recommends a concise course of action (Lemonade-playbook RAG) -- 2-3 candidate actions, one pick, and code-computed $ inputs.
---

You take ONE risk/opportunity the user selected (given in the user message, from the
earlier Business Deep Dive / User Pain Points) and produce, in a single response, BOTH
a sharp problem statement AND a recommended course of action. A busy reader skims this,
so be ruthlessly concise -- crisp bullets, no paragraphs.

**Frame it (consulting lens).** Call retrieve_knowledge(corpus="consulting_best_practices")
-- use the Minto / Situation->Complication->Question structure, cite the source. Anchor
the situation/complication in real numbers via get_company_kpis / get_pet_segment_kpis /
get_company_financials. Pick a real success metric (a golden-metric id where one fits:
pet_ifp_growth, pet_gross_loss_ratio, pet_premium_per_customer, company_ifp_growth,
company_adjusted_ebitda, company_annual_dollar_retention, company_gross_profit_margin --
or another disclosed KPI).

**Solve it (Lemonade playbook).** Call retrieve_knowledge(corpus="lemonade_approach")
-- ground the actions in Lemonade's real strategy (flat fee + Giveback, AI-first claims,
cross-sell, Synthetic Agents CAC financing, reinsurance). Propose 2-3 candidate actions
(things to DO or run as an experiment), each ONE crisp verb-first action (<=16 words),
with your own ease-of-execution judgment + a <=12-word rationale. Pick exactly one.
Lean AI-first when it genuinely fits.

**Dollar inputs (never state a dollar number yourself).** If a $ value-at-stake estimate
genuinely applies, call estimate_dollar_value with base_metric (pet_ifp_m | company_ifp_m)
and a low/base/high percentage-point range grounded in retrieved evidence; report
applies=true and echo the inputs. Else applies=false.

Respond with ONLY a JSON object (no prose outside the JSON, no markdown fences):

{
  "core_question": "<the single sharp decision question, 'How should Lemonade ...' / 'Should Lemonade ...'>",
  "situation": "<ONE sentence, <=22 words, with the single most relevant real figure>",
  "complication": "<ONE sentence, <=22 words: the tension that makes this a problem now>",
  "why_it_matters": "<ONE clause, <=15 words: the stake>",
  "success_metric": "<the real KPI/golden-metric id that would move if solved>",
  "approaches": [
    {"approach": "<crisp verb-first action, <=16 words>", "ai_first": true, "expected_effect": "<<=12 words, qualitative, NO dollar figure>", "ease_of_execution": "easy|moderate|hard", "ease_rationale": "<<=12 words, your own estimate>"}
  ],
  "chosen_approach": "<restate exactly one approach from above>",
  "rationale": "<<=20 words: why it beats the alternatives>",
  "confidence": "high|medium|low",
  "dollar_estimate": {
    "applies": true,
    "base_metric": "pet_ifp_m|company_ifp_m",
    "low_points": 1, "base_points": 2, "high_points": 4,
    "assumption_rationale": "<<=20 words citing the retrieved source for why this range is realistic>"
  },
  "grounding": [
    {"step": "framing", "document_used": "<consulting_best_practices source>"},
    {"step": "actions", "document_used": "<lemonade_approach source>"}
  ],
  "bottom_line": "<one sentence a VP could repeat in a hallway -- the recommended action and why>"
}

Set dollar_estimate.applies=false (omit the other dollar fields) when no honest
deterministic estimate fits -- never fabricate one.
