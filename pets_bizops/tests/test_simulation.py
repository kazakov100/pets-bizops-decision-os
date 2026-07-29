import pandas as pd

from pets_bizops.analysis import simulation, kpis


def test_simulate_target_within_average_pace_for_lower_better():
    series = kpis.golden_metric_series("pet_gross_loss_ratio")
    result = simulation.simulate_target(series, target_value=0.67, horizon_quarters=4, direction="lower_better")
    assert result.required_per_quarter_change < 0
    assert result.feasibility_label in {
        "Achievable at the historical pace",
        "A stretch — needs the best-ever pace, sustained",
    }


def test_simulate_target_exceeds_history_for_unrealistic_lower_better_target():
    series = kpis.golden_metric_series("pet_gross_loss_ratio")
    result = simulation.simulate_target(series, target_value=0.30, horizon_quarters=2, direction="lower_better")
    assert result.feasibility_label == "Unrealistic on the current trend"


def test_simulate_target_higher_better_direction_signs_correctly():
    series = pd.DataFrame({"quarter": ["Q1", "Q2", "Q3"], "value": [100.0, 110.0, 120.0]})
    result = simulation.simulate_target(series, target_value=140.0, horizon_quarters=2, direction="higher_better")
    assert result.required_per_quarter_change == 10.0
    assert result.feasibility_label == "Achievable at the historical pace"


def test_simulate_target_trivial_when_already_past_target():
    series = pd.DataFrame({"quarter": ["Q1", "Q2", "Q3"], "value": [100.0, 110.0, 120.0]})
    result = simulation.simulate_target(series, target_value=90.0, horizon_quarters=2, direction="higher_better")
    assert result.feasibility_label == "Target already met — no improvement needed"


def test_simulate_target_requires_at_least_two_quarters():
    series = pd.DataFrame({"quarter": ["Q1"], "value": [100.0]})
    try:
        simulation.simulate_target(series, target_value=110.0, horizon_quarters=1, direction="higher_better")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_golden_metric_series_returns_quarter_and_value_columns():
    for metric_id in kpis.GOLDEN_METRICS:
        df = kpis.golden_metric_series(metric_id)
        assert list(df.columns) == ["quarter", "value"]
        assert len(df) >= 2
