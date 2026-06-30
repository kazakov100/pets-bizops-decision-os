"""Pets BizOps Decision OS -- Overview page.

Shows REAL, publicly disclosed Lemonade Inc. (NASDAQ: LMND) metrics for the
Pet insurance line, sourced from quarterly SEC-filed shareholder letters.
No synthetic data anywhere in this app. The Company/Pet snapshot KPI cards
below are fully deterministic (no LLM calls). The "Risks & Opportunities"
section uses an AI call (Risks & Opportunities Skill, grounded in the
consulting_best_practices RAG corpus): the user picks a strategic framework,
and the AI maps where the risks and opportunities are through that lens --
plotting them on a code-rendered Impact x Confidence map. Every number cited
comes from a real tool call; supporting real-data charts render in code.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from pets_bizops.data import real_lemonade_data as data
from pets_bizops.data import default_runs
from pets_bizops.analysis import kpis, impact
from pets_bizops.ai import tools, client, prompts, skills, jobs, full_chain
from pets_bizops.rag import embeddings
from pets_bizops.ui import style, validation, jobs_ui

st.set_page_config(page_title="Business Overview -- Pets BizOps Decision OS", page_icon=style.LEMONADE_ICON, layout="wide")
style.inject_global_styles()

# Warm the embedding model in the background at startup so the first
# retrieve_knowledge call doesn't pay the one-time ~8s model load mid-request.
embeddings.prewarm()

style.headline("Business Overview", "Lemonade's Pet insurance business, at a glance.")

with st.expander("ℹ️ How this works — the approach", expanded=False):
    st.markdown(
        "- **The flow:** read the company's status → surface the main **risks & opportunities** → "
        "examine **user pain points** → merge it all into a **course of action**.\n"
        "- **Every stage is LLM-driven, each grounded in its own purpose-built RAG corpus** + a "
        "tailored prompt telling the model what to retrieve: *consulting frameworks* (risks & "
        "opportunities), *sentiment-analysis methodology* (user pains), and *Lemonade's own stated "
        "strategy* (course of action).\n"
        "- **Real data only:** every figure comes from Lemonade's SEC disclosures via tools — the AI "
        "explains and frames, code computes; it never invents a number.\n"
        "- **Hallucination safeguard:** each run is checked by a separate validator — a deterministic "
        "pass that verifies every citation against the actual tool-call transcript, plus an optional "
        "second-model audit.\n"
        "- **No setup needed:** each page shows a precomputed example by default; run any step (or all "
        "three at once) live whenever you want."
    )

company = kpis.company_latest_snapshot()
pet = kpis.pet_latest_snapshot()
pet_loss_ratio_series = kpis.pet_loss_ratio_series()
share = kpis.pet_share_of_company()

# Run-everything button: runs the whole chain (Risks & Opportunities -> User
# Pain Points -> Course of Action) in one background job. Each page already
# shows a precomputed example; this regenerates all three live.
_FULL_JOB = "full_chain"
st.caption("Each AI page shows a precomputed example by default. To regenerate all three live in one go:")
if st.button("▶️ Run the full analysis live (Risks & Opportunities → User Pain Points → Course of Action)", type="primary"):
    try:
        jobs.submit(
            _FULL_JOB, full_chain.run_full_chain,
            framework_id=st.session_state.get("chosen_framework_select", full_chain.DEFAULT_FRAMEWORK),
        )
        st.rerun()
    except client.MissingApiKeyError as e:
        st.error(str(e))

_full_done = jobs_ui.poll_result(_FULL_JOB, running_msg="⏳ Running the full analysis (3 model passes, ~a few minutes) — you can switch tabs and come back; it won't be cancelled.")
if _full_done is not None:
    for _key, _payload in _full_done.items():
        st.session_state[_key] = _payload["result"]
        st.session_state[f"{_key}_transcript"] = _payload["transcript"]
        st.session_state.pop(f"audit_{_key}", None)
    st.success("Full analysis complete — all three AI pages now show this fresh live run.")

# Executive takeaway -- the answer-first hero. Reads the SAME Risks &
# Opportunities run that drives the section lower on the page (live run in
# session, else the precomputed default), so the top block and the detail
# never disagree. The KPI $ impact is code-computed from the AI's stated
# assumption -- never an AI-asserted figure.
_dd = st.session_state.get("business_deep_dive")
if _dd is None:
    _dd = default_runs.load_default("business_deep_dive")[0]
_exec = (_dd or {}).get("executive_summary")
if _exec:
    _kpi = _exec.get("kpi_impact", {})
    _computed = impact.resolve_estimate(_kpi.get("dollar_estimate"))
    style.executive_takeaway(
        _exec.get("key_takeaway", ""), _exec.get("why_it_matters", ""),
        _exec.get("recommended_action", ""), _kpi.get("metric_label", ""),
        _computed,
    )
    if _computed:
        with st.expander("How the KPI impact was computed (code-computed from the AI's stated assumption)"):
            st.caption(style.escape_dollar(_computed.get("formula", "")))
            st.caption(f"Assumption (AI, RAG-grounded): {_computed.get('assumption_rationale', '')}")


def labeled_vertical_bar(bars: alt.Chart, label_field: str) -> alt.Chart:
    """A vertical bar chart layered with its value labels above each bar."""
    text = bars.mark_text(align="center", baseline="bottom", dy=-4, color=style.TEXT, fontWeight="bold").encode(
        text=alt.Text(f"{label_field}:N")
    )
    return bars + text


def labeled_horizontal_bar(bars: alt.Chart, label_field: str) -> alt.Chart:
    """A horizontal bar chart layered with its value labels at the bar end."""
    text = bars.mark_text(align="left", baseline="middle", dx=4, color=style.TEXT, fontWeight="bold").encode(
        text=alt.Text(f"{label_field}:N")
    )
    return bars + text


customers_df = kpis.company_quarterly_series().dropna(subset=["customers"])
customers_yoy_pct = (
    customers_df.iloc[-1]["customers"] / customers_df.iloc[-5]["customers"] - 1
    if len(customers_df) >= 5 else None
)

net_loss_df = kpis.company_quarterly_series().dropna(subset=["net_loss_m"])
net_loss_qoq_pct = (
    net_loss_df.iloc[-1]["net_loss_m"] / net_loss_df.iloc[-2]["net_loss_m"] - 1
    if len(net_loss_df) >= 2 else None
)

st.divider()
style.headline("Company snapshot", f"Most recent disclosed quarter: {company['quarter']}")
col1, col2, col3, col4 = st.columns(4)
with col1:
    style.kpi_card("In-Force Premium", style.fmt_usd_m(company['in_force_premium_m']), f"{company['ifp_yoy_growth_pct']:+.0%} YoY", True)
with col2:
    style.kpi_card(
        "Customers", f"{company['customers'] / 1_000_000:.2f}M",
        f"{customers_yoy_pct:+.0%} YoY" if customers_yoy_pct is not None else company["quarter"],
        True if customers_yoy_pct is not None else None,
    )
with col3:
    style.kpi_card(
        f"Gross Loss Ratio ({company['loss_ratio_year']})",
        f"{company['gross_loss_ratio']:.0%}",
        f"vs {data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]['gross_loss_ratio']:.0%} in {data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]['year']}",
        True,
    )
with col4:
    style.kpi_card(
        "Net Loss", f"${company['net_loss_m']:.1f}M",
        f"{net_loss_qoq_pct:+.0%} QoQ" if net_loss_qoq_pct is not None else company["net_loss_period"],
        (net_loss_qoq_pct < 0) if net_loss_qoq_pct is not None else None,
    )

style.insight(
    "Bottom line: growth is accelerating and underwriting is improving company-wide",
    f"In-force premium grew {company['ifp_yoy_growth_pct']:+.0%} YoY to {style.fmt_usd_m(company['in_force_premium_m'])}, "
    f"the gross loss ratio improved to {company['gross_loss_ratio']:.0%} in {company['loss_ratio_year']} "
    f"(from {data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]['gross_loss_ratio']:.0%} in {data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]['year']}), "
    f"and net loss in {company['net_loss_period']} was ${company['net_loss_m']:.1f}M -- the company-wide picture is healthy.",
)

st.divider()
style.headline("Pet segment snapshot", f"Lemonade Pet launched {data.PET_LAUNCH_DATE}")
pcol1, pcol2, pcol3, pcol4 = st.columns(4)
with pcol1:
    style.kpi_card(
        "Pet In-Force Premium", f"${pet['in_force_premium_m']:.0f}M",
        f"{pet['yoy_ifp_growth_pct']:+.0%} YoY · {pet['qoq_ifp_growth_pct']:+.0%} QoQ",
        True,
    )
with pcol2:
    style.kpi_card(
        "Pet Premium / Customer", f"${pet['premium_per_customer']:.0f}",
        f"{pet['yoy_ppc_growth_pct']:+.0%} YoY · {pet['qoq_ppc_growth_pct']:+.0%} QoQ",
        True,
    )
with pcol3:
    yoy_loss_ratio_points = pet.get("yoy_loss_ratio_points")
    qoq_loss_ratio_points = pet["qoq_loss_ratio_points"]
    style.kpi_card(
        "Pet Gross Loss Ratio", f"{pet['gross_loss_ratio']:.0%}",
        f"{yoy_loss_ratio_points:+.1f}pts YoY · {qoq_loss_ratio_points:+.1f}pts QoQ" if yoy_loss_ratio_points is not None else f"{qoq_loss_ratio_points:+.1f}pts QoQ",
        (yoy_loss_ratio_points < 0) if yoy_loss_ratio_points is not None else (qoq_loss_ratio_points < 0),
    )
with pcol4:
    share_prior_year = kpis.pet_share_of_company(pet["yoy_quarter"]) if pet.get("yoy_quarter") else None
    share_prior_q = kpis.pet_share_of_company(pet["prior_quarter"])
    share_change_points = (
        (share["pet_share_pct"] - share_prior_year["pet_share_pct"]) * 100 if share_prior_year else None
    )
    share_qoq_points = (share["pet_share_pct"] - share_prior_q["pet_share_pct"]) * 100
    yoy_part = f"{share_change_points:+.1f}pts YoY · " if share_change_points is not None else ""
    style.kpi_card(
        "Share of Company IFP", f"{share['pet_share_pct']:.0%}",
        f"{yoy_part}{share_qoq_points:+.1f}pts QoQ (2nd largest)",
        (share_change_points > 0) if share_change_points is not None else (share_qoq_points > 0),
    )

style.insight(
    "Bottom line: Pet is growing fast, but underwriting and monetization haven't kept pace",
    f"Pet in-force premium grew {pet['yoy_ifp_growth_pct']:+.0%} YoY to ${pet['in_force_premium_m']:.0f}M and is now "
    f"{share['pet_share_pct']:.0%} of company IFP (2nd-largest segment), but premium per customer grew only "
    f"{pet['yoy_ppc_growth_pct']:+.0%} YoY and the gross loss ratio sits at {pet['gross_loss_ratio']:.0%} -- "
    "growth is outpacing both monetization and underwriting improvement, unlike the company-wide trend above.",
)

# ---------------------------------------------------------------------------
# Real, code-rendered chart views. Every chart_id below renders real
# tool-backed data; they appear as the "Supporting real-data charts" under
# the Risks & Opportunities map. The AI cannot invent a chart or a number.
# ---------------------------------------------------------------------------

def _chart_company_ifp_trend() -> alt.Chart:
    company_df = kpis.company_quarterly_series()
    chart = (
        alt.Chart(company_df)
        .mark_line(point=True, color=style.PINK)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("in_force_premium_m:Q", title="In-Force Premium ($M)"),
            tooltip=["quarter", "in_force_premium_m", "customers"],
        )
        .properties(title="Company-wide In-Force Premium", height=280)
    )
    return style.themed_chart(chart)


def _chart_growth_acceleration() -> alt.Chart:
    growth_df = kpis.company_quarterly_series().dropna(subset=["ifp_yoy_growth_pct"]).copy()
    growth_df["value_label"] = growth_df["ifp_yoy_growth_pct"].map(lambda v: f"{v:.0%}")
    bars = (
        alt.Chart(growth_df)
        .mark_bar(color=style.NAVY)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("ifp_yoy_growth_pct:Q", title="YoY IFP Growth", axis=alt.Axis(format="%")),
            tooltip=["quarter", alt.Tooltip("ifp_yoy_growth_pct:Q", format=".0%")],
        )
        .properties(title="YoY Growth Rate", height=280)
    )
    return style.themed_chart(labeled_vertical_bar(bars, "value_label"))


def _chart_pet_ifp_trend() -> alt.Chart:
    pet_df = kpis.pet_quarterly_series().copy()
    pet_df["value_label"] = pet_df["in_force_premium_m"].map(lambda v: f"${v:.0f}M")
    bars = (
        alt.Chart(pet_df)
        .mark_bar(color=style.PINK)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("in_force_premium_m:Q", title="Pet In-Force Premium ($M)"),
            tooltip=["quarter", "in_force_premium_m"],
        )
        .properties(title="Pet Segment In-Force Premium (disclosed points only)", height=280)
    )
    return style.themed_chart(labeled_vertical_bar(bars, "value_label"))


def _chart_segment_breakdown() -> alt.Chart:
    breakdown_df = pd.DataFrame(share["breakdown"]).sort_values("in_force_premium_m", ascending=False).reset_index(drop=True)
    breakdown_df["highlight"] = breakdown_df["segment"].map(lambda s: "Pet" if s == "Pet" else "Other lines")
    breakdown_df["value_label"] = breakdown_df["in_force_premium_m"].map(lambda v: f"${v:.0f}M")
    bars = (
        alt.Chart(breakdown_df)
        .mark_bar()
        .encode(
            x=alt.X("in_force_premium_m:Q", title="In-Force Premium ($M)"),
            y=alt.Y("segment:N", sort=breakdown_df["segment"].tolist(), title=None),
            color=alt.Color(
                "highlight:N",
                scale=alt.Scale(domain=["Pet", "Other lines"], range=[style.PINK, "#D9D9D9"]),
                legend=None,
            ),
            tooltip=["segment", "in_force_premium_m"],
        )
        .properties(title=f"Segment Breakdown ({share['quarter']})", height=280)
    )
    return style.themed_chart(labeled_horizontal_bar(bars, "value_label"))


def _chart_company_vs_pet_loss_ratio() -> alt.Chart:
    # Now QUARTERLY for both: company-wide gross loss ratio is disclosed
    # quarterly in COMPANY_FINANCIALS (previously only annual was available, so
    # this chart had to mix annual company bars with Pet quarterly averages).
    company = kpis.company_financials_series()[["quarter", "gross_loss_ratio"]].assign(entity="Company")
    pet = kpis.segment_quarterly("Pet")[["quarter", "gross_loss_ratio"]].assign(entity="Pet")
    df = pd.concat([company, pet], ignore_index=True)
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("gross_loss_ratio:Q", title="Gross Loss Ratio", axis=alt.Axis(format="%")),
            color=alt.Color("entity:N", scale=alt.Scale(domain=["Company", "Pet"], range=[style.NAVY, style.PINK]), legend=alt.Legend(title=None)),
            tooltip=["quarter", "entity", alt.Tooltip("gross_loss_ratio:Q", format=".0%")],
        )
        .properties(title="Company vs. Pet Gross Loss Ratio (quarterly)", height=280)
    )
    return style.themed_chart(chart)


def _chart_adjusted_ebitda_path() -> alt.Chart:
    fin = kpis.company_financials_series().copy()
    fin["value_label"] = fin["adjusted_ebitda_m"].map(lambda v: f"${v:.0f}M")
    bars = (
        alt.Chart(fin)
        .mark_bar(color=style.NAVY)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("adjusted_ebitda_m:Q", title="Adjusted EBITDA ($M)"),
            tooltip=["quarter", alt.Tooltip("adjusted_ebitda_m:Q", format=",.1f")],
        )
        .properties(title="Adjusted EBITDA -- Path to Breakeven (guided Q4'26)", height=280)
    )
    return style.themed_chart(labeled_vertical_bar(bars, "value_label"))


def _chart_revenue_vs_ifp() -> alt.Chart:
    fin = kpis.company_financials_series()[["quarter", "revenue_m"]].rename(columns={"revenue_m": "value"}).assign(series="Revenue")
    ifp = kpis.company_quarterly_series()[["quarter", "in_force_premium_m"]].rename(columns={"in_force_premium_m": "value"}).assign(series="In-Force Premium")
    df = pd.concat([fin, ifp], ignore_index=True)
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("value:Q", title="$M"),
            color=alt.Color("series:N", scale=alt.Scale(domain=["In-Force Premium", "Revenue"], range=[style.PINK, style.NAVY]), legend=alt.Legend(title=None)),
            tooltip=["quarter", "series", alt.Tooltip("value:Q", format=",.0f")],
        )
        .properties(title="Revenue vs. In-Force Premium ($M) -- revenue now outgrowing IFP", height=280)
    )
    return style.themed_chart(chart)


def _chart_annual_dollar_retention() -> alt.Chart:
    fin = kpis.company_financials_series().copy()
    fin["value_label"] = fin["annual_dollar_retention"].map(lambda v: f"{v:.0%}")
    bars = (
        alt.Chart(fin)
        .mark_bar(color=style.PINK)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("annual_dollar_retention:Q", title="Annual Dollar Retention", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0.7, 0.95])),
            tooltip=["quarter", alt.Tooltip("annual_dollar_retention:Q", format=".0%")],
        )
        .properties(title="Annual Dollar Retention", height=280)
    )
    return style.themed_chart(labeled_vertical_bar(bars, "value_label"))


def _chart_pet_loss_ratio_trend() -> alt.Chart:
    chart = (
        alt.Chart(pet_loss_ratio_series)
        .mark_line(point=True, color=style.PINK)
        .encode(
            x=alt.X("quarter:N", sort=None, title=None),
            y=alt.Y("gross_loss_ratio:Q", title="Pet Gross Loss Ratio", axis=alt.Axis(format="%")),
            tooltip=["quarter", alt.Tooltip("gross_loss_ratio:Q", format=".0%")],
        )
        .properties(title="Pet Gross Loss Ratio -- Full Disclosed History (9 Quarters)", height=280)
    )
    return style.themed_chart(chart)


CHART_REGISTRY = {
    "company_ifp_trend": _chart_company_ifp_trend,
    "growth_acceleration": _chart_growth_acceleration,
    "pet_ifp_trend": _chart_pet_ifp_trend,
    "segment_breakdown": _chart_segment_breakdown,
    "company_vs_pet_loss_ratio": _chart_company_vs_pet_loss_ratio,
    "pet_loss_ratio_trend": _chart_pet_loss_ratio_trend,
    "adjusted_ebitda_path": _chart_adjusted_ebitda_path,
    "revenue_vs_ifp": _chart_revenue_vs_ifp,
    "annual_dollar_retention": _chart_annual_dollar_retention,
}

# ---------------------------------------------------------------------------
# Risks & Opportunities -- the USER chooses a framework; the AI advises on the
# trade-offs of each lens for the current data, then maps where the risks and
# opportunities are through that lens. The headline visual is the Risk &
# Opportunity Map (Impact x Confidence); real-data charts render as supporting
# evidence. The AI never invents a number.
# ---------------------------------------------------------------------------


_LEVEL_NUM = {"high": 3, "medium": 2, "low": 1}
# Real-data charts shown (collapsed) as supporting evidence under the R&O map.
_SUPPORTING_CHART_IDS = ["segment_breakdown", "company_vs_pet_loss_ratio", "adjusted_ebitda_path"]


def _render_risk_opportunity_map(items: list[dict]) -> None:
    """The single, framework-agnostic showcase chart: every risk/opportunity
    (numbered to match the lists below) plotted on an Impact x Confidence
    matrix, red = risk / green = opportunity. Each bubble shows its NUMBER (not
    its title) to avoid overlapping labels; the title is in the tooltip and in
    the numbered list beneath. Axes are the AI's assessment; each point's
    detail/evidence ties it to real data. Expects each item to carry '_n'.
    """
    rows = []
    for it in items or []:
        impact = _LEVEL_NUM.get(str(it.get("impact", "")).lower(), 2)
        conf = _LEVEL_NUM.get(str(it.get("confidence", "")).lower(), 2)
        # deterministic jitter so co-located points don't fully overlap
        jx = ((hash(it.get("title", "")) % 9) - 4) / 11.0
        jy = ((hash("y" + it.get("title", "")) % 9) - 4) / 11.0
        rows.append({
            "n": it.get("_n"),
            "title": it.get("title", ""),
            "type": "Opportunity" if it.get("type") == "opportunity" else "Risk",
            "framework_element": it.get("framework_element", ""),
            "impact_n": impact + jx,
            "confidence_n": conf + jy,
            "detail": it.get("detail", ""),
            "evidence_source": it.get("evidence_source", ""),
        })
    if not rows:
        return
    df = pd.DataFrame(rows)
    label_expr = "datum.value == 1 ? 'Low' : datum.value == 2 ? 'Medium' : datum.value == 3 ? 'High' : ''"
    base = alt.Chart(df).encode(
        x=alt.X("impact_n:Q", title="Impact →", scale=alt.Scale(domain=[0.5, 3.6]),
                axis=alt.Axis(values=[1, 2, 3], labelExpr=label_expr, grid=True, labelFontSize=13)),
        y=alt.Y("confidence_n:Q", title="Confidence →", scale=alt.Scale(domain=[0.5, 3.6]),
                axis=alt.Axis(values=[1, 2, 3], labelExpr=label_expr, grid=True, labelFontSize=13)),
    )
    points = base.mark_circle(size=620, opacity=0.9).encode(
        color=alt.Color("type:N", scale=alt.Scale(domain=["Risk", "Opportunity"], range=["#D64545", "#1B7A3D"]), legend=alt.Legend(title=None, labelFontSize=13)),
        tooltip=["n", "type", "title", "framework_element", "detail", "evidence_source"],
    )
    numbers = base.mark_text(fontSize=12, fontWeight="bold", color="white").encode(text="n:Q")
    st.altair_chart(
        style.themed_chart((points + numbers).properties(height=420, title="Risk & Opportunity Map — Impact × Confidence")),
        width="stretch",
    )
    st.caption(
        "Each bubble is numbered to match the lists below. **Impact** = the AI's judgment of how much is at stake. "
        "**Confidence** = evidence quality on a fixed rubric: high = a directly disclosed figure, "
        "medium = real data + a directional inference, low = public-sentiment/anecdotal signal. "
        "Red = risk, green = opportunity."
    )


FRAMEWORK_LABELS = {
    "bcg_growth_share": "BCG Growth-Share",
    "three_horizons": "Three Horizons of Growth",
    "swot": "SWOT",
    "issue_tree": "Issue Tree (Minto Pyramid)",
    "porters_five_forces": "Porter's Five Forces",
    "pestel": "PESTEL (macro environment)",
}

st.divider()
deep_dive_skill = skills.load_skill("business_deep_dive")
style.headline("Risks & Opportunities", "Pick a strategic lens; the AI maps the risks and opportunities through it.")

_ids = list(FRAMEWORK_LABELS.keys())
if "chosen_framework_select" not in st.session_state:
    st.session_state.chosen_framework_select = "bcg_growth_share"

# Step 1 -- optional framework advisor.
st.caption("The AI weighs each lens against Lemonade's real numbers and cited frameworks — you make the call.")
style.model_badge(client.FAST_MODEL)
_ADVISOR_JOB = "framework_advisor"
if st.button("🧭 Step 1 (optional): compare frameworks for this situation"):
    try:
        jobs.submit(
            _ADVISOR_JOB, client.run_tool_loop,
            system_prompt=prompts.BUSINESS_FRAMEWORK_ADVISOR_SYSTEM_PROMPT,
            user_message="Compare the frameworks for Lemonade's current business data as instructed.",
            tool_schemas=tools.TOOL_SCHEMAS,
            tool_executor=tools.build_tool_executor(),
            model=client.FAST_MODEL,
        )
        st.rerun()
    except client.MissingApiKeyError as e:
        st.error(str(e))

_adv_done = jobs_ui.poll_result(_ADVISOR_JOB)
if _adv_done is not None:
    text, _ = _adv_done
    try:
        advice = client.parse_json_response(text)
        st.session_state.framework_advice = advice
        # The recommendation sets (pre-selects) the dropdown below; the user can still override.
        if advice.get("suggested_default") in _ids:
            st.session_state.chosen_framework_select = advice["suggested_default"]
    except ValueError as e:
        st.error(f"Could not parse the model's response: {e}")

advice = st.session_state.get("framework_advice")
if advice:
    rec_id = advice.get("suggested_default")
    if rec_id in FRAMEWORK_LABELS:
        style.insight(
            f"✅ AI-recommended lens: {FRAMEWORK_LABELS[rec_id]}",
            advice.get("recommendation_reason", "") + "  — pre-selected below; override if you disagree.",
        )
    with st.expander("See the full pros/cons the AI weighed for every framework"):
        for opt in advice.get("framework_options", []):
            fid = opt.get("framework_id", "")
            tag = " &nbsp;✅ <strong>recommended</strong>" if fid == rec_id else ""
            style.note(
                f"<strong>{FRAMEWORK_LABELS.get(fid, fid)}</strong>{tag} — best for: {opt.get('best_for','')}<br/>"
                f"👍 {opt.get('pro_for_this_situation','')}<br/>👎 {opt.get('con_for_this_situation','')}<br/>"
                f"<em>{opt.get('rag_source','')}</em>"
            )

# Step 2 -- user chooses (defaults to the AI's recommendation when present).
chosen_framework = st.selectbox(
    "Step 2: choose the framework to apply",
    _ids,
    format_func=lambda fid: FRAMEWORK_LABELS[fid],
    key="chosen_framework_select",
)

st.caption(f"🧠 System prompt used: **{deep_dive_skill.name}** • 📚 RAG corpus: **consulting_best_practices**")
style.model_badge(client.MODEL)
with st.expander("View system prompt (tells the AI when/how to retrieve from the RAG corpus)"):
    st.markdown(deep_dive_skill.body)

# Step 3 -- apply.
_RNO_JOB = "risks_opportunities"
if st.button(f"Step 3: Map Risks & Opportunities with {FRAMEWORK_LABELS[chosen_framework]}", type="primary"):
    try:
        system_prompt = prompts.SHARED_GUARDRAILS + "\n\n" + deep_dive_skill.body
        st.session_state._rno_framework = chosen_framework  # capture at submit, not at done
        jobs.submit(
            _RNO_JOB, client.run_tool_loop,
            system_prompt=system_prompt,
            user_message=f"The user has chosen framework_id = {chosen_framework}. Apply it as instructed.",
            tool_schemas=tools.TOOL_SCHEMAS,
            tool_executor=tools.build_tool_executor(),
        )
        st.rerun()
    except client.MissingApiKeyError as e:
        st.error(str(e))

_rno_done = jobs_ui.poll_result(_RNO_JOB)
if _rno_done is not None:
    text, transcript = _rno_done
    try:
        result = client.parse_json_response(text)
        result["framework_id"] = st.session_state.get("_rno_framework", chosen_framework)
        st.session_state.business_deep_dive = result
        st.session_state.business_deep_dive_transcript = transcript
        st.session_state.pop("audit_business_deep_dive", None)
    except ValueError as e:
        st.error(f"Could not parse the model's response: {e}")

deep_dive = st.session_state.get("business_deep_dive")
deep_dive_transcript = st.session_state.get("business_deep_dive_transcript", [])
dd_is_default = deep_dive is None
if dd_is_default:
    deep_dive, deep_dive_transcript = default_runs.load_default("business_deep_dive")

if deep_dive is not None:
    if dd_is_default:
        st.info("📌 Showing a precomputed example (a real prior run, Three Horizons lens). Choose a framework and run Step 3 above for a fresh live analysis.")
    fid = deep_dive.get("framework_id", "bcg_growth_share")
    style.insight(deep_dive.get("bottom_line", ""), deep_dive.get("narrative", ""))

    items = deep_dive.get("items", [])
    for i, it in enumerate(items, 1):  # number items so chart bubbles match the lists
        it["_n"] = i
    _render_risk_opportunity_map(items)

    # The items themselves, numbered to match the map, grouped by type.
    rcol, ocol = st.columns(2)
    with rcol:
        st.markdown("**⚠ Risks**")
        for it in [x for x in items if x.get("type") == "risk"]:
            style.risk_opportunity_card(
                it.get("_n"), "risk", it.get("title", ""), it.get("framework_element", ""),
                it.get("impact", "?"), it.get("confidence", "?"),
                it.get("detail", ""), it.get("evidence_source", ""),
            )
    with ocol:
        st.markdown("**↑ Opportunities**")
        for it in [x for x in items if x.get("type") == "opportunity"]:
            style.risk_opportunity_card(
                it.get("_n"), "opportunity", it.get("title", ""), it.get("framework_element", ""),
                it.get("impact", "?"), it.get("confidence", "?"),
                it.get("detail", ""), it.get("evidence_source", ""),
            )

    with st.expander("📈 Supporting real-data charts"):
        for cid in _SUPPORTING_CHART_IDS:
            chart_fn = CHART_REGISTRY.get(cid)
            if chart_fn is not None:
                st.altair_chart(chart_fn(), width="stretch")

    validation.render_validation(deep_dive, deep_dive_transcript, "business_deep_dive")
    style.rag_sources_used(deep_dive_transcript)

    with st.expander(f"Tool calls used ({len(deep_dive_transcript)})"):
        for entry in deep_dive_transcript:
            st.markdown(f"**{entry['tool']}**({entry['input']})")
            st.json(entry["result"])

    st.caption(f"🧭 Lens: {FRAMEWORK_LABELS.get(fid, fid)} • grounding: {deep_dive.get('rag_source', '')}")
    st.success("Continue to **User Pain Points**, then **Course of Action**.")
