"""Deterministic KPI computation over real, publicly disclosed Lemonade data.

No LLM calls here. Every function reads from data/real_lemonade_data.py and
only computes derived values (deltas, ratios, growth rates) from numbers
that are genuinely present -- it never fills in a missing quarter.
"""

from __future__ import annotations

import pandas as pd

from pets_bizops.data import real_lemonade_data as data

PRIMARY_KPI_NAME = "pet_in_force_premium_m"
ALL_SEGMENTS = ["Homeowners", "Pet", "Car", "Europe", "Other"]


def company_latest_snapshot() -> dict:
    """Most recent disclosed company-wide quarter, plus the most recent
    annual loss ratio and the most recent disclosed net loss figure.
    """
    q = data.COMPANY_QUARTERLY
    latest = q.iloc[-1]
    latest_with_net_loss = q.dropna(subset=["net_loss_m"]).iloc[-1]
    latest_loss_ratio = data.COMPANY_ANNUAL_LOSS_RATIO.iloc[-1]
    return {
        "quarter": latest["quarter"],
        "in_force_premium_m": float(latest["in_force_premium_m"]),
        "customers": int(latest["customers"]) if latest["customers"] is not None else None,
        "premium_per_customer": int(latest["premium_per_customer"]),
        "ifp_yoy_growth_pct": latest["ifp_yoy_growth_pct"],
        "loss_ratio_year": latest_loss_ratio["year"],
        "gross_loss_ratio": float(latest_loss_ratio["gross_loss_ratio"]),
        "net_loss_ratio": float(latest_loss_ratio["net_loss_ratio"]),
        "net_loss_period": latest_with_net_loss["quarter"],
        "net_loss_m": float(latest_with_net_loss["net_loss_m"]),
    }


def segment_quarterly(segment: str) -> pd.DataFrame:
    """Full quarterly time series for one segment (Homeowners/Pet/Car/Europe/Other)."""
    return data.SEGMENT_QUARTERLY[data.SEGMENT_QUARTERLY["segment"] == segment].reset_index(drop=True)


def pet_latest_snapshot() -> dict:
    pet = segment_quarterly("Pet")
    latest = pet.iloc[-1]
    prior = pet.iloc[-2]
    prior_year = pet.iloc[-5] if len(pet) >= 5 else None  # same quarter, prior year

    out = {
        "quarter": latest["quarter"],
        "in_force_premium_m": float(latest["in_force_premium_m"]),
        "premium_per_customer": int(latest["premium_per_customer"]),
        "gross_loss_ratio": float(latest["gross_loss_ratio"]),
        "prior_quarter": prior["quarter"],
        "prior_in_force_premium_m": float(prior["in_force_premium_m"]),
        "qoq_ifp_growth_pct": round(float(latest["in_force_premium_m"]) / float(prior["in_force_premium_m"]) - 1, 4),
        "qoq_ppc_growth_pct": round(float(latest["premium_per_customer"]) / float(prior["premium_per_customer"]) - 1, 4),
        "qoq_loss_ratio_points": round((float(latest["gross_loss_ratio"]) - float(prior["gross_loss_ratio"])) * 100, 1),
        **data.PET_OTHER_FACTS,
    }
    if prior_year is not None:
        out["yoy_quarter"] = prior_year["quarter"]
        out["yoy_ifp_growth_pct"] = round(float(latest["in_force_premium_m"]) / float(prior_year["in_force_premium_m"]) - 1, 4)
        out["yoy_ppc_growth_pct"] = round(float(latest["premium_per_customer"]) / float(prior_year["premium_per_customer"]) - 1, 4)
        out["yoy_loss_ratio_points"] = round((float(latest["gross_loss_ratio"]) - float(prior_year["gross_loss_ratio"])) * 100, 1)
    return out


def pet_loss_ratio_series() -> pd.DataFrame:
    """Full quarterly Pet gross loss ratio series -- a real trend, not a
    single snapshot, now that the underlying disclosure covers 9 quarters.
    """
    pet = segment_quarterly("Pet")
    return pet[["quarter", "gross_loss_ratio"]].copy()


RECENT_WINDOW_QUARTERS = 5  # matches the trailing window each shareholder letter itself reports


def recent_quarters(df: pd.DataFrame, n: int = RECENT_WINDOW_QUARTERS) -> pd.DataFrame:
    """The most recent n quarters of a quarterly dataframe.

    Used for "is this metric improving lately" comparisons -- Pet's full
    9-quarter history includes its early ramp-up period (when the book was
    tiny and the loss ratio hadn't stabilized yet), which isn't a fair
    comparison window for "is it flat or trending now."
    """
    return df.tail(n).reset_index(drop=True)


def segment_breakdown(quarter: str = "Q1'26") -> dict:
    """Cross-segment in-force premium breakdown at a given quarter."""
    rows = data.SEGMENT_QUARTERLY[data.SEGMENT_QUARTERLY["quarter"] == quarter]
    total = rows["in_force_premium_m"].sum()
    pet_row = rows[rows["segment"] == "Pet"].iloc[0]
    breakdown = rows[["segment", "in_force_premium_m"]].sort_values("in_force_premium_m", ascending=False).to_dict(orient="records")
    return {
        "quarter": quarter,
        "pet_ifp_m": float(pet_row["in_force_premium_m"]),
        "total_ifp_m": float(total),
        "pet_share_pct": float(pet_row["in_force_premium_m"] / total),
        "breakdown": breakdown,
    }


def pet_share_of_company(quarter: str = "Q1'26") -> dict:
    return segment_breakdown(quarter)


def company_quarterly_series() -> pd.DataFrame:
    return data.COMPANY_QUARTERLY.copy()


def company_financials_series() -> pd.DataFrame:
    return data.COMPANY_FINANCIALS.copy()


