from pets_bizops.analysis import kpis


def test_company_latest_snapshot_keys():
    snap = kpis.company_latest_snapshot()
    expected = {
        "quarter", "in_force_premium_m", "customers", "premium_per_customer",
        "ifp_yoy_growth_pct", "loss_ratio_year", "gross_loss_ratio", "net_loss_ratio",
        "net_loss_period", "net_loss_m",
    }
    assert expected.issubset(snap.keys())
    assert snap["quarter"] == "Q1'26"


def test_pet_latest_snapshot_includes_yoy_comparison():
    snap = kpis.pet_latest_snapshot()
    assert snap["yoy_quarter"] == "Q1'25"
    assert snap["in_force_premium_m"] > snap["prior_in_force_premium_m"]
    assert snap["yoy_ifp_growth_pct"] > 0


def test_pet_loss_ratio_series_has_nine_quarters():
    series = kpis.pet_loss_ratio_series()
    assert len(series) == 9
    assert series["gross_loss_ratio"].between(0.5, 0.8).all()


def test_segment_breakdown_sums_to_total():
    share = kpis.pet_share_of_company("Q1'26")
    total_from_breakdown = sum(s["in_force_premium_m"] for s in share["breakdown"])
    assert total_from_breakdown == share["total_ifp_m"]
    assert 0 < share["pet_share_pct"] < 1


def test_pet_is_second_largest_at_q1_26():
    share = kpis.pet_share_of_company("Q1'26")
    assert share["breakdown"][0]["segment"] == "Homeowners"
    assert share["breakdown"][1]["segment"] == "Pet"


def test_pet_is_second_largest_at_q4_25():
    share = kpis.pet_share_of_company("Q4'25")
    assert share["breakdown"][0]["segment"] == "Homeowners"
    assert share["breakdown"][1]["segment"] == "Pet"


def test_company_quarterly_series_is_chronological():
    series = kpis.company_quarterly_series()
    assert series["in_force_premium_m"].is_monotonic_increasing


def test_all_segments_quarterly_series_has_45_rows():
    series = kpis.all_segments_quarterly_series()
    assert len(series) == 9 * 5  # 9 quarters x 5 segments
