"""Deterministic feasibility simulation for golden-metric targets.

Given a metric's real quarterly history and a user-chosen target, this
computes the pace required to hit that target and compares it to the pace
the metric has actually shown historically -- no LLM involved. The AI layer
only ever comments on a simulation result already computed here; it never
asserts feasibility on its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class SimulationResult:
    metric_id: str
    direction: str  # "higher_better" | "lower_better"
    current_quarter: str
    current_value: float
    target_value: float
    horizon_quarters: int
    required_total_change: float
    required_per_quarter_change: float
    historical_avg_quarterly_change: float
    historical_best_quarterly_change: float
    historical_worst_quarterly_change: float
    quarters_at_avg_pace_to_reach_target: float | None
    feasibility_label: str
    feasibility_detail: str
    projected_path: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "metric_id": self.metric_id,
            "direction": self.direction,
            "current_quarter": self.current_quarter,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "horizon_quarters": self.horizon_quarters,
            "required_total_change": self.required_total_change,
            "required_per_quarter_change": self.required_per_quarter_change,
            "historical_avg_quarterly_change": self.historical_avg_quarterly_change,
            "historical_best_quarterly_change": self.historical_best_quarterly_change,
            "historical_worst_quarterly_change": self.historical_worst_quarterly_change,
            "quarters_at_avg_pace_to_reach_target": self.quarters_at_avg_pace_to_reach_target,
            "feasibility_label": self.feasibility_label,
            "feasibility_detail": self.feasibility_detail,
            "projected_path": self.projected_path,
        }


def _favorable_change(delta: float, direction: str) -> float:
    """Signs a raw quarter-over-quarter delta so that positive == movement
    toward the goal, regardless of whether higher or lower is better.
    """
    return delta if direction == "higher_better" else -delta


def simulate_target(
    series: pd.DataFrame,
    target_value: float,
    horizon_quarters: int,
    direction: str,
    metric_id: str = "",
) -> SimulationResult:
    """series must have columns ['quarter', 'value'], chronological order."""
    if len(series) < 2:
        raise ValueError("Need at least 2 historical quarters to simulate a target.")
    if horizon_quarters < 1:
        raise ValueError("horizon_quarters must be >= 1.")

    current_row = series.iloc[-1]
    current_value = float(current_row["value"])
    current_quarter = current_row["quarter"]

    raw_deltas = series["value"].diff().dropna().tolist()
    favorable_deltas = [_favorable_change(d, direction) for d in raw_deltas]

    historical_avg = sum(favorable_deltas) / len(favorable_deltas)
    historical_best = max(favorable_deltas)
    historical_worst = min(favorable_deltas)

    required_total_change = target_value - current_value
    required_per_quarter = required_total_change / horizon_quarters
    required_favorable_per_quarter = _favorable_change(required_per_quarter, direction)

    quarters_at_avg_pace = None
    if historical_avg > 0:
        required_favorable_total = _favorable_change(required_total_change, direction)
        if required_favorable_total > 0:
            quarters_at_avg_pace = round(required_favorable_total / historical_avg, 1)
        else:
            quarters_at_avg_pace = 0.0  # already past the target in the favorable direction

    if required_favorable_per_quarter <= 0:
        label = "trivial-or-wrong-direction"
        detail = (
            "The target is already at or beyond the current value in the favorable direction "
            "-- no improvement pace is actually required."
        )
    elif required_favorable_per_quarter <= max(historical_avg, 0):
        label = "within historical average pace"
        detail = (
            f"The required pace ({required_favorable_per_quarter:.4f}/quarter, favorable direction) "
            f"is at or below the historical average quarterly move "
            f"({historical_avg:.4f}/quarter) -- achievable if the recent trend simply continues."
        )
    elif required_favorable_per_quarter <= historical_best:
        label = "requires sustaining the best historical quarter, every quarter"
        detail = (
            f"The required pace ({required_favorable_per_quarter:.4f}/quarter) exceeds the historical "
            f"average ({historical_avg:.4f}/quarter) but is within the single best quarter ever "
            f"disclosed ({historical_best:.4f}) -- would require repeating an exceptional quarter "
            f"every quarter for {horizon_quarters} quarters straight."
        )
    else:
        label = "exceeds any historical quarterly move -- not realistic on current trend"
        detail = (
            f"The required pace ({required_favorable_per_quarter:.4f}/quarter) exceeds even the best "
            f"single quarter seen in the disclosed history ({historical_best:.4f}/quarter) -- hitting "
            f"this target in {horizon_quarters} quarters would require a structural change, not just "
            f"continuing the current trend."
        )

    projected_path = []
    for i in range(horizon_quarters + 1):
        projected_path.append({
            "step": i,
            "value": round(current_value + required_per_quarter * i, 4),
        })

    return SimulationResult(
        metric_id=metric_id,
        direction=direction,
        current_quarter=current_quarter,
        current_value=current_value,
        target_value=target_value,
        horizon_quarters=horizon_quarters,
        required_total_change=round(required_total_change, 4),
        required_per_quarter_change=round(required_per_quarter, 4),
        historical_avg_quarterly_change=round(historical_avg, 4),
        historical_best_quarterly_change=round(historical_best, 4),
        historical_worst_quarterly_change=round(historical_worst, 4),
        quarters_at_avg_pace_to_reach_target=quarters_at_avg_pace,
        feasibility_label=label,
        feasibility_detail=detail,
        projected_path=projected_path,
    )
