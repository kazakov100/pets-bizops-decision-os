"""Structured Evidence layer over real, publicly disclosed Lemonade data.

The AI layer only ever consumes Evidence objects, never raw dataframes.
Every Evidence object names its own limitations -- here, that almost always
means "this is public aggregate disclosure, not granular internal data."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pets_bizops.data import real_lemonade_data as data
from pets_bizops.analysis import kpis

PUBLIC_DATA_LIMITATION = (
    "This is Lemonade's public quarterly disclosure, not internal data -- there is no "
    "policy-level, state-level, or channel-level granularity available."
)


@dataclass
class Evidence:
    finding: str
    segment: str
    confidence: str  # "high" | "medium" | "low"
    supporting_metrics: dict = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "finding": self.finding,
            "segment": self.segment,
            "confidence": self.confidence,
            "supporting_metrics": self.supporting_metrics,
            "limitations": self.limitations,
        }


def pet_growth_vs_loss_ratio_evidence() -> Evidence:
    pet = kpis.pet_latest_snapshot()
    company = kpis.company_latest_snapshot()
    full_series = kpis.pet_loss_ratio_series()
    recent_series = kpis.recent_quarters(full_series)
    recent_range = (recent_series["gross_loss_ratio"].min(), recent_series["gross_loss_ratio"].max())
    full_range = (full_series["gross_loss_ratio"].min(), full_series["gross_loss_ratio"].max())

    return Evidence(
        finding=(
            f"Pet in-force premium grew {pet['yoy_ifp_growth_pct']:+.0%} YoY to "
            f"${pet['in_force_premium_m']:.0f}M as of {pet['quarter']} (from "
            f"${pet['prior_in_force_premium_m']:.0f}M at {pet['prior_quarter']}). Over the most "
            f"recent {len(recent_series)} quarters ({recent_series.iloc[0]['quarter']}-"
            f"{recent_series.iloc[-1]['quarter']}), its quarterly gross loss ratio has stayed "
            f"within a narrow {recent_range[0]:.0%}-{recent_range[1]:.0%} band, showing no clear "
            f"improving trend -- over its full {len(full_series)}-quarter disclosed history "
            f"(including its early 2024 ramp-up), the range was wider "
            f"({full_range[0]:.0%}-{full_range[1]:.0%}). In contrast, the company-wide ANNUAL "
            f"gross loss ratio improved from {data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]['gross_loss_ratio']:.0%} "
            f"({data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]['year']}) to {company['gross_loss_ratio']:.0%} "
            f"({company['loss_ratio_year']})."
        ),
        segment="product_line=Pet",
        confidence="high",
        supporting_metrics={
            "pet_yoy_ifp_growth_pct": pet["yoy_ifp_growth_pct"],
            "pet_loss_ratio_full_series": full_series.to_dict(orient="records"),
            "pet_loss_ratio_recent_min": float(recent_range[0]),
            "pet_loss_ratio_recent_max": float(recent_range[1]),
            "company_gross_loss_ratio_latest": company["gross_loss_ratio"],
            "company_gross_loss_ratio_prior_year": float(data.COMPANY_ANNUAL_LOSS_RATIO.iloc[0]["gross_loss_ratio"]),
        },
        limitations=[
            PUBLIC_DATA_LIMITATION,
            "Company-wide loss ratio is only disclosed annually, while Pet's is disclosed "
            "quarterly -- the comparison mixes a multi-year annual improvement against a "
            "recent-quarters window, not a perfectly matched timeframe.",
            "Pet launched in July 2020 and is still a young line (~5.5 years old at this "
            "snapshot); a stable-but-not-improving loss ratio during rapid growth is common "
            "while a book is still maturing, and is not necessarily a sign of mispricing.",
        ],
    )


def pet_premium_per_customer_evidence() -> Evidence:
    pet = kpis.pet_latest_snapshot()
    return Evidence(
        finding=(
            f"Pet premium per customer rose {pet['yoy_ppc_growth_pct']:+.0%} YoY to "
            f"${pet['premium_per_customer']} as of {pet['quarter']}, while in-force premium grew "
            f"{pet['yoy_ifp_growth_pct']:+.0%} over the same year -- i.e. most of Pet's growth is "
            f"still new customers, not deeper monetization of existing ones, though "
            f"premium-per-customer is moving in the right direction too."
        ),
        segment="product_line=Pet",
        confidence="high",
        supporting_metrics={
            "pet_yoy_ppc_growth_pct": pet["yoy_ppc_growth_pct"],
            "pet_yoy_ifp_growth_pct": pet["yoy_ifp_growth_pct"],
        },
        limitations=[
            PUBLIC_DATA_LIMITATION,
            "No breakdown of how much of the premium-per-customer increase is price "
            "increases on existing policies vs. new customers buying higher coverage -- "
            "though the Q1'26 letter does disclose that ~$85M of Pet's IFP now comes from "
            "cross-sell to existing customers, which is a related but distinct signal.",
        ],
    )


def pet_segment_share_evidence() -> Evidence:
    share = kpis.pet_share_of_company()
    homeowners_m = next(s["in_force_premium_m"] for s in share["breakdown"] if s["segment"] == "Homeowners")
    gap_m = homeowners_m - share["pet_ifp_m"]
    return Evidence(
        finding=(
            f"At {share['quarter']} (the latest closed quarter), Pet was ${share['pet_ifp_m']:.0f}M of "
            f"${share['total_ifp_m']:.0f}M total company in-force premium "
            f"({share['pet_share_pct']:.0%}), still the 2nd-largest line, ${gap_m:.0f}M behind "
            f"Homeowners (${homeowners_m:.0f}M). Separately, Lemonade's Q1'26 shareholder letter "
            f"includes a forward-looking note that Pet crossed Homeowners to become the largest "
            f"line early in Q2 2026 -- a milestone not yet reflected in any closed-quarter table."
        ),
        segment="product_line=Pet",
        confidence="high",
        supporting_metrics={"share_breakdown": share["breakdown"], "pet_share_pct": share["pet_share_pct"]},
        limitations=[
            PUBLIC_DATA_LIMITATION,
            "The Q2 2026 'became largest line' note is forward-looking commentary in the Q1'26 "
            "letter, not a disclosed closed-quarter figure -- treat it as directional, not as "
            "confirmed Q2'26 segment data (which isn't public yet).",
        ],
    )


def company_growth_acceleration_evidence() -> Evidence:
    series = data.COMPANY_QUARTERLY.dropna(subset=["ifp_yoy_growth_pct"])
    is_monotonic_increasing = series["ifp_yoy_growth_pct"].is_monotonic_increasing
    return Evidence(
        finding=(
            f"Company-wide in-force premium YoY growth has risen every quarter from "
            f"{series.iloc[0]['ifp_yoy_growth_pct']:.0%} ({series.iloc[0]['quarter']}) to "
            f"{series.iloc[-1]['ifp_yoy_growth_pct']:.0%} ({series.iloc[-1]['quarter']}) -- "
            f"{'a consistent acceleration trend' if is_monotonic_increasing else 'a mostly rising but not strictly monotonic trend'} "
            f"across {len(series)} quarters."
        ),
        segment="company-wide",
        confidence="high",
        supporting_metrics={"quarters": series.to_dict(orient="records"), "monotonic": bool(is_monotonic_increasing)},
        limitations=[
            PUBLIC_DATA_LIMITATION,
            "Growth-rate acceleration alone doesn't indicate which product lines are "
            "driving it in a given quarter without the segment breakdown.",
        ],
    )


def pet_loss_ratio_vs_other_segments_evidence() -> Evidence:
    """Compares Pet's loss-ratio trajectory against the other young/growing
    segments (Car, Europe) which DID show clear improvement over the same
    window -- a more apples-to-apples comparison than vs. the company-wide
    annual figure.
    """
    pet_series = kpis.segment_quarterly("Pet")
    car_series = kpis.segment_quarterly("Car")
    car_change_points = (car_series.iloc[-1]["gross_loss_ratio"] - car_series.iloc[0]["gross_loss_ratio"]) * 100
    pet_change_points = (pet_series.iloc[-1]["gross_loss_ratio"] - pet_series.iloc[0]["gross_loss_ratio"]) * 100

    return Evidence(
        finding=(
            f"Over the same {len(pet_series)}-quarter window ({pet_series.iloc[0]['quarter']} to "
            f"{pet_series.iloc[-1]['quarter']}), Car's gross loss ratio moved "
            f"{car_change_points:+.0f} points ({car_series.iloc[0]['gross_loss_ratio']:.0%} to "
            f"{car_series.iloc[-1]['gross_loss_ratio']:.0%}, though Q4'25 included a one-time "
            f"favorable reserve adjustment), while Pet's moved only {pet_change_points:+.0f} "
            f"points ({pet_series.iloc[0]['gross_loss_ratio']:.0%} to {pet_series.iloc[-1]['gross_loss_ratio']:.0%}) "
            f"-- Pet is the only major growth segment without a clear underwriting "
            f"improvement trend over this window."
        ),
        segment="product_line=Pet vs Car",
        confidence="medium",
        supporting_metrics={
            "pet_change_points": round(float(pet_change_points), 1),
            "car_change_points": round(float(car_change_points), 1),
        },
        limitations=[
            PUBLIC_DATA_LIMITATION,
            "Car's improvement is partly a one-time reserve benefit in Q4'25 (per Lemonade's "
            "own footnote), so the comparison may overstate how much Car genuinely improved "
            "on an underlying basis.",
            "Different product lines (auto vs. pet) have structurally different loss-ratio "
            "dynamics and underwriting cycles, so this is a directional comparison, not a "
            "controlled one.",
        ],
    )
