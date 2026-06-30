"""Lemonade-inspired visual styling for the Streamlit app.

Not affiliated with or endorsed by Lemonade -- colors/typography are inspired
by their public brand (hot pink, white, rounded cards, bold friendly
headlines) for a portfolio project, not a pixel-accurate clone of their app.
"""

from __future__ import annotations

import altair as alt
import streamlit as st

PINK = "#FF0083"
PINK_TINT = "#FFE6F2"
PINK_DARK = "#A8005E"
CARD_BG = "#F7F5F2"
TEXT = "#2B2B2B"
MUTED = "#6B6B6B"
NAVY = "#2B2B45"

CHART_COLOR_SEQUENCE = [PINK, NAVY, "#946200", "#0A8754", MUTED]

_LOGO_SVG = f"""
<svg width="{{size}}" height="{{size}}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <rect width="100" height="100" rx="18" fill="{PINK}"/>
    <path d="M 56 16
             C 47 9, 38 15, 41 23
             C 43 29, 51 29, 52 23
             L 51 64
             C 51 72, 41 76, 34 69
             C 45 79, 59 80, 71 87
             C 76 89.5, 79 85, 75 82"
          fill="none" stroke="white" stroke-width="7"
          stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def logo(size: int = 64) -> str:
    """An original cursive-L monogram in Lemonade's pink/white palette --
    inspired by their visual identity, not a reproduction of their actual
    trademarked logo asset.
    """
    return _LOGO_SVG.format(size=size)


def themed_chart(chart: alt.Chart) -> alt.Chart:
    """Apply consistent Lemonade-pink styling to any Altair chart."""
    return chart.configure_axis(
        labelColor=MUTED, titleColor=MUTED, gridColor="#EFEFEF", domainColor="#DDDDDD"
    ).configure_view(strokeWidth=0).configure_title(color=TEXT, fontSize=14, fontWeight="bold")

_CSS = f"""
<style>
.pbz-disclaimer {{
    background: {PINK_TINT};
    border-left: 4px solid {PINK};
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
    color: {TEXT};
    margin-bottom: 1.2rem;
}}

.pbz-card {{
    background: {CARD_BG};
    border-radius: 18px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.9rem;
}}

.pbz-card h4 {{
    margin: 0 0 0.3rem 0;
    font-size: 0.95rem;
    color: {MUTED};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}

.pbz-card .pbz-value {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {TEXT};
}}

.pbz-card .pbz-delta-up {{
    color: #0A8754;
    font-weight: 600;
    font-size: 0.95rem;
}}

.pbz-card .pbz-delta-down {{
    color: #C81E5C;
    font-weight: 600;
    font-size: 0.95rem;
}}

.pbz-card .pbz-delta-neutral {{
    color: {MUTED};
    font-weight: 500;
    font-size: 0.95rem;
}}

.pbz-badge {{
    background: {PINK};
    color: white;
    border-radius: 999px;
    width: 110px;
    height: 110px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    margin: 0 auto 0.6rem auto;
    text-align: center;
    line-height: 1.1;
}}

.pbz-badge .pbz-badge-value {{
    font-size: 1.4rem;
}}

.pbz-badge .pbz-badge-label {{
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    opacity: 0.9;
}}

.pbz-fact-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 1.6rem;
    margin-bottom: 1.1rem;
}}

.pbz-fact {{
    min-width: 200px;
}}

.pbz-fact .pbz-fact-label {{
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: {MUTED};
    font-weight: 600;
    margin-bottom: 0.1rem;
}}

.pbz-fact .pbz-fact-value {{
    font-size: 0.95rem;
    color: {TEXT};
}}

table.pbz-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
    font-size: 0.92rem;
}}

table.pbz-table th {{
    text-align: left;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: {MUTED};
    font-weight: 600;
    padding: 0.5rem 0.9rem;
    border-bottom: 2px solid #EAEAEA;
}}

table.pbz-table td {{
    padding: 0.6rem 0.9rem;
    border-bottom: 1px solid #EFEFEF;
    color: {TEXT};
}}

table.pbz-table tr:last-child td {{
    border-bottom: none;
}}

.pbz-change-up {{
    color: #0A8754;
    font-weight: 700;
}}

.pbz-change-down {{
    color: #C81E5C;
    font-weight: 700;
}}

