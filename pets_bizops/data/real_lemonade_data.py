"""Real, publicly disclosed Lemonade, Inc. (NASDAQ: LMND) metrics.

Every number below comes directly from Lemonade's quarterly shareholder
letters (filed with the SEC as Form 8-K exhibits -- primary source, fetched
directly from sec.gov). Each shareholder letter publishes a trailing
5-quarter table covering in-force premium, gross loss ratio, and premium
per customer by product line; the tables below were assembled by taking the
union of five overlapping letters (Q1'25 through Q1'26) and cross-checking
that every quarter which appears in more than one letter matches exactly
across letters. It does. No number here is estimated, interpolated, or
synthetic.

Customer counts, net loss, and the full company financials (revenue, gross
profit, Adjusted EBITDA, Annual Dollar Retention, quarterly company loss
ratios) come from the Q1'26 letter's "Historical Operating Metrics" table,
whose overlapping IFP / premium-per-customer / customer columns match the
independently-assembled segment tables exactly -- cross-validating the source.
"""

from __future__ import annotations

import pandas as pd

PET_LAUNCH_DATE = "2020-07"
LATEST_CLOSED_QUARTER = "Q1'26"
NOTE_Q2_26_NOT_AVAILABLE = (
    "Q2 2026 has not closed yet (the quarter ends in June 2026), so no audited or "
    "disclosed figures exist for it. The Q1'26 shareholder letter mentions, as a "
    "forward-looking note, that Pet crossed $500M IFP 'early in the second quarter' -- "
    "that single milestone fact is kept separately (see PET_OTHER_FACTS) and is not "
    "treated as a closed-quarter data point."
)

SOURCES = [
    "Lemonade, Inc. Q1 2025 Shareholder Letter, SEC Form 8-K (sec.gov/Archives/edgar/data/0001691421/000169142125000062/lmndshareholderletterq12.htm)",
    "Lemonade, Inc. Q2 2025 Shareholder Letter, SEC Form 8-K (sec.gov/Archives/edgar/data/0001691421/000169142125000120/lmndshareholderletterq22.htm)",
    "Lemonade, Inc. Q3 2025 Shareholder Letter, SEC Form 8-K (sec.gov/Archives/edgar/data/0001691421/000169142125000146/lmndshareholderletterq32.htm)",
    "Lemonade, Inc. Q4 2025 Shareholder Letter, SEC Form 8-K (sec.gov/Archives/edgar/data/0001691421/000169142126000006/lmndshareholderletterq42.htm)",
    "Lemonade, Inc. Q1 2026 Shareholder Letter, SEC Form 8-K (sec.gov/Archives/edgar/data/0001691421/000169142126000029/lmndshareholderletterq12.htm)",
    "Each letter's trailing 5-quarter 'IFP BREAKDOWN', 'GROSS LOSS RATIO BY TYPE', and "
    "'PREMIUM PER CUSTOMER' tables -- cross-validated across overlapping quarters.",
    "Q1 2026 letter's full 9-quarter 'Historical Operating Metrics' table -- source for "
    "COMPANY_FINANCIALS (revenue, gross earned premium, gross/adjusted gross profit + margin, "
    "Adjusted EBITDA, Annual Dollar Retention, quarterly company gross/net loss ratio) and "
    "for completing the company net-loss and customer-count series.",
    "Insurance Journal: \"Lemonade Books Q3 Net Loss of $37.5 Million\" (Nov 2025) -- customer counts.",
    "Insurance Journal: \"Lemonade Books Q4 Net Loss of $21.7M as Customer Count Grows\" (Feb 2026) -- customer counts.",
]

QUARTER_ORDER = ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25", "Q3'25", "Q4'25", "Q1'26"]

# ---------------------------------------------------------------------------
# Segment-level quarterly disclosure -- the core dataset. One row per
# (quarter, segment), long format so it's easy to filter/pivot.
# ---------------------------------------------------------------------------

_IFP_M = {
    "Homeowners": [449, 468, 488, 503, 513, 523, 531, 530, 540],
    "Pet": [201, 224, 254, 283, 314, 350, 394, 439, 490],
    "Car": [123, 123, 117, 122, 134, 150, 163, 187, 214],
    "Europe": [12, 14, 19, 24, 33, 43, 51, 60, 67],
    "Other": [9, 10, 11, 12, 14, 17, 19, 21, 23],
}

