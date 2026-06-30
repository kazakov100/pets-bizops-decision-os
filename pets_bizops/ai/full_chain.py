"""Run the whole analysis chain end-to-end in one call: User Pain Points ->
Risks & Opportunities (a chosen framework) -> Course of Action (on the first
risk surfaced). Pure Python (no streamlit) so it can run on a background
thread; returns every stage's result + transcript for the caller to store.

Used by the "Run the full analysis" button (live) and by
scripts/build_default_runs.py (to bake the precomputed defaults).
"""

from __future__ import annotations

from pets_bizops.ai import tools, client, prompts, skills
from pets_bizops.analysis import impact

DEFAULT_FRAMEWORK = "three_horizons"


def resolve_dollar_estimate(result: dict) -> None:
    """Code computes the $ from the AI's stated assumption; sets result['computed_dollar']."""
    de = result.get("dollar_estimate") or {}
    if not de.get("applies"):
        result["computed_dollar"] = None
        return
    try:
        est = impact.estimate_dollar_value(
            de.get("base_metric", ""), de.get("low_points", 0), de.get("base_points", 0), de.get("high_points", 0)
        ).as_dict()
        result["computed_dollar"] = {
            "range": f"${est['low_usd_m']:.1f}-{est['high_usd_m']:.1f}M/year (base ${est['base_case_usd_m']:.1f}M)",
            "formula": est["formula"],
            "assumption_rationale": de.get("assumption_rationale", ""),
        }
    except (ValueError, TypeError):
        result["computed_dollar"] = None


def run_full_chain(framework_id: str = DEFAULT_FRAMEWORK) -> dict:
    """Returns {stage: {"result": dict, "transcript": list}} for the three AI stages."""
    ts = tools.TOOL_SCHEMAS

    sentiment = skills.load_skill("sentiment_analysis")
    sp = prompts.SHARED_GUARDRAILS + "\n\n" + sentiment.body + "\n\n" + prompts.SENTIMENT_ANALYSIS_SYSTEM_PROMPT_SUFFIX
    text, tr_pain = client.run_tool_loop(sp, "Analyze Lemonade Pet's user pain points, risks, and opportunities from the sentiment data.", ts, tools.build_tool_executor())
    pain = client.parse_json_response(text)

    dd = skills.load_skill("business_deep_dive")
    sp = prompts.SHARED_GUARDRAILS + "\n\n" + dd.body
    text, tr_rno = client.run_tool_loop(sp, f"The user has chosen framework_id = {framework_id}. Apply it as instructed.", ts, tools.build_tool_executor())
    rno = client.parse_json_response(text)
    rno["framework_id"] = framework_id

    risks = [i for i in rno.get("items", []) if i.get("type") == "risk"]
    chosen = risks[0] if risks else (rno.get("items") or [{"title": "Pet's gross loss ratio plateau", "detail": ""}])[0]
    coa = skills.load_skill("course_of_action")
    sp = prompts.SHARED_GUARDRAILS + "\n\n" + coa.body
    um = (
        f"The user selected this risk (from Business Deep Dive):\n{chosen.get('title','')}\n{chosen.get('detail','')}\n\n"
        "Frame it and recommend a course of action, as instructed."
    )
    text, tr_coa = client.run_tool_loop(sp, um, ts, tools.build_tool_executor())
    coa_result = client.parse_json_response(text)
    resolve_dollar_estimate(coa_result)

    return {
        "user_pain_points": {"result": pain, "transcript": tr_pain},
        "business_deep_dive": {"result": rno, "transcript": tr_rno},
        "course_of_action": {"result": coa_result, "transcript": tr_coa},
    }
