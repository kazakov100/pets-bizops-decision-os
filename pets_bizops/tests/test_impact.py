import pytest

from pets_bizops.analysis import impact, kpis


def test_estimate_dollar_value_is_exact_function_of_real_base_metric():
    # The number must be a reproducible function of the REAL current pet IFP,
    # read here from kpis (not hardcoded) -- proves the arithmetic, not the
    # AI, produces it.
    pet_ifp_m = float(kpis.pet_latest_snapshot()["in_force_premium_m"])
    est = impact.estimate_dollar_value("pet_ifp_m", low_points=1, base_points=2, high_points=4)
    assert est.base_usd_m == round(pet_ifp_m, 1)
    assert est.low_usd_m == round(pet_ifp_m * 0.01, 1)
    assert est.base_case_usd_m == round(pet_ifp_m * 0.02, 1)
    assert est.high_usd_m == round(pet_ifp_m * 0.04, 1)


def test_estimate_dollar_value_company_base_metric():
    company_ifp_m = float(kpis.company_latest_snapshot()["in_force_premium_m"])
    est = impact.estimate_dollar_value("company_ifp_m", 1, 2, 3)
    assert est.base_usd_m == round(company_ifp_m, 1)
    assert est.high_usd_m == round(company_ifp_m * 0.03, 1)


def test_estimate_dollar_value_ranges_increase_with_points():
    est = impact.estimate_dollar_value("pet_ifp_m", 1, 2, 4)
    assert 0 < est.low_usd_m < est.base_case_usd_m < est.high_usd_m


def test_estimate_dollar_value_unknown_base_metric_raises():
    with pytest.raises(ValueError):
        impact.estimate_dollar_value("not_a_real_metric", 1, 2, 3)


def test_as_dict_has_expected_keys():
    d = impact.estimate_dollar_value("pet_ifp_m", 1, 2, 4).as_dict()
    for key in ("base_metric", "base_usd_m", "low_usd_m", "base_case_usd_m", "high_usd_m", "formula"):
        assert key in d