def company_financials_latest() -> dict:
    """Most recent disclosed company-wide financials/operating metrics
    (revenue, gross profit + margin, Adjusted EBITDA, Annual Dollar Retention,
    quarterly company loss ratios) plus the prior-year-same-quarter values for
    YoY context.
    """
    fin = data.COMPANY_FINANCIALS
    latest = fin.iloc[-1]
    prior_year = fin.iloc[-5] if len(fin) >= 5 else None
    out = {
        "quarter": latest["quarter"],
        "revenue_m": float(latest["revenue_m"]),
        "gross_earned_premium_m": float(latest["gross_earned_premium_m"]),
        "gross_profit_m": float(latest["gross_profit_m"]),
        "adjusted_gross_profit_m": float(latest["adjusted_gross_profit_m"]),
        "adjusted_ebitda_m": float(latest["adjusted_ebitda_m"]),
        "gross_profit_margin": float(latest["gross_profit_margin"]),
        "annual_dollar_retention": float(latest["annual_dollar_retention"]),
        "gross_loss_ratio": float(latest["gross_loss_ratio"]),
        "net_loss_ratio": float(latest["net_loss_ratio"]),
    }
    if prior_year is not None:
        out["yoy_quarter"] = prior_year["quarter"]
        out["yoy_revenue_growth_pct"] = round(float(latest["revenue_m"]) / float(prior_year["revenue_m"]) - 1, 4)
        out["yoy_adjusted_ebitda_improvement_m"] = round(float(latest["adjusted_ebitda_m"]) - float(prior_year["adjusted_ebitda_m"]), 1)
    return out


def pet_quarterly_series() -> pd.DataFrame:
    return segment_quarterly("Pet")


def all_segments_quarterly_series() -> pd.DataFrame:
    return data.SEGMENT_QUARTERLY.copy()


def company_loss_ratio_series() -> pd.DataFrame:
    return data.COMPANY_ANNUAL_LOSS_RATIO.copy()


def segment_yoy_growth_series(segment: str) -> pd.DataFrame:
    """Quarterly YoY in-force-premium growth for one segment, computed from
    the disclosed quarterly series itself (needs >=5 quarters; first 4
    quarters have no prior-year comparison and are dropped).
    """
    s = segment_quarterly(segment)
    rows = []
    for i in range(4, len(s)):
        cur, prior = s.iloc[i], s.iloc[i - 4]
        rows.append({
            "quarter": cur["quarter"],
            "yoy_growth_pct": round(float(cur["in_force_premium_m"]) / float(prior["in_force_premium_m"]) - 1, 4),
        })
    return pd.DataFrame(rows)


GOLDEN_METRICS = {
    "pet_ifp_growth": {
        "label": "Pet YoY In-Force Premium Growth",
        "unit": "pct",
        "direction": "higher_better",
        "segment": "Pet",
    },
    "pet_gross_loss_ratio": {
        "label": "Pet Gross Loss Ratio",
        "unit": "pct",
        "direction": "lower_better",
        "segment": "Pet",
    },
    "pet_premium_per_customer": {
        "label": "Pet Premium per Customer",
        "unit": "usd",
        "direction": "higher_better",
        "segment": "Pet",
    },
    "company_ifp_growth": {
        "label": "Company-wide YoY In-Force Premium Growth",
        "unit": "pct",
        "direction": "higher_better",
        "segment": "Company",
    },
    "company_adjusted_ebitda": {
        "label": "Company Adjusted EBITDA ($M, toward breakeven)",
        "unit": "usd",
        "direction": "higher_better",
        "segment": "Company",
    },
    "company_annual_dollar_retention": {
        "label": "Annual Dollar Retention",
        "unit": "pct",
        "direction": "higher_better",
        "segment": "Company",
    },
    "company_gross_profit_margin": {
        "label": "Company Gross Profit Margin",
        "unit": "pct",
        "direction": "higher_better",
        "segment": "Company",
    },
}


def golden_metric_series(metric_id: str) -> pd.DataFrame:
    """Quarter/value series for a golden metric, in the metric's own unit
    (pct as a fraction e.g. 0.69, usd as a plain number).
    """
    if metric_id == "pet_ifp_growth":
        df = segment_yoy_growth_series("Pet")
        return df.rename(columns={"yoy_growth_pct": "value"})
    if metric_id == "pet_gross_loss_ratio":
        df = segment_quarterly("Pet")[["quarter", "gross_loss_ratio"]]
        return df.rename(columns={"gross_loss_ratio": "value"})
    if metric_id == "pet_premium_per_customer":
        df = segment_quarterly("Pet")[["quarter", "premium_per_customer"]]
        return df.rename(columns={"premium_per_customer": "value"})
    if metric_id == "company_ifp_growth":
        df = data.COMPANY_QUARTERLY.dropna(subset=["ifp_yoy_growth_pct"])[["quarter", "ifp_yoy_growth_pct"]]
        return df.rename(columns={"ifp_yoy_growth_pct": "value"})
    if metric_id == "company_adjusted_ebitda":
        df = data.COMPANY_FINANCIALS[["quarter", "adjusted_ebitda_m"]]
        return df.rename(columns={"adjusted_ebitda_m": "value"})
    if metric_id == "company_annual_dollar_retention":
        df = data.COMPANY_FINANCIALS[["quarter", "annual_dollar_retention"]]
        return df.rename(columns={"annual_dollar_retention": "value"})
    if metric_id == "company_gross_profit_margin":
        df = data.COMPANY_FINANCIALS[["quarter", "gross_profit_margin"]]
        return df.rename(columns={"gross_profit_margin": "value"})
    raise ValueError(f"Unknown golden metric id: {metric_id}")
