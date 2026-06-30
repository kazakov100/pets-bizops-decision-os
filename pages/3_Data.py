"""View the real, publicly disclosed Lemonade data tables behind the KPIs.

Deterministic, no AI -- lets you sanity-check the underlying disclosed
numbers rather than only the computed KPIs on the Overview page.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from pets_bizops.data import real_lemonade_data as data
from pets_bizops.analysis import kpis
from pets_bizops.ui import style

st.set_page_config(page_title="Data -- Pets BizOps Decision OS", page_icon="🐾", layout="wide")
style.inject_global_styles()

style.headline("Data", "The real, publicly disclosed numbers behind every chart and AI call in this app.")
style.disclaimer_banner("📊 REAL DATA, PUBLIC DISCLOSURE ONLY -- no synthetic or fabricated numbers anywhere below.")

tab0, tab1, tabf, tab2, tab3, tab4, tab5 = st.tabs(
    ["Mission & strategy", "Company quarterly", "Company financials", "Pet segment quarterly", "Segment breakdown (Q1'26)", "Loss ratio & net loss", "Raw source data"]
)

with tab0:
    st.caption("Lemonade's own publicly stated business model and growth strategy -- context for the levers and risks discussed on the AI pages.")
    style.note(data.MISSION_AND_STRATEGY)
    style.sources_footer(data.SOURCES)

with tab1:
    st.caption("Company-wide in-force premium, customers, and premium per customer, by quarter.")
    st.dataframe(data.COMPANY_QUARTERLY, width="stretch", hide_index=True)

with tabf:
    st.caption(
        "Company-wide financials & operating metrics, all 9 quarters -- from the Q1'26 "
        "shareholder letter's 'Historical Operating Metrics' table. Revenue, gross earned "
        "premium, gross/adjusted gross profit + margin, Adjusted EBITDA (path to the guided "
        "first EBITDA-positive quarter in Q4'26), Annual Dollar Retention, and the "
        "company-wide quarterly gross/net loss ratios."
    )
    fin = data.COMPANY_FINANCIALS.copy()
    for col in ["gross_profit_margin", "annual_dollar_retention", "gross_loss_ratio", "net_loss_ratio"]:
        fin[col] = fin[col].map(lambda v: f"{v:.0%}")
    st.dataframe(fin, width="stretch", hide_index=True)
    st.json(kpis.company_financials_latest())

with tab2:
    st.caption(
        "Pet segment in-force premium, premium per customer, and gross loss ratio, by quarter "
        "(Q1'24 through Q1'26, reconstructed from overlapping shareholder-letter trailing tables)."
    )
    st.dataframe(kpis.pet_quarterly_series(), width="stretch", hide_index=True)
    st.json(data.PET_OTHER_FACTS)

with tab3:
    st.caption("All segments' in-force premium, loss ratio, and premium per customer, every quarter.")
    st.dataframe(kpis.all_segments_quarterly_series(), width="stretch", hide_index=True)
    st.json(kpis.pet_share_of_company("Q1'26"))
    st.json(data.CAR_SEGMENT_FACTS)

with tab4:
    st.caption("Company-wide gross/net loss ratio -- now available QUARTERLY (from the Q1'26 letter's historical table), plus the annual figures and the full disclosed net-loss series.")
    clr = data.COMPANY_FINANCIALS[["quarter", "gross_loss_ratio", "net_loss_ratio"]].copy()
    for col in ["gross_loss_ratio", "net_loss_ratio"]:
        clr[col] = clr[col].map(lambda v: f"{v:.0%}")
    st.dataframe(clr, width="stretch", hide_index=True)
    st.dataframe(data.COMPANY_ANNUAL_LOSS_RATIO, width="stretch", hide_index=True)
    st.dataframe(data.COMPANY_QUARTERLY[["quarter", "net_loss_m"]].dropna(), width="stretch", hide_index=True)

with tab5:
    st.caption(
        "The literal source tables this app is built on, exactly as transcribed from each "
        "shareholder letter -- one wide row per segment, one column per quarter, matching the "
        "letters' own 'IFP BREAKDOWN' / 'GROSS LOSS RATIO BY TYPE' / 'PREMIUM PER CUSTOMER' "
        "table layout. Every other table and chart in this app is derived from exactly these "
        "numbers -- nothing is estimated or interpolated."
    )

    st.markdown("**In-Force Premium by segment, $M (as disclosed)**")
    ifp_raw = pd.DataFrame(data._IFP_M, index=data.QUARTER_ORDER).T
    ifp_raw.index.name = "segment"
    st.dataframe(ifp_raw, width="stretch")

    st.markdown("**Gross Loss Ratio by segment (as disclosed)**")
    glr_raw = pd.DataFrame(data._GROSS_LOSS_RATIO, index=data.QUARTER_ORDER).T
    glr_raw.index.name = "segment"
    st.dataframe(glr_raw.style.format("{:.0%}"), width="stretch")
    style.note(data.CAR_Q4_25_FOOTNOTE)

    st.markdown("**Premium per Customer by segment, $ (as disclosed)**")
    ppc_raw = pd.DataFrame(data._PREMIUM_PER_CUSTOMER, index=data.QUARTER_ORDER).T
    ppc_raw.index.name = "segment"
    st.dataframe(ppc_raw, width="stretch")

    st.markdown("**Company-wide quarterly table (as disclosed)**")
    st.dataframe(data.COMPANY_QUARTERLY, width="stretch", hide_index=True)

    st.markdown("**Notes on data coverage**")
    style.note(data.NOTE_Q2_26_NOT_AVAILABLE)

    st.markdown("**Primary and secondary sources, verbatim**")
    style.sources_footer(data.SOURCES)