_GROSS_LOSS_RATIO = {
    "Homeowners": [0.79, 0.78, 0.69, 0.55, 0.82, 0.60, 0.51, 0.39, 0.49],
    "Pet": [0.63, 0.72, 0.71, 0.69, 0.68, 0.70, 0.69, 0.71, 0.69],
    "Car": [0.99, 0.95, 0.92, 0.83, 0.88, 0.82, 0.76, 0.40, 0.74],
    "Europe": [1.06, 0.98, 0.92, 0.75, 0.91, 0.83, 0.70, 0.64, 0.85],
}
# Q4'25 Car loss ratio (40%) benefited from favorable year-end reserve
# movements per the Q1'26 letter's own footnote -- a one-time effect, not a
# structural improvement. Keep the number but don't read it as a trend.
CAR_Q4_25_FOOTNOTE = (
    "In Q4 2025, Car's gross loss ratio benefited from year-end reserve movements, "
    "resulting in a notably strong calendar-quarter result of 40% -- a one-time effect "
    "per Lemonade's own footnote, not a structural improvement."
)

_PREMIUM_PER_CUSTOMER = {
    "Homeowners": [266, 270, 266, 266, 265, 260, 251, 247, 243],
    "Pet": [664, 687, 712, 727, 742, 752, 782, 804, 822],
    "Car": [1544, 1725, 1751, 1800, 1853, 1895, 1964, 2021, 2067],
    "Europe": [110, 113, 129, 129, 147, 168, 176, 184, 187],
    "Other": [791, 803, 846, 913, 998, 1037, 1071, 1091, 1123],
}

SEGMENT_QUARTERLY = pd.concat(
    [
        pd.DataFrame(
            {
                "quarter": QUARTER_ORDER,
                "segment": segment,
                "in_force_premium_m": _IFP_M[segment],
                "gross_loss_ratio": _GROSS_LOSS_RATIO.get(segment),
                "premium_per_customer": _PREMIUM_PER_CUSTOMER[segment],
            }
        )
        for segment in ["Homeowners", "Pet", "Car", "Europe", "Other"]
    ],
    ignore_index=True,
)

# ---------------------------------------------------------------------------
# Company-wide quarterly metrics
# ---------------------------------------------------------------------------

COMPANY_QUARTERLY = pd.DataFrame(
    {
        "quarter": QUARTER_ORDER,
        "in_force_premium_m": [794, 839, 889, 944, 1008, 1083, 1158, 1237, 1333],
        "premium_per_customer": [379, 387, 384, 388, 396, 402, 403, 414, 424],
        # Full series now sourced directly from the Q1'26 letter's "Historical
        # Operating Metrics" table (previously the early quarters were unavailable
        # to us and left as None).
        "customers": [2_095_275, 2_167_194, 2_313_113, 2_430_056, 2_545_496, 2_693_107, 2_869_900, 2_984_513, 3_142_581],
        # Net loss now exact and complete from that same table (previously had
        # gaps and ~0.5M rounding from secondary reporting).
        "net_loss_m": [47.3, 57.2, 67.7, 30.0, 62.4, 43.9, 37.5, 21.7, 35.8],
        # Explicitly disclosed YoY growth rate (Lemonade states this directly each
        # quarter; not derived here, to avoid any disclosed-vs-computed mismatch).
        "ifp_yoy_growth_pct": [None, None, None, 0.26, 0.27, 0.29, 0.30, 0.31, 0.32],
    }
)

# ---------------------------------------------------------------------------
# Company-wide financials & operating metrics -- the full 9-quarter
# "Historical Operating Metrics" table from the Q1'26 shareholder letter
# (SEC 8-K exhibit), fetched directly from sec.gov. Adds the profitability,
# retention, and margin dimensions the segment tables don't carry. The IFP /
# premium-per-customer / customer columns of that table match the
# independently-assembled SEGMENT/COMPANY tables above exactly, which
# cross-validates this source.
# ---------------------------------------------------------------------------

