"""Course of Action: the FINAL page of the chain. ONE step -- pick a
risk/opportunity (from the Business Deep Dive + User Pain Points) and the AI,
in a single pass, frames it into a sharp problem statement (consulting RAG:
Minto / SCQA) AND recommends a course of action (Lemonade-playbook RAG):
2-3 candidate actions + one pick.

Dollar values come only from impact.py's deterministic calculator (never
AI-invented); ease of execution is the AI's own qualitative judgment.
"""

from __future__ import annotations

import streamlit as st

from pets_bizops.analysis import kpis, simulation, impact
from pets_bizops.ai import tools, client, prompts, skills, jobs
from pets_bizops.data import default_runs
from pets_bizops.ui import style, validation, jobs_ui

st.set_page_config(page_title="Course of Action -- Pets BizOps Decision OS", page_icon="🐾", layout="wide")
style.inject_global_styles()

style.headline("Course of Action", "Pick one risk/opportunity; the AI frames it into a sharp problem and recommends a course of action -- in one pass.")

business_deep_dive = st.session_state.get("business_deep_dive")
user_pain_points = st.session_state.get("user_pain_points")
# Fall back to the precomputed default runs so this page works standalone
# (a reviewer can land here without running the upstream pages first).
if business_deep_dive is None:
    business_deep_dive = default_runs.load_default("business_deep_dive")[0]
if user_pain_points is None:
    user_pain_points = default_runs.load_default("user_pain_points")[0]

if business_deep_dive is None or user_pain_points is None:
    st.warning("Run **Business Overview**'s Risks & Opportunities and **User Pain Points** first -- this page builds on what they surface.")
    st.stop()

# Gather every identified risk/opportunity/pain-point into a selectable list.
candidates = []
for it in business_deep_dive.get("items", business_deep_dive.get("key_implications", [])):
    label = it.get("title") or it.get("implication", "")
    if label:
        candidates.append({"label": label, "type": it.get("type", "risk"), "source": "Business Deep Dive", "detail": it.get("detail", "")})
for p in user_pain_points.get("pain_points", []):
    candidates.append({"label": p.get("pain_point", ""), "type": "pain point", "source": "User Pain Points", "detail": ""})
for r in user_pain_points.get("risks", []):
    candidates.append({"label": r.get("risk", ""), "type": "risk", "source": "User Pain Points", "detail": ""})
for o in user_pain_points.get("opportunities", []):
    candidates.append({"label": o.get("opportunity", ""), "type": "opportunity", "source": "User Pain Points", "detail": ""})
candidates = [c for c in candidates if c["label"]]


def _resolve_dollar_estimate(result: dict) -> None:
    """The AI supplies only the inputs (base_metric + assumed point range) in
    result['dollar_estimate']; CODE does the arithmetic. Sets result['computed_dollar'].
    """
    de = result.get("dollar_estimate") or {}
    if not de.get("applies"):
        result["computed_dollar"] = None
        return
    try:
        est = impact.estimate_dollar_value(
            base_metric=de.get("base_metric", ""),
            low_points=de.get("low_points", 0),
            base_points=de.get("base_points", 0),
            high_points=de.get("high_points", 0),
        ).as_dict()
        result["computed_dollar"] = {
            "range": f"${est['low_usd_m']:.1f}-{est['high_usd_m']:.1f}M/year (base ${est['base_case_usd_m']:.1f}M)",
            "formula": est["formula"],
            "assumption_rationale": de.get("assumption_rationale", ""),
        }
    except (ValueError, TypeError):
        result["computed_dollar"] = None


# ---------------------------------------------------------------------------
# One step: pick a problem -> AI frames it (consulting RAG) AND recommends a
# course of action (Lemonade RAG) in a single pass.
# ---------------------------------------------------------------------------
st.divider()
coa_skill = skills.load_skill("course_of_action")

_COA_JOB = "course_of_action"
if not candidates:
    st.info("No risks/opportunities were found in the upstream analyses to choose from.")
else:
    labels = [f"({c['type']}, {c['source']}) {c['label']}" for c in candidates]
    sel_idx = st.selectbox("Which problem do you want to solve?", range(len(labels)), format_func=lambda i: labels[i])
    selected = candidates[sel_idx]

    st.caption("📚 RAG: **consulting_best_practices** (frames the problem) + **lemonade_approach** (grounds the actions).")
    style.model_badge(client.MODEL)
    with st.expander("View system prompt (tells the AI when/how to retrieve from the RAG corpora)"):
        st.markdown(coa_skill.body)

    if st.button("Frame the problem & recommend a course of action", type="primary"):
        try:
            system_prompt = prompts.SHARED_GUARDRAILS + "\n\n" + coa_skill.body
            user_message = (
                f"The user selected this {selected['type']} (from {selected['source']}):\n"
                f"{selected['label']}\n{selected.get('detail', '')}\n\n"
                "Frame it and recommend a course of action, as instructed."
            )
            jobs.submit(
                _COA_JOB, client.run_tool_loop,
                system_prompt=system_prompt,
                user_message=user_message,
                tool_schemas=tools.TOOL_SCHEMAS,
                tool_executor=tools.build_tool_executor(),
            )
            st.rerun()
        except client.MissingApiKeyError as e:
            st.error(str(e))