.pbz-tag {{
    display: inline-block;
    font-size: 0.72rem;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    background: #F2F2F2;
    color: {MUTED};
    font-weight: 600;
}}

.pbz-tag-pink {{
    background: {PINK_TINT};
    color: #A8005E;
}}

.pbz-confidence-high {{
    background: #E6F4EC;
    color: #0A8754;
}}

.pbz-confidence-medium {{
    background: #FFF6E5;
    color: #946200;
}}

.pbz-confidence-low {{
    background: #F2F2F2;
    color: {MUTED};
}}

.pbz-hyp-card {{
    background: {CARD_BG};
    border-radius: 16px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}}

.pbz-hyp-card .pbz-hyp-rank {{
    display: inline-block;
    background: {PINK};
    color: white;
    border-radius: 999px;
    width: 26px;
    height: 26px;
    text-align: center;
    line-height: 26px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-right: 0.5rem;
}}

.pbz-hyp-card .pbz-hyp-statement {{
    font-size: 1rem;
    font-weight: 600;
    color: {TEXT};
    margin: 0.3rem 0 0.5rem 0;
}}

.pbz-hyp-card .pbz-hyp-rationale {{
    font-size: 0.88rem;
    color: {MUTED};
    margin-bottom: 0.5rem;
}}

.pbz-hyp-card .pbz-hyp-tags {{
    margin-bottom: 0.4rem;
}}

.pbz-hyp-card .pbz-hyp-tags .pbz-tag {{
    margin-right: 0.4rem;
}}

.pbz-missing-data {{
    font-size: 0.8rem;
    color: #A8005E;
}}

.pbz-note {{
    font-size: 0.85rem;
    color: {MUTED};
    margin: 0.2rem 0 1rem 0;
}}

.pbz-note-lg {{
    font-size: 1rem;
    color: {TEXT};
    margin: 0.3rem 0 1.1rem 0;
}}