COMPANY_FINANCIALS = pd.DataFrame(
    {
        "quarter": QUARTER_ORDER,
        "revenue_m": [119.1, 122.0, 136.6, 148.8, 151.2, 164.1, 194.5, 228.1, 258.0],
        "gross_earned_premium_m": [187.9, 199.9, 213.1, 226.4, 233.6, 252.3, 274.7, 290.2, 306.2],
        "gross_profit_m": [34.7, 30.8, 37.5, 63.9, 38.6, 64.3, 79.9, 110.6, 100.1],
        "adjusted_gross_profit_m": [36.7, 33.4, 38.6, 66.2, 46.0, 65.6, 80.9, 112.0, 100.8],
        "adjusted_ebitda_m": [-33.9, -43.0, -49.0, -23.8, -47.0, -40.9, -25.6, -4.6, -17.1],
        "gross_profit_margin": [0.29, 0.25, 0.27, 0.43, 0.26, 0.39, 0.41, 0.48, 0.39],
        "annual_dollar_retention": [0.88, 0.88, 0.87, 0.86, 0.84, 0.84, 0.85, 0.85, 0.85],
        # Company-wide gross/net loss ratio, now available QUARTERLY (previously
        # only the annual figures in COMPANY_ANNUAL_LOSS_RATIO were available).
        "gross_loss_ratio": [0.79, 0.79, 0.73, 0.63, 0.78, 0.67, 0.62, 0.52, 0.62],
        "net_loss_ratio": [0.78, 0.79, 0.81, 0.62, 0.82, 0.69, 0.64, 0.53, 0.63],
    }
)
# Lemonade guides to its first Adjusted EBITDA-positive quarter in Q4 2026; the
# adjusted_ebitda_m series above shows the steep path toward it (-$4.6M in
# Q4'25 was the best quarter of the series). Revenue has grown faster than IFP
# recently (71% YoY in Q1'26 vs 32% IFP) due to the reduced quota-share
# reinsurance cession effective Q3'25 raising retained premium.
# Lemonade has explicitly highlighted this as "N consecutive quarters of
# accelerating growth" -- the YoY% itself rising each quarter (26 -> 27 -> 29
# -> 30 -> 31 -> 32) is the headline trend, not just absolute premium growth.

# Full-year loss ratios -- disclosed at the annual level.
COMPANY_ANNUAL_LOSS_RATIO = pd.DataFrame(
    [
        {"year": "FY2024", "gross_loss_ratio": 0.73, "net_loss_ratio": 0.75},
        {"year": "FY2025", "gross_loss_ratio": 0.64, "net_loss_ratio": 0.65},
    ]
)

# ---------------------------------------------------------------------------
# Pet segment facts not captured in the quarterly table above
# ---------------------------------------------------------------------------

PET_OTHER_FACTS = {
    "launch_date": PET_LAUNCH_DATE,
    "q4_25_yoy_ifp_growth_pct": round(439 / 283 - 1, 4),  # computed from the disclosed IFP series itself
    "q4_25_ppc_yoy_growth_pct": round(804 / 727 - 1, 4),
    "q4_25_quarterly_gross_loss_ratio": 0.71,
    "cost_per_claim_2025_usd": 14,
    "became_largest_product_line_as_of": "early Q2 2026 (forward-looking note in Q1'26 letter, not a closed quarter)",
    "pet_ifp_from_existing_customer_cross_sell_m": 85,  # disclosed in Q1'26 letter
}

CAR_SEGMENT_FACTS = {
    "q3_25_gross_loss_ratio": 0.76,
    "q3_25_yoy_loss_ratio_improvement_points": 16,
    "q4_25_footnote": CAR_Q4_25_FOOTNOTE,
}

MISSION_AND_STRATEGY = """
Lemonade's publicly stated model: a flat ~25% fee on premium (vs. the
traditional insurer incentive to deny claims to protect underwriting
margin), with the Giveback program donating unclaimed premium to
customer-chosen charities -- explicitly designed to reduce the incentive for
claim fraud or denial disputes. The company positions itself as AI-first:
"Maya" handles quoting/onboarding, "Jim" handles claims. Its stated growth
strategy is cross-sell/bundling across renters, homeowners, pet, life, and
car to raise premium-per-customer and lifetime value (the Q1'26 letter
states ~$85M of Pet's in-force premium now comes from CAC-free cross-sales
to existing customers). It runs two distinct capital partnerships: a
quota-share reinsurance program (progressively reduced from 75% to 70% to
55% cession, with a further reduction effective Q3'25) that relieves
regulatory-capital burden, and the "Synthetic Agents" program with General
Catalyst -- which finances up to 80% of monthly customer-acquisition cost in
return for up to a 16% commission on that cohort's premiums -- that relieves
working-capital burden and funds capital-light growth.
""".strip()
