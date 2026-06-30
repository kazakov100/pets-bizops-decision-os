"""Real, publicly available customer-sentiment signal for Lemonade, Inc.

This is NOT Lemonade's internal NPS/CSAT data -- it's the closest public
proxy available: aggregated Trustpilot ratings and the NAIC consumer
complaint index. Both are genuinely public and cited below; neither is
fabricated or synthetic. Treat this as directional market signal, not a
substitute for real internal survey data.
"""

from __future__ import annotations

SOURCES = [
    "Trustpilot: Lemonade Reviews (trustpilot.com/review/lemonade.com) -- "
    "aggregate rating and review count, retrieved June 2026.",
    "NAIC Consumer Information Source (content.naic.org/cis_refined_results.htm) -- "
    "complaint index by company, most recent published year (2024).",
    "Secondary review aggregation (MoneyGeek, Insurify, NerdWallet, Yahoo Finance "
    "pet-insurance reviews, 2026) -- cross-checked for recurring complaint themes.",
    "2023 NAIC complaint index figure (3.5) per a secondary aggregator's combined "
    "renters/home/condo complaint-index reporting for that year -- noted as a possibly "
    "narrower scope than the 2024 company-wide figure, so treated as directional, not "
    "a precisely matched YoY comparison.",
]

PUBLIC_SENTIMENT_LIMITATION = (
    "This is aggregated public review/complaint data, not Lemonade's internal "
    "NPS, CSAT, or churn-survey data -- there is no segment-level (e.g. Pet-only) "
    "breakdown available publicly, and review-site samples skew toward customers "
    "with a strong (positive or negative) reaction, not the full customer base."
)

TRUSTPILOT_SNAPSHOT = {
    "rating": 4.1,
    "scale": 5.0,
    "review_count": 5750,
    "as_of": "2026-06",
    "source": "Trustpilot",
}

NAIC_COMPLAINT_INDEX = {
    "value": 3.85,
    "industry_baseline": 1.0,
    "year": 2024,
    "prior_year": 2023,
    "prior_year_value": 3.5,
    "prior_year_caveat": (
        "The 2023 figure (3.5) comes from a secondary aggregator covering combined "
        "renters/home/condo complaints specifically, which may not be the exact same "
        "scope as the 2024 company-wide figure -- treat the YoY move as directional."
    ),
    "interpretation": "A value of 1.0 means complaint volume in line with the industry average for similar-sized carriers; 3.85 means roughly 4x that baseline.",
    "source": "NAIC Consumer Information Source",
}

COMPLAINT_THEMES = [
    {
        "theme": "Premium increases after the first 12 months",
        "sentiment": "negative",
        "emoji": "💰",
        "notes": "Most frequently cited in reviews for pets that aged into a higher pricing tier or after a claim was filed.",
    },
    {
        "theme": "Claim denials tied to pre-existing-condition enforcement",
        "sentiment": "negative",
        "emoji": "📋",
        "notes": "Recurring theme across review sites; customers report disputes over what counts as pre-existing.",
    },
    {
        "theme": "Slow processing on complex/multi-step claims",
        "sentiment": "negative",
        "emoji": "⏱️",
        "notes": "Echoes the NAIC complaint themes (claim denials, slow complex-claim handling, difficulty reaching a human).",
    },
    {
        "theme": "Fast reimbursement and ease of use for simple claims",
        "sentiment": "positive",
        "emoji": "⚡",
        "notes": "The most consistently cited positive theme -- the AI-first claims flow ('Jim') performs well for straightforward cases.",
    },
]
