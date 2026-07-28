"""User Pain Points: real public customer-sentiment signal, analyzed by the
Lemonade Sentiment Analysis Skill into named pain points and the risks/
opportunities they imply.
"""

from __future__ import annotations

import streamlit as st

from pets_bizops.data import market_sentiment, default_runs
from pets_bizops.ai import tools, client, prompts, skills, jobs
from pets_bizops.ui import style, validation, jobs_ui

st.set_page_config(page_title="User Pain Points -- Pets BizOps Decision OS", page_icon=style.LEMONADE_ICON, layout="wide")
style.inject_global_styles()

# Plain-language labels for tool-based evidence sources, so raw tool names
# (e.g. "get_market_sentiment") never surface to the reader.
_SOURCE_LABELS = {
    "get_market_sentiment": "customer reviews & complaints",
    "get_pet_segment_kpis": "Pet segment KPIs",
    "get_company_kpis": "company KPIs",
    "get_company_financials": "company financials",
}


def _friendly_source(src: str) -> str:
    if not src:
        return src
    token = src.split()[0]  # the AI may append prose after the tool name; take the tool token
    if token in _SOURCE_LABELS:
        return _SOURCE_LABELS[token]
    if token.startswith("get_"):
        return token[4:].replace("_", " ")
    return src

style.headline(
    "User Pain Points",
    "Real customer-sentiment signal, analyzed into named pain points, risks, and opportunities.",
)

st.divider()
style.headline("1. Evidence base (real public signal)")

tp = market_sentiment.TRUSTPILOT_SNAPSHOT
naic = market_sentiment.NAIC_COMPLAINT_INDEX
c1, c2 = st.columns(2)
with c1:
    style.kpi_card("Trustpilot", f"{tp['rating']:.1f} / {tp['scale']:.0f}", f"{tp['review_count']:,} reviews · {tp['as_of']}", None)
with c2:
    style.kpi_card("NAIC complaint index", f"{naic['value']:.2f}", f"≈{naic['value']/naic['industry_baseline']:.0f}× industry baseline ({naic['industry_baseline']:.0f}) · {naic['year']}", None)

st.markdown(
    f"**Sample:** {tp['review_count']:,} public Trustpilot reviews + the NAIC consumer-complaint "
    f"index. **Representativeness:** {market_sentiment.PUBLIC_SENTIMENT_LIMITATION}"
)
st.caption(
    "These real review/complaint themes feed the AI analysis below -- they appear verbatim in "
    "the \"Sources & grounding\" panel once you run it, so every pain point stays traceable to "
    "the real signal."
)

st.divider()
sentiment_skill = skills.load_skill("sentiment_analysis")
style.headline("2. User pain points (AI analysis)", "The AI reads the real review/complaint signal into named pain points, risks, and opportunities -- the conclusions live here, not above.")
style.decision_basis(["sentiment_methodology"], sentiment_skill.body, model_id=client.MODEL)

_JOB = "user_pain_points"
if st.button("Analyze User Pain Points", type="primary"):
    try:
        system_prompt = prompts.SHARED_GUARDRAILS + "\n\n" + sentiment_skill.body + "\n\n" + prompts.SENTIMENT_ANALYSIS_SYSTEM_PROMPT_SUFFIX
        jobs.submit(
            _JOB, client.run_tool_loop,
            system_prompt=system_prompt,
            user_message="Analyze Lemonade Pet's user pain points, risks, and opportunities from the sentiment data.",
            tool_schemas=tools.TOOL_SCHEMAS,
            tool_executor=tools.build_tool_executor(),
        )
        st.rerun()
    except client.MissingApiKeyError as e:
        st.error(str(e))

_done = jobs_ui.poll_result(_JOB)
if _done is not None:
    text, transcript = _done
    try:
        st.session_state.user_pain_points = client.parse_json_response(text)
        st.session_state.user_pain_points_transcript = transcript
        st.session_state.pop("audit_user_pain_points", None)
    except ValueError as e:
        st.error(f"Could not parse the model's response: {e}")

result = st.session_state.get("user_pain_points")
transcript = st.session_state.get("user_pain_points_transcript", [])
is_default = result is None
if is_default:
    result, transcript = default_runs.load_default("user_pain_points")

if result is not None:
    if is_default:
        st.info("📌 Showing a precomputed example analysis (a real prior run). Click **Analyze User Pain Points** above to generate a fresh one live.")

    st.markdown("**🗣 Pain points**")
    for i, p in enumerate(result.get("pain_points", []), 1):
        style.pain_point_card(
            i, p.get("pain_point", ""),
            prevalence=p.get("prevalence", ""),
            significance=p.get("business_significance", ""),
            source=_friendly_source(p.get("evidence_source", "")),
        )

    rcol, ocol = st.columns(2)
    with rcol:
        st.markdown("**⚠ Risks**")
        for i, r in enumerate(result.get("risks", []), 1):
            style.risk_opportunity_card(i, "risk", r.get("risk", ""), impact=r.get("severity", ""))
    with ocol:
        st.markdown("**↑ Opportunities**")
        for i, o in enumerate(result.get("opportunities", []), 1):
            style.risk_opportunity_card(i, "opportunity", o.get("opportunity", ""), impact=o.get("potential_impact", ""))

    validation.render_validation(result, transcript, "user_pain_points")
    style.rag_sources_used(transcript)

    with st.expander(f"Tool calls used ({len(transcript)})"):
        for entry in transcript:
            st.markdown(f"**{entry['tool']}**({entry['input']})")
            st.json(entry["result"])

    # Grounding -- de-emphasized, at the very bottom.
    fc = result.get("framework_choice")
    if fc:
        st.caption(f"🧭 Grounding: {fc.get('document_used', '')} — {fc.get('justification', '')}")

    st.success("Continue to **Business Overview**'s AI Deep Dive (if not done yet), then **Course of Action**.")