_coa_done = jobs_ui.poll_result(_COA_JOB)
if _coa_done is not None:
    text, transcript = _coa_done
    try:
        result = client.parse_json_response(text)
        _resolve_dollar_estimate(result)
        st.session_state.course_of_action = result
        st.session_state.course_of_action_transcript = transcript
        st.session_state.pop("audit_course_of_action", None)
    except ValueError as e:
        st.error(f"Could not parse the model's response: {e}")

result = st.session_state.get("course_of_action")
coa_transcript = st.session_state.get("course_of_action_transcript", [])
coa_is_default = result is None
if coa_is_default:
    result, coa_transcript = default_runs.load_default("course_of_action")

if result is not None:
    if coa_is_default:
        st.info("📌 Showing a precomputed example (a real prior run on one problem). Pick a problem and click the button above to run a fresh one live.")
    # Headline answer first (pink hero), then the question (pink), then the
    # quieter framing detail, then the actions with the pick called out (green).
    if result.get("bottom_line"):
        style.recommendation_hero(result["bottom_line"])
    style.insight("Core question", result.get("core_question", ""))
    st.markdown(f"- **Situation:** {style.escape_dollar(result.get('situation',''))}")
    st.markdown(f"- **Complication:** {style.escape_dollar(result.get('complication',''))}")
    st.markdown(f"- **Why it matters:** {style.escape_dollar(result.get('why_it_matters',''))}")
    st.markdown(f"- **Success metric:** `{result.get('success_metric','')}`")

    computed = result.get("computed_dollar")
    if computed:
        st.caption(style.escape_dollar(f"💰 Estimated value at stake: {computed['range']}"))
        with st.expander("How this estimate was computed (code-computed from the AI's stated assumption)"):
            st.caption(style.escape_dollar(computed.get("formula", "")))
            st.caption(f"Assumption (AI, RAG-grounded): {computed.get('assumption_rationale', '')}")

    st.markdown("**What to do — candidate actions**")
    chosen = result.get("chosen_approach", "")
    for a in result.get("approaches", []):
        approach = a.get("approach", "")
        ai_badge = " 🤖" if a.get("ai_first") else ""
        st.markdown(
            f"- **{style.escape_dollar(approach)}**{ai_badge} "
            f"<span style='color:#9a9a9a;font-size:0.82rem;'>· {a.get('ease_of_execution','?')} to execute · {style.escape_dollar(a.get('expected_effect',''))}</span>",
            unsafe_allow_html=True,
        )
    if chosen:
        style.recommended_action(chosen)
        st.caption(f"Why this one: {result.get('rationale', '')} • Confidence: {result.get('confidence', '?')}")

    validation.render_validation(result, coa_transcript, "course_of_action")
    style.rag_sources_used(coa_transcript)
    grounding = result.get("grounding", [])
    if grounding:
        parts = " • ".join(f"{g.get('step','')}: {g.get('document_used','')}" for g in grounding)
        st.caption(f"🧭 Grounding — {parts}")

    with st.expander(f"Tool calls used ({len(coa_transcript)})"):
        for entry in coa_transcript:
            st.markdown(f"**{entry['tool']}**({entry['input']})")
            st.json(entry["result"])

    st.caption(
        "Grounded entirely in Lemonade's real public disclosure and real, cited external "
        "knowledge -- no internal Lemonade data, no experiment was actually run."
    )

st.divider()
with st.expander("Optional: check feasibility of a specific metric target"):
    st.caption("A deterministic feasibility check -- compares the pace required to hit a target against the metric's real historical pace. No AI involved.")
    metric_ids = list(kpis.GOLDEN_METRICS.keys())
    metric_labels = {m: kpis.GOLDEN_METRICS[m]["label"] for m in metric_ids}
    selected_metric = st.selectbox("Golden metric", metric_ids, format_func=lambda m: metric_labels[m])
    metric_meta = kpis.GOLDEN_METRICS[selected_metric]
    series = kpis.golden_metric_series(selected_metric)
    current_value = float(series.iloc[-1]["value"])
    unit = metric_meta["unit"]

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        if unit == "pct":
            target_pct_points = st.slider("Target value", min_value=0, max_value=100, value=round(current_value * 100), step=1, format="%d%%")
            target_value = target_pct_points / 100
        else:
            target_value = st.number_input("Target value ($)", value=float(round(current_value * 1.1, 0)), step=10.0)
    with tcol2:
        horizon_quarters = st.slider("Horizon (quarters from now)", min_value=1, max_value=12, value=4)

    if st.button("Run Feasibility Check"):
        sim = simulation.simulate_target(
            series=series,
            target_value=target_value,
            horizon_quarters=horizon_quarters,
            direction=metric_meta["direction"],
            metric_id=selected_metric,
        ).as_dict()
        badge = {"within historical average pace": "🟢", "requires sustaining the best historical quarter, every quarter": "🟡", "trivial-or-wrong-direction": "⚪"}.get(sim["feasibility_label"], "🔴")
        st.markdown(f"### {badge} {sim['feasibility_label']}")
        style.note(sim["feasibility_detail"])