.pbz-ro {{
    border-radius: 10px;
    padding: 0.55rem 0.8rem 0.65rem 0.8rem;
    margin: 0 0 0.55rem 0;
    border-left: 4px solid;
}}
.pbz-ro.risk {{ border-left-color: #D64550; background: #FDEDEF; }}
.pbz-ro.opp  {{ border-left-color: #0A8754; background: #E9F6F0; }}
.pbz-ro-head {{ display: flex; align-items: center; gap: 0.45rem; }}
.pbz-ro-num {{
    flex: none; display: inline-flex; align-items: center; justify-content: center;
    width: 1.3rem; height: 1.3rem; border-radius: 50%;
    font-size: 0.72rem; font-weight: 700; color: #fff;
}}
.pbz-ro.risk .pbz-ro-num {{ background: #D64550; }}
.pbz-ro.opp  .pbz-ro-num {{ background: #0A8754; }}
.pbz-ro-title {{ font-size: 0.92rem; font-weight: 700; color: {TEXT}; line-height: 1.25; }}
.pbz-ro-meta {{ margin: 0.3rem 0 0 0; display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; }}
.pbz-ro-pill {{
    font-size: 0.64rem; font-weight: 700; letter-spacing: 0.02em;
    padding: 0.05rem 0.42rem; border-radius: 999px;
    background: rgba(0,0,0,0.05); color: #666; text-transform: uppercase;
}}
.pbz-ro-pill.hi {{ background: rgba(214,69,80,0.16); color: #B23240; }}
.pbz-ro.opp .pbz-ro-pill.hi {{ background: rgba(10,135,84,0.16); color: #0A8754; }}
.pbz-ro-tag {{ font-size: 0.66rem; color: #999; font-style: italic; }}
.pbz-ro-detail {{ font-size: 0.81rem; color: #4A4A4A; margin-top: 0.35rem; line-height: 1.4; }}
.pbz-ro-src {{ font-size: 0.63rem; color: #B0B0B0; margin-top: 0.3rem; }}

.pbz-section-emphasis {{
    border-left: 4px solid {PINK};
    padding-left: 0.7rem;
    font-size: 1.1rem;
    font-weight: 700;
    color: {TEXT};
    margin: 0.4rem 0 0.7rem 0;
}}

.pbz-theme-card {{
    padding: 0.2rem 0;
    margin-bottom: 0.9rem;
}}

.pbz-theme-card .pbz-theme-title {{
    font-size: 1.05rem;
    font-weight: 700;
    color: {PINK_DARK};
    margin-bottom: 0.15rem;
}}

.pbz-theme-card .pbz-theme-detail {{
    font-size: 0.92rem;
    color: {TEXT};
}}

.pbz-insight {{
    background: {PINK_TINT};
    border-radius: 14px;
    padding: 0.7rem 1.1rem;
    margin-bottom: 0.7rem;
    font-size: 0.92rem;
    color: {TEXT};
}}

.pbz-insight .pbz-insight-label {{
    display: block;
    color: {PINK_DARK};
    font-weight: 700;
    font-size: 1.15rem;
    margin-bottom: 0.3rem;
}}

.pbz-insight .pbz-insight-detail {{
    display: block;
}}

.pbz-rec-hero {{
    background: linear-gradient(135deg, {PINK} 0%, {PINK_DARK} 100%);
    border-radius: 16px;
    padding: 1.1rem 1.3rem;
    margin: 0.2rem 0 1.0rem 0;
    color: white;
}}

.pbz-rec-hero .pbz-rec-hero-label {{
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 700;
    opacity: 0.85;
    margin-bottom: 0.35rem;
}}

.pbz-rec-hero .pbz-rec-hero-text {{
    display: block;
    font-size: 1.2rem;
    font-weight: 600;
    line-height: 1.45;
}}

.pbz-situation {{
    background: #F4F5F8;
    border-left: 5px solid {NAVY};
    border-radius: 10px;
    padding: 0.95rem 1.2rem;
    margin: 0.2rem 0 1.0rem 0;
    color: {TEXT};
}}

.pbz-rec-action {{
    background: #E7F6EC;
    border-left: 5px solid #1B7A3D;
    border-radius: 10px;
    padding: 0.8rem 1.1rem;
    margin: 0.5rem 0 0.8rem 0;
    color: {TEXT};
}}

.pbz-rec-action .pbz-rec-action-label {{
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-size: 0.7rem;
    font-weight: 700;
    color: #1B7A3D;
    margin-bottom: 0.25rem;
}}

.pbz-situation .pbz-situation-label {{
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 700;
    color: {NAVY};
    margin-bottom: 0.35rem;
}}

.pbz-situation .pbz-situation-text {{
    display: block;
    font-size: 1.1rem;
    font-weight: 500;
    line-height: 1.5;
}}

.pbz-grounding {{
    border-radius: 12px;
    padding: 0.55rem 0.9rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    font-weight: 600;
}}

.pbz-grounding-pass {{
    background: #E7F6EC;
    color: #1B7A3D;
    border: 1px solid #9BD8B0;
}}

.pbz-grounding-warn {{
    background: #FFF3E0;
    color: #8A5A00;
    border: 1px solid #F0C27B;
}}

.pbz-framework-badge {{
    background: {PINK_TINT};
    border-left: 4px solid {PINK};
    border-radius: 8px;
    padding: 0.5rem 0.9rem;
    margin: 0.4rem 0 0.7rem 0;
    font-size: 0.9rem;
    color: {TEXT};
}}

.pbz-headline {{
    font-size: 2.1rem;
    font-weight: 700;
    color: {PINK};
    margin-bottom: 0.1rem;
}}

.pbz-subhead {{
    font-size: 1.05rem;
    color: {MUTED};
    margin-bottom: 1.4rem;
}}

div[data-testid="stSidebarNav"] {{
    padding-top: 0.5rem;
}}
</style>
"""


def inject_global_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def disclaimer_banner(text: str) -> None:
    st.markdown(f'<div class="pbz-disclaimer">{text}</div>', unsafe_allow_html=True)


def fmt_usd_m(value_m: float) -> str:
    """Format a $M figure, switching to $B above 1,000M (e.g. 1333 -> '$1.3B')."""
    if abs(value_m) >= 1000:
        return f"${value_m / 1000:,.1f}B"
    return f"${value_m:,.0f}M"


def escape_dollar(text: str) -> str:
    """Replace '$' with the HTML entity so Streamlit's markdown doesn't
    interpret paired '$...$' as LaTeX math (which garbles dollar figures, e.g.
    "$1.3B ... $490M"). Uses '&#36;' rather than a '\\$' backslash-escape
    because these strings are injected inside raw HTML (unsafe_allow_html),
    where a markdown backslash-escape would render as a literal backslash.
    The entity renders as '$' in both plain-markdown and HTML contexts.
    """
    if not isinstance(text, str):
        return text
    return text.replace("$", "&#36;")


def headline(title: str, subhead: str | None = None) -> None:
    st.markdown(f'<div class="pbz-headline">{title}</div>', unsafe_allow_html=True)
    if subhead:
        st.markdown(f'<div class="pbz-subhead">{subhead}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str | None = None, delta_positive: bool | None = None) -> None:
    delta_html = ""
    if delta is not None:
        if delta_positive is None:
            delta_html = f'<div class="pbz-delta-neutral">{delta}</div>'
        else:
            css_class = "pbz-delta-up" if delta_positive else "pbz-delta-down"
            arrow = "▲" if delta_positive else "▼"
            delta_html = f'<div class="{css_class}">{arrow} {delta}</div>'
    st.markdown(
        f"""
        <div class="pbz-card">
            <h4>{label}</h4>
            <div class="pbz-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_badge(value: str, label: str) -> None:
    st.markdown(
        f"""
        <div class="pbz-badge">
            <div class="pbz-badge-value">{value}</div>
            <div class="pbz-badge-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fact_row(facts: list[tuple[str, str]]) -> None:
    """A row of plain label/value facts -- e.g. dataset coverage dates --
    rendered as quiet text, not colored cards, for an executive-summary feel.
    """
    items = "".join(
        f'<div class="pbz-fact"><div class="pbz-fact-label">{label}</div>'
        f'<div class="pbz-fact-value">{value}</div></div>'
        for label, value in facts
    )
    st.markdown(f'<div class="pbz-fact-row">{items}</div>', unsafe_allow_html=True)


def _change_span(pct_change: float) -> str:
    css_class = "pbz-change-up" if pct_change >= 0 else "pbz-change-down"
    arrow = "▲" if pct_change >= 0 else "▼"
    return f'<span class="{css_class}">{arrow} {pct_change:+.0%}</span>'


def anomaly_table(rows: list[dict]) -> None:
    """A plain table of segment-level KPI moves: one row per segment, a
    color-coded change column, and an optional tag -- replaces a stack of
    colored alert boxes with something closer to an exec-readable table.

    Each row: {"segment": str, "before": float, "after": float,
               "pct_change": float, "tag": str | None}
    """
    body_rows = ""
    for r in rows:
        tag_html = ""
        if r.get("tag"):
            tag_class = "pbz-tag pbz-tag-pink" if r.get("tag_pink") else "pbz-tag"
            tag_html = f'<span class="{tag_class}">{r["tag"]}</span>'
        body_rows += (
            f"<tr><td>{r['segment']}</td>"
            f"<td>${r['before']:.0f}</td>"
            f"<td>${r['after']:.0f}</td>"
            f"<td>{_change_span(r['pct_change'])}</td>"
            f"<td>{tag_html}</td></tr>"
        )
    st.markdown(
        f"""
        <table class="pbz-table">
            <thead>
                <tr><th>Segment</th><th>Before</th><th>After</th><th>Change</th><th>Note</th></tr>
            </thead>
            <tbody>{body_rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def insight(label: str, detail: str) -> None:
    """A pink, rounded callout for a chart's main takeaway -- visually
    distinct from regular body text/notes so the key insight reads first.
    """
    st.markdown(
        f'<div class="pbz-insight"><span class="pbz-insight-label">{escape_dollar(label)}</span><span class="pbz-insight-detail">{escape_dollar(detail)}</span></div>',
        unsafe_allow_html=True,
    )


def model_badge(model_id: str) -> None:
    """Shows which model this step uses + why -- so the model choice and its
    pros/cons are visible, not hidden. Reads client.MODEL_INFO.
    """
    from pets_bizops.ai import client

    info = client.MODEL_INFO.get(model_id, {"label": model_id, "role": ""})
    st.caption(f"⚙️ Model: **{info['label']}** — {info['role']}")


def situation_banner(text: str) -> None:
    """The top-of-page framing: the factual situation + the central question
    the analysis exists to answer. Deterministic (computed from real KPIs),
    shown on cold load. It frames the question -- it does NOT assert a
    conclusion, so it doesn't pre-empt the analysis that follows.
    """
    st.markdown(
        f'<div class="pbz-situation"><span class="pbz-situation-label">The central question</span>'
        f'<span class="pbz-situation-text">{escape_dollar(text)}</span></div>',
        unsafe_allow_html=True,
    )


def recommended_action(text: str) -> None:
    """A green-accented callout for the single recommended action -- visually
    distinct from the candidate list so the 'do this' reads instantly."""
    st.markdown(
        f'<div class="pbz-rec-action"><span class="pbz-rec-action-label">⭐ Recommended action</span>'
        f'{escape_dollar(text)}</div>',
        unsafe_allow_html=True,
    )


def recommendation_hero(text: str) -> None:
    """The synthesized executive recommendation -- shown only AFTER the
    analysis chain has run (at the top of the Course of Action results), so
    the answer appears after the work, not before it.
    """
    st.markdown(
        f'<div class="pbz-rec-hero"><span class="pbz-rec-hero-label">Executive recommendation</span>'
        f'<span class="pbz-rec-hero-text">{escape_dollar(text)}</span></div>',
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    st.markdown(f'<div class="pbz-note">{escape_dollar(text)}</div>', unsafe_allow_html=True)


def risk_opportunity_card(
    n: int, kind: str, title: str, framework_element: str,
    impact: str, confidence: str, detail: str, source: str,
) -> None:
    """A scannable color-coded card for one risk/opportunity item: number badge
    matching the bubble map, title, impact/confidence pills (high = accent), the
    framework element tag, a tight detail line, and a muted source.
    """
    cls = "risk" if kind == "risk" else "opp"
    imp_hi = "hi" if str(impact).lower() == "high" else ""
    conf_hi = "hi" if str(confidence).lower() == "high" else ""
    st.markdown(
        f'<div class="pbz-ro {cls}">'
        f'<div class="pbz-ro-head">'
        f'<span class="pbz-ro-num">{n}</span>'
        f'<span class="pbz-ro-title">{escape_dollar(title)}</span>'
        f'</div>'
        f'<div class="pbz-ro-meta">'
        f'<span class="pbz-ro-pill {imp_hi}">impact {escape_dollar(impact)}</span>'
        f'<span class="pbz-ro-pill {conf_hi}">conf {escape_dollar(confidence)}</span>'
        f'<span class="pbz-ro-tag">{escape_dollar(framework_element)}</span>'
        f'</div>'
        f'<div class="pbz-ro-detail">{escape_dollar(detail)}</div>'
        f'<div class="pbz-ro-src">{escape_dollar(source)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def note_lg(text: str) -> None:
    """A larger, higher-contrast variant of note() for content that should
    read more prominently than a quiet footnote (e.g. sentiment themes).
    """
    st.markdown(f'<div class="pbz-note-lg">{escape_dollar(text)}</div>', unsafe_allow_html=True)


def theme_card(emoji: str, title: str, detail: str) -> None:
    """A pink-bordered callout for one sentiment theme -- emoji + bold title
    up top, plain detail line below, more visually distinct than a plain
    bolded inline note.
    """
    st.markdown(
        f"""
        <div class="pbz-theme-card">
            <div class="pbz-theme-title">{emoji} {title}</div>
            <div class="pbz-theme-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def framework_choice_badge(choice: dict) -> None:
    """Renders the AI's named framework/methodology choice + justification --
    the visible "which lens, and why" signal, consistent across all 3 AI
    pages. Accepts either {framework_id|document_used, justification} shapes.
    """
    if not choice:
        return
    label = choice.get("framework_id") or choice.get("document_used") or "—"
    justification = choice.get("justification", "")
    st.markdown(
        f'<div class="pbz-framework-badge">🧭 <strong>Lens / grounding:</strong> '
        f'{escape_dollar(str(label))}<br/><span style="opacity:0.85;">{escape_dollar(justification)}</span></div>',
        unsafe_allow_html=True,
    )


def grounding_badge(report, label: str = "code-verified") -> None:
    """Renders a Tier-1 grounding-check result: a pass/warn badge plus an
    expander listing every claim and what it matched against. `report` is a
    grounding_check.GroundingReport.
    """
    unverified = report.unverified
    if not unverified:
        st.markdown(
            f'<div class="pbz-grounding pbz-grounding-pass">✅ {report.verified_count}/{report.total} '
            f'citations verified against the real transcript ({label})</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="pbz-grounding pbz-grounding-warn">⚠ {len(unverified)} of {report.total} '
            f'citations could not be matched to the transcript ({label})</div>',
            unsafe_allow_html=True,
        )
    with st.expander(f"Grounding detail ({report.total} claims)"):
        for v in report.verdicts:
            icon = {"verified_tool": "✅", "verified_rag": "📚", "allowed_generic": "◽", "unverified": "⚠"}.get(v.verdict, "•")
            st.markdown(f"{icon} **{v.verdict}** — `{escape_dollar(v.value)}` _(from {v.field})_")


def rag_sources_used(transcript: list[dict]) -> None:
    """Surfaces the actual retrieved RAG chunks from a tool-call transcript --
    distinct from the static skill instructions (the "how to think" prompt)
    and from the generic "Tool calls used" expander (which also includes
    plain KPI lookups). This is the literal retrieved knowledge-base
    evidence the AI cited, with real sources and similarity scores.
    """
    retrieved = [entry for entry in transcript if entry.get("tool") == "retrieve_knowledge"]
    if not retrieved:
        return
    n_chunks = sum(len(e.get("result", {}).get("results", [])) for e in retrieved)
    with st.expander(f"📚 RAG sources retrieved ({n_chunks} chunks across {len(retrieved)} queries)"):
        for entry in retrieved:
            query = entry.get("input", {}).get("query", "")
            corpus = entry.get("input", {}).get("corpus", "")
            st.caption(f"Query: “{query}” (corpus: {corpus})")
            for chunk in entry.get("result", {}).get("results", []):
                st.markdown(f"**{chunk.get('source', '')}** (score: {chunk.get('score', 0):.3f})")
                note(chunk.get("text", ""))


def section_emphasis(text: str) -> None:
    """A subheadline with a pink left border to draw the eye to a section
    that matters more than a plain bold markdown line would convey.
    """
    st.markdown(f'<div class="pbz-section-emphasis">{text}</div>', unsafe_allow_html=True)


def sources_footer(sources: list[str]) -> None:
    items = "".join(f"<li>{s}</li>" for s in sources)
    st.markdown(
        f'<div class="pbz-note"><strong>Sources:</strong><ul style="margin-top:0.3rem;">{items}</ul></div>',
        unsafe_allow_html=True,
    )


def _confidence_tag(confidence: str) -> str:
    css_class = f"pbz-tag pbz-confidence-{confidence}"
    return f'<span class="{css_class}">{confidence} confidence</span>'


def findings_table(findings: list[dict]) -> None:
    """Each finding: {"finding": str, "segment": str, "confidence": str,
    "evidence_source": str}.
    """
    body_rows = ""
    for f in findings:
        body_rows += (
            f"<tr><td>{f['finding']}</td>"
            f"<td>{f.get('segment', '')}</td>"
            f"<td>{_confidence_tag(f.get('confidence', 'low'))}</td>"
            f"<td><span class=\"pbz-tag\">{f.get('evidence_source', '')}</span></td></tr>"
        )
    st.markdown(
        f"""
        <table class="pbz-table">
            <thead><tr><th>Finding</th><th>Segment</th><th>Confidence</th><th>Source</th></tr></thead>
            <tbody>{body_rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def hypothesis_card(rank: int, hypothesis: dict) -> None:
    """hypothesis: {"statement", "evidence_strength", "impact_estimate",
    "confidence", "rationale", "missing_data": [...], "composite_score"}.
    """
    tags = "".join(
        f'<span class="pbz-tag">{label}: {hypothesis.get(field, "?")}</span>'
        for field, label in [
            ("evidence_strength", "Evidence"),
            ("impact_estimate", "Impact"),
            ("confidence", "Confidence"),
        ]
    )
    missing_html = ""
    if hypothesis.get("missing_data"):
        items = "; ".join(hypothesis["missing_data"])
        missing_html = f'<div class="pbz-missing-data">Missing data to validate: {items}</div>'

    st.markdown(
        f"""
        <div class="pbz-hyp-card">
            <span class="pbz-hyp-rank">{rank}</span>
            <span style="color:{MUTED}; font-size:0.8rem;">composite score: {hypothesis.get('composite_score', '?')}</span>
            <div class="pbz-hyp-statement">{hypothesis['statement']}</div>
            <div class="pbz-hyp-tags">{tags}</div>
            <div class="pbz-hyp-rationale">{hypothesis.get('rationale', '')}</div>
            {missing_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
