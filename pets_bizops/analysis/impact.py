"""Deterministic $ impact estimation.

The dollar figure is always computed here in code -- never asserted by the
LLM. The AI's only role (on the Course of Action page) is to supply the
INPUTS to this formula: which real base metric to apply the assumption to,
and the assumed percentage-point range it believes is achievable (grounded
in retrieved RAG evidence). Code resolves the base metric to its real
current value and does the arithmetic. This keeps the multiplication
hallucination-proof while generalizing to any risk/opportunity the AI
surfaces, rather than a fixed list of pre-coded pain points.
"""

from __future__ import annotations

from dataclasses import dataclass

from pets_bizops.analysis import kpis

# Enumerated, code-resolved base metrics. The AI may only name one of these
# keys -- it can never supply an arbitrary base dollar figure itself.
BASE_METRICS = {
    "pet_ifp_m": "Pet in-force premium (latest disclosed quarter)",
    "company_ifp_m": "Company-wide in-force premium (latest disclosed quarter)",
}


def _resolve_base_usd_m(base_metric: str) -> float:
    if base_metric == "pet_ifp_m":
        return float(kpis.pet_latest_snapshot()["in_force_premium_m"])
    if base_metric == "company_ifp_m":
        return float(kpis.company_latest_snapshot()["in_force_premium_m"])
    raise ValueError(f"Unknown base_metric: {base_metric!r}. Known: {list(BASE_METRICS)}")


@dataclass
class DollarEstimate:
    base_metric: str
    base_usd_m: float
    low_usd_m: float
    base_case_usd_m: float
    high_usd_m: float
    formula: str

    def as_dict(self) -> dict:
        return {
            "base_metric": self.base_metric,
            "base_usd_m": self.base_usd_m,
            "low_usd_m": self.low_usd_m,
            "base_case_usd_m": self.base_case_usd_m,
            "high_usd_m": self.high_usd_m,
            "formula": self.formula,
        }


def estimate_dollar_value(
    base_metric: str,
    low_points: float,
    base_points: float,
    high_points: float,
) -> DollarEstimate:
    """Estimate an annual $ range as base_usd_m * (assumed_points / 100).

    `base_metric` is resolved to a real current $ figure in code; the
    point assumptions come from the AI (grounded in RAG) but the arithmetic
    is done here, never by the model.
    """
    base_usd_m = _resolve_base_usd_m(base_metric)

    def value_for(points: float) -> float:
        return round(base_usd_m * (float(points) / 100), 1)

    return DollarEstimate(
        base_metric=base_metric,
        base_usd_m=round(base_usd_m, 1),
        low_usd_m=value_for(low_points),
        base_case_usd_m=value_for(base_points),
        high_usd_m=value_for(high_points),
        formula=f"value_usd_m = {base_metric} (${base_usd_m:.0f}M) * (assumed_points / 100)",
    )
